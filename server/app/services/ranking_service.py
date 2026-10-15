import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.redis import get_redis_client
from app.db.models.user import User, UserStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ranking import LeaderboardResponse, MyRankResponse, RankedStudentItem

REDIS_KEY_LB_OVERALL = "lb:overall"
REDIS_CHANNEL_LB_UPDATES = "lb:updates"


def compute_leaderboard_score(points: int, last_completed_at: Optional[datetime]) -> float:
    """
    Score formula: points + (1 - epoch_seconds / 1e10)
    Points are positive integers. The fraction breaks ties:
    Earlier completion timestamp yields a higher fraction.
    """
    if points <= 0:
        return 0.0
    epoch = last_completed_at.timestamp() if last_completed_at else 0.0
    tie_break_fraction = max(0.0, min(0.999999, 1.0 - (epoch / 1e10)))
    return float(points) + tie_break_fraction


class RankingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

    async def refresh_student(self, student_id: uuid.UUID) -> None:
        """
        Recomputes student points from DB and sets score absolutely in Redis.
        Broadcasts live update event over Redis pub/sub.
        """
        user = await self.user_repo.get_by_id(student_id)
        redis = await get_redis_client()

        # If user is not active, remove from leaderboard
        if not user or user.status != UserStatus.ACTIVE:
            await redis.zrem(REDIS_KEY_LB_OVERALL, str(student_id))
            await redis.publish(REDIS_CHANNEL_LB_UPDATES, json.dumps({"action": "remove", "student_id": str(student_id)}))
            return

        total_points, tasks_completed, last_completed_at = await self.task_repo.get_student_points_summary(student_id)

        if total_points <= 0:
            await redis.zrem(REDIS_KEY_LB_OVERALL, str(student_id))
        else:
            score = compute_leaderboard_score(total_points, last_completed_at)
            await redis.zadd(REDIS_KEY_LB_OVERALL, {str(student_id): score})

        # Broadcast update for live SSE listeners
        payload = {
            "action": "update",
            "student_id": str(student_id),
            "points": total_points,
            "tasks_completed": tasks_completed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await redis.publish(REDIS_CHANNEL_LB_UPDATES, json.dumps(payload))
        logger.info("Refreshed ranking for student %s: points=%d", student_id, total_points)

    async def get_top_students(
        self,
        scope: str = "overall",
        course_id: Optional[uuid.UUID] = None,
        limit: int = 4,
    ) -> LeaderboardResponse:
        redis = await get_redis_client()
        key = REDIS_KEY_LB_OVERALL if scope == "overall" or not course_id else f"lb:course:{course_id}"

        # Fetch top members from Redis
        try:
            top_member_ids = await redis.zrevrange(key, 0, limit - 1)
        except Exception as e:
            logger.warning("Redis leaderboard fetch failed: %s; falling back to DB", e)
            top_member_ids = []

        items: List[RankedStudentItem] = []

        if top_member_ids:
            for rank_idx, m_id in enumerate(top_member_ids, start=1):
                try:
                    s_uuid = uuid.UUID(m_id)
                    user = await self.user_repo.get_by_id(s_uuid)
                    if user and user.status == UserStatus.ACTIVE:
                        total_pts, tasks_cnt, _ = await self.task_repo.get_student_points_summary(s_uuid)
                        if total_pts > 0:
                            items.append(
                                RankedStudentItem(
                                    rank=rank_idx,
                                    student_id=user.id,
                                    name=user.full_name,
                                    avatar_url=user.avatar_url,
                                    points=total_pts,
                                    tasks_completed=tasks_cnt,
                                )
                            )
                except Exception:
                    continue

        # If Redis was empty or cold, fall back to SQL and seed Redis
        if not items:
            db_top = await self.task_repo.get_top_students_sql(course_id=course_id, limit=limit)
            for rank_idx, (s_id, name, avatar, pts, cnt, last_comp) in enumerate(db_top, start=1):
                items.append(
                    RankedStudentItem(
                        rank=rank_idx,
                        student_id=s_id,
                        name=name,
                        avatar_url=avatar,
                        points=int(pts),
                        tasks_completed=int(cnt),
                    )
                )
                score = compute_leaderboard_score(int(pts), last_comp)
                try:
                    await redis.zadd(key, {str(s_id): score})
                except Exception:
                    pass

        return LeaderboardResponse(
            updated_at=datetime.now(timezone.utc),
            scope=scope,
            course_id=course_id,
            items=items,
        )

    async def get_student_rank(
        self,
        student_id: uuid.UUID,
        scope: str = "overall",
        course_id: Optional[uuid.UUID] = None,
    ) -> MyRankResponse:
        redis = await get_redis_client()
        key = REDIS_KEY_LB_OVERALL if scope == "overall" or not course_id else f"lb:course:{course_id}"

        total_pts, tasks_cnt, last_comp = await self.task_repo.get_student_points_summary(student_id)
        if total_pts <= 0:
            return MyRankResponse(student_id=student_id, rank=None, points=0, tasks_completed=0)

        rank_val = None
        try:
            zrank = await redis.zrevrank(key, str(student_id))
            if zrank is not None:
                rank_val = zrank + 1
        except Exception:
            pass

        return MyRankResponse(
            student_id=student_id,
            rank=rank_val,
            points=total_pts,
            tasks_completed=tasks_cnt,
        )

    async def rebuild_all_scores(self) -> int:
        """Cold-start rebuild or nightly reconciliation of Redis leaderboard."""
        db_top = await self.task_repo.get_top_students_sql(limit=5000)
        redis = await get_redis_client()
        count = 0
        for s_id, _, _, pts, _, last_comp in db_top:
            score = compute_leaderboard_score(int(pts), last_comp)
            await redis.zadd(REDIS_KEY_LB_OVERALL, {str(s_id): score})
            count += 1
        logger.info("Rebuilt Redis leaderboard for %d students", count)
        return count
