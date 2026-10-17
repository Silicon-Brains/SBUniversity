import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.course import Course, CourseTeacher, Enrollment, EnrollmentStatus
from app.db.models.user import User, UserRole
from app.db.models.whiteboard import (
    WhiteboardMessage,
    WhiteboardSession,
    WhiteboardStroke,
)

WHITEBOARD_CHAT_LIFETIME = timedelta(minutes=10)


class WhiteboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_courses(self, user: User) -> list[tuple[Course, bool]]:
        stmt = select(Course)
        if user.role == UserRole.TEACHER:
            stmt = stmt.where(
                or_(
                    Course.teacher_id == user.id,
                    Course.teacher_assignments.any(
                        CourseTeacher.teacher_id == user.id
                    ),
                )
            )
        elif user.role == UserRole.STUDENT:
            stmt = (
                stmt.join(Enrollment, Enrollment.course_id == Course.id)
                .where(
                    Enrollment.student_id == user.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
        elif user.role != UserRole.ADMIN:
            return []
        stmt = stmt.order_by(Course.title)
        courses = list((await self.db.execute(stmt)).scalars().unique().all())
        if not courses:
            return []
        active_course_ids = set(
            (
                await self.db.execute(
                    select(WhiteboardSession.course_id).where(
                        WhiteboardSession.course_id.in_(
                            [course.id for course in courses]
                        ),
                        WhiteboardSession.is_active.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )
        return [(course, course.id in active_course_ids) for course in courses]

    async def get_course(self, course_id: uuid.UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def can_access_course(self, user: User, course: Course) -> bool:
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.TEACHER:
            return await self.db.scalar(
                select(Course.id).where(
                    Course.id == course.id,
                    or_(
                        Course.teacher_id == user.id,
                        Course.teacher_assignments.any(
                            CourseTeacher.teacher_id == user.id
                        ),
                    ),
                )
            ) is not None
        if user.role != UserRole.STUDENT:
            return False
        enrollment = await self.db.scalar(
            select(Enrollment.id).where(
                Enrollment.course_id == course.id,
                Enrollment.student_id == user.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        return enrollment is not None

    async def get_active_session(
        self, course_id: uuid.UUID
    ) -> WhiteboardSession | None:
        return await self.db.scalar(
            select(WhiteboardSession)
            .where(
                WhiteboardSession.course_id == course_id,
                WhiteboardSession.is_active.is_(True),
            )
        )

    async def get_session(
        self, session_id: uuid.UUID
    ) -> WhiteboardSession | None:
        return await self.db.scalar(
            select(WhiteboardSession)
            .options(selectinload(WhiteboardSession.strokes))
            .where(WhiteboardSession.id == session_id)
        )

    async def get_session_strokes(
        self,
        session: WhiteboardSession,
        board_generation: int | None,
        after_stroke_id: uuid.UUID | None,
    ) -> tuple[list[WhiteboardStroke], bool]:
        if board_generation is None or board_generation != session.board_generation:
            return await self._list_all_strokes(session.id), True
        if after_stroke_id is None:
            return await self._list_all_strokes(session.id), True

        cursor = await self.db.scalar(
            select(WhiteboardStroke).where(
                WhiteboardStroke.id == after_stroke_id,
                WhiteboardStroke.session_id == session.id,
            )
        )
        if cursor is None:
            return await self._list_all_strokes(session.id), True

        stmt = (
            select(WhiteboardStroke)
            .where(
                WhiteboardStroke.session_id == session.id,
                or_(
                    WhiteboardStroke.created_at > cursor.created_at,
                    (
                        WhiteboardStroke.created_at == cursor.created_at
                    )
                    & (WhiteboardStroke.id > cursor.id),
                ),
            )
            .order_by(WhiteboardStroke.created_at, WhiteboardStroke.id)
        )
        return list((await self.db.execute(stmt)).scalars().all()), False

    async def _list_all_strokes(
        self, session_id: uuid.UUID
    ) -> list[WhiteboardStroke]:
        stmt = (
            select(WhiteboardStroke)
            .where(WhiteboardStroke.session_id == session_id)
            .order_by(WhiteboardStroke.created_at, WhiteboardStroke.id)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def start_session(
        self, course: Course, creator: User
    ) -> WhiteboardSession:
        await self.db.execute(
            select(Course.id)
            .where(Course.id == course.id)
            .with_for_update()
        )
        active = await self.get_active_session(course.id)
        if active:
            return active
        session = WhiteboardSession(course_id=course.id, created_by=creator.id)
        self.db.add(session)
        await self.db.commit()
        return await self.get_session(session.id) or session

    async def end_session(self, session: WhiteboardSession) -> None:
        session.is_active = False
        session.ended_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def create_stroke(
        self,
        session_id: uuid.UUID,
        author_id: uuid.UUID,
        tool: str,
        color: str,
        width: int,
        points: list[dict[str, float]],
    ) -> WhiteboardStroke:
        await self.db.execute(
            select(WhiteboardSession.id)
            .where(WhiteboardSession.id == session_id)
            .with_for_update()
        )
        created_at = datetime.now(timezone.utc)
        latest_created_at = await self.db.scalar(
            select(func.max(WhiteboardStroke.created_at)).where(
                WhiteboardStroke.session_id == session_id
            )
        )
        if latest_created_at is not None:
            if latest_created_at.tzinfo is None:
                latest_created_at = latest_created_at.replace(tzinfo=timezone.utc)
            if created_at <= latest_created_at:
                created_at = latest_created_at + timedelta(microseconds=1)
        stroke = WhiteboardStroke(
            session_id=session_id,
            author_id=author_id,
            tool=tool,
            color=color,
            width=width,
            points=points,
            created_at=created_at,
        )
        self.db.add(stroke)
        await self.db.commit()
        await self.db.refresh(stroke)
        return stroke

    async def count_strokes(self, session_id: uuid.UUID) -> int:
        return int(
            await self.db.scalar(
                select(func.count(WhiteboardStroke.id)).where(
                    WhiteboardStroke.session_id == session_id
                )
            )
            or 0
        )

    async def delete_strokes(self, session_id: uuid.UUID) -> None:
        result = await self.db.execute(
            delete(WhiteboardStroke).where(
                WhiteboardStroke.session_id == session_id
            )
        )
        if result.rowcount:
            await self.db.execute(
                update(WhiteboardSession)
                .where(WhiteboardSession.id == session_id)
                .values(
                    board_generation=WhiteboardSession.board_generation + 1
                )
            )
        await self.db.commit()

    async def delete_last_stroke(self, session_id: uuid.UUID) -> bool:
        stroke = await self.db.scalar(
            select(WhiteboardStroke)
            .where(WhiteboardStroke.session_id == session_id)
            .order_by(WhiteboardStroke.created_at.desc(), WhiteboardStroke.id.desc())
            .limit(1)
        )
        if stroke is None:
            return False
        await self.db.delete(stroke)
        await self.db.execute(
            update(WhiteboardSession)
            .where(WhiteboardSession.id == session_id)
            .values(board_generation=WhiteboardSession.board_generation + 1)
        )
        await self.db.commit()
        return True

    async def delete_expired_messages(
        self, now: datetime | None = None
    ) -> int:
        result = await self.db.execute(
            delete(WhiteboardMessage).where(
                WhiteboardMessage.expires_at
                <= (now or datetime.now(timezone.utc))
            )
        )
        deleted = result.rowcount or 0
        if deleted:
            await self.db.commit()
        return deleted

    async def list_messages(
        self, session_id: uuid.UUID
    ) -> list[tuple[WhiteboardMessage, User]]:
        rows = await self.db.execute(
            select(WhiteboardMessage, User)
            .join(User, User.id == WhiteboardMessage.sender_id)
            .where(
                WhiteboardMessage.session_id == session_id,
                WhiteboardMessage.expires_at > datetime.now(timezone.utc),
            )
            .order_by(WhiteboardMessage.created_at.desc())
            .limit(100)
        )
        return list(reversed(rows.all()))

    async def create_message(
        self, session_id: uuid.UUID, sender_id: uuid.UUID, content: str
    ) -> tuple[WhiteboardMessage, User]:
        created_at = datetime.now(timezone.utc)
        message = WhiteboardMessage(
            session_id=session_id,
            sender_id=sender_id,
            content=content,
            expires_at=created_at + WHITEBOARD_CHAT_LIFETIME,
            created_at=created_at,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        sender = await self.db.get(User, sender_id)
        assert sender is not None
        return message, sender
