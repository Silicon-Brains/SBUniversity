# database.md — SBUniversity Database Design

## 1. Technology
- **Supabase PostgreSQL** (database name: `postgres`, schema `public`)
- Access: **FastAPI only** (SQLAlchemy 2 async + asyncpg) using the Supabase connection string (pooler).
- Migrations: **Alembic**.
- Extensions: `pgcrypto` (UUID), `citext` (case-insensitive email).
- Conventions: UUID PKs (`gen_random_uuid()`), `timestamptz`, `created_at`/`updated_at` on all mutable tables, snake_case.

## 2. Enums
```
user_role:        student | teacher | admin
user_status:      active | suspended | deleted
enrollment_status: active | completed | dropped
exam_status:      draft | published | closed
attempt_status:   in_progress | submitted | auto_submitted
notice_audience:  all | students | teachers | course
notice_priority:  normal | important | urgent
notice_status:    draft | published | archived
chat_role:        user | model
task_type:        exam | assignment
task_verification: auto | teacher_approval
task_status:      active | archived
completion_status: pending_review | completed | rejected | revoked
```

## 3. Entity Relationship Overview
```
users 1──1 student_profiles
users 1──1 teacher_profiles
departments 1──* student_profiles / teacher_profiles / courses
users(teacher) 1──* courses
users(student) *──* courses   (via enrollments)
courses 1──* exams 1──* questions 1──* question_options
exams 1──* exam_attempts *──1 users(student)
exam_attempts 1──* attempt_answers *──1 questions
exam_attempts 1──1 results
users(student) *──* courses → certificates
courses 1──* tasks            (exams 1──0..1 tasks, for exam-type tasks)
tasks 1──* task_completions *──1 users(student)
users 1──* notices (author)
users 1──* chat_sessions 1──* chat_messages
users 1──* audit_logs (actor)
```

## 4. Tables

### users
```
users
 ├── id                uuid PK default gen_random_uuid()
 ├── clerk_user_id     text UNIQUE NOT NULL
 ├── email             citext UNIQUE NOT NULL
 ├── full_name         text NOT NULL
 ├── avatar_url        text NULL
 ├── role              user_role NOT NULL default 'student'
 ├── status            user_status NOT NULL default 'active'
 ├── last_seen_at      timestamptz NULL
 ├── created_at        timestamptz NOT NULL default now()
 └── updated_at        timestamptz NOT NULL default now()
```
Indexes: `(role)`, `(status)`, `(lower(full_name))`.

### departments
```
departments
 ├── id        uuid PK
 ├── code      text UNIQUE NOT NULL
 ├── name      text UNIQUE NOT NULL
 └── created_at timestamptz default now()
```

### student_profiles
```
student_profiles
 ├── user_id          uuid PK → users.id ON DELETE CASCADE
 ├── student_code     text UNIQUE NOT NULL        -- SBU-2026-0001
 ├── department_id    uuid NULL → departments.id
 ├── batch_year       int NULL
 ├── phone            text NULL
 ├── date_of_birth    date NULL
 ├── photo_path       text NULL                   -- Supabase Storage
 ├── id_valid_until   date NULL
 ├── qr_token         text UNIQUE NOT NULL        -- random, for public verify
 └── updated_at       timestamptz
```

### teacher_profiles
```
teacher_profiles
 ├── user_id        uuid PK → users.id ON DELETE CASCADE
 ├── employee_code  text UNIQUE NOT NULL
 ├── department_id  uuid NULL → departments.id
 ├── designation    text NULL
 └── bio            text NULL
```

### courses
```
courses
 ├── id            uuid PK
 ├── code          text UNIQUE NOT NULL
 ├── title         text NOT NULL
 ├── description   text NULL
 ├── department_id uuid NULL → departments.id
 ├── teacher_id    uuid NOT NULL → users.id        -- must have role teacher
 ├── is_published  boolean NOT NULL default false
 ├── created_at / updated_at
```
Indexes: `(teacher_id)`, `(department_id)`.

### enrollments
```
enrollments
 ├── id                uuid PK
 ├── student_id        uuid NOT NULL → users.id
 ├── course_id         uuid NOT NULL → courses.id
 ├── status            enrollment_status default 'active'
 ├── progress_percent  numeric(5,2) default 0     -- derived, cached
 ├── enrolled_at       timestamptz default now()
 ├── completed_at      timestamptz NULL
 └── UNIQUE (student_id, course_id)
```
Indexes: `(course_id)`, `(student_id)`.

### exams
```
exams
 ├── id                 uuid PK
 ├── course_id          uuid NOT NULL → courses.id
 ├── created_by         uuid NOT NULL → users.id
 ├── title              text NOT NULL
 ├── instructions       text NULL
 ├── duration_minutes   int NOT NULL CHECK (> 0)
 ├── total_marks        numeric(7,2) NOT NULL         -- computed from questions
 ├── pass_marks         numeric(7,2) NOT NULL CHECK (pass_marks <= total_marks)
 ├── negative_marking   numeric(4,2) NOT NULL default 0
 ├── max_attempts       int NOT NULL default 1
 ├── shuffle_questions  boolean default true
 ├── show_review        boolean default true          -- show per-question review
 ├── start_at           timestamptz NOT NULL
 ├── end_at             timestamptz NOT NULL CHECK (end_at > start_at)
 ├── status             exam_status default 'draft'
 ├── created_at / updated_at
```
Indexes: `(course_id, status)`, `(start_at, end_at)`.

### questions
```
questions
 ├── id           uuid PK
 ├── exam_id      uuid NOT NULL → exams.id ON DELETE CASCADE
 ├── text         text NOT NULL
 ├── marks        numeric(5,2) NOT NULL default 1
 ├── position     int NOT NULL
 ├── explanation  text NULL
 └── UNIQUE (exam_id, position)
```

### question_options
```
question_options
 ├── id           uuid PK
 ├── question_id  uuid NOT NULL → questions.id ON DELETE CASCADE
 ├── text         text NOT NULL
 ├── is_correct   boolean NOT NULL default false
 ├── position     int NOT NULL
 └── UNIQUE (question_id, position)
```
Rule: exactly **one** `is_correct = true` per question (MVP) — enforced by partial unique index `ON question_options(question_id) WHERE is_correct`.

### exam_attempts
```
exam_attempts
 ├── id            uuid PK
 ├── exam_id       uuid NOT NULL → exams.id
 ├── student_id    uuid NOT NULL → users.id
 ├── attempt_no    int NOT NULL default 1
 ├── status        attempt_status default 'in_progress'
 ├── started_at    timestamptz NOT NULL default now()
 ├── expires_at    timestamptz NOT NULL      -- min(started_at+duration, exam.end_at)
 ├── submitted_at  timestamptz NULL
 └── UNIQUE (exam_id, student_id, attempt_no)
```
Indexes: `(student_id)`, `(exam_id)`, partial `(student_id) WHERE status='in_progress'`.

### attempt_answers
```
attempt_answers
 ├── id                  uuid PK
 ├── attempt_id          uuid NOT NULL → exam_attempts.id ON DELETE CASCADE
 ├── question_id         uuid NOT NULL → questions.id
 ├── selected_option_id  uuid NULL → question_options.id
 ├── answered_at         timestamptz default now()
 └── UNIQUE (attempt_id, question_id)
```

### results
```
results
 ├── id             uuid PK
 ├── attempt_id     uuid UNIQUE NOT NULL → exam_attempts.id
 ├── exam_id        uuid NOT NULL → exams.id
 ├── student_id     uuid NOT NULL → users.id
 ├── score          numeric(7,2) NOT NULL
 ├── total_marks    numeric(7,2) NOT NULL
 ├── percentage     numeric(5,2) NOT NULL
 ├── grade          text NOT NULL            -- A+, A, B...
 ├── passed         boolean NOT NULL
 ├── time_taken_sec int NOT NULL
 ├── rank_in_exam   int NULL                 -- per-exam rank, informational (NOT the Live Ranking)
 ├── pdf_path       text NULL                -- cached PDF in Storage
 └── created_at     timestamptz default now()
```
Indexes: `(student_id)`, `(exam_id, score DESC, time_taken_sec ASC)`.

### certificates
```
certificates
 ├── id                uuid PK
 ├── certificate_code  text UNIQUE NOT NULL   -- e.g. SBU-CERT-7F3K9Q2M
 ├── student_id        uuid NOT NULL → users.id
 ├── course_id         uuid NOT NULL → courses.id
 ├── final_percentage  numeric(5,2) NOT NULL
 ├── issued_at         timestamptz default now()
 ├── revoked_at        timestamptz NULL
 ├── revoked_by        uuid NULL → users.id
 ├── pdf_path          text NULL
 └── UNIQUE (student_id, course_id)
```

### tasks
```
tasks
 ├── id            uuid PK
 ├── course_id     uuid NOT NULL → courses.id
 ├── created_by    uuid NOT NULL → users.id
 ├── type          task_type NOT NULL
 ├── exam_id       uuid NULL UNIQUE → exams.id ON DELETE RESTRICT   -- exam tasks only
 ├── title         text NOT NULL
 ├── description   text NULL
 ├── points        int NOT NULL CHECK (points >= 0)
 ├── verification  task_verification NOT NULL
 ├── due_at        timestamptz NULL                                  -- informational
 ├── status        task_status NOT NULL default 'active'
 ├── created_at / updated_at
```
Checks: `type='exam' ⇒ exam_id IS NOT NULL AND verification='auto'`; `type='assignment' ⇒ exam_id IS NULL AND verification='teacher_approval'`.
Indexes: `(course_id, status)`, `(created_by)`.
Rules (service layer): exam tasks are created/archived by exam publish/close; `points` becomes **immutable** once any completion exists; published exams cannot be hard-deleted.

### task_completions
```
task_completions
 ├── id                uuid PK
 ├── task_id           uuid NOT NULL → tasks.id
 ├── student_id        uuid NOT NULL → users.id
 ├── status            completion_status NOT NULL
 ├── submission_note   text NULL                  -- assignment tasks
 ├── submission_url    text NULL
 ├── points_awarded    int NOT NULL default 0     -- snapshot of task.points when completed
 ├── submitted_at      timestamptz NOT NULL default now()
 ├── completed_at      timestamptz NULL           -- set when status becomes 'completed'
 ├── reviewed_by       uuid NULL → users.id
 ├── reviewed_at       timestamptz NULL
 ├── review_note       text NULL
 ├── revoked_by        uuid NULL → users.id
 ├── revoked_at        timestamptz NULL
 └── UNIQUE (task_id, student_id)                 -- guarantees points are awarded once
```
Indexes: `(student_id, status)`, `(task_id, status)`, partial `(student_id, completed_at) WHERE status='completed'`.
Constraint: `status='completed' ⇒ completed_at IS NOT NULL AND points_awarded >= 0`.
Rows are **never hard-deleted** — revoke instead (keeps the audit trail).

### notices
```
notices
 ├── id            uuid PK
 ├── author_id     uuid NOT NULL → users.id
 ├── title         text NOT NULL
 ├── body          text NOT NULL
 ├── audience      notice_audience NOT NULL default 'all'
 ├── course_id     uuid NULL → courses.id        -- required when audience='course'
 ├── priority      notice_priority default 'normal'
 ├── is_pinned     boolean default false
 ├── status        notice_status default 'published'
 ├── published_at  timestamptz default now()
 ├── expires_at    timestamptz NULL
 ├── created_at / updated_at
```
Check: `audience='course'` ⇒ `course_id IS NOT NULL`. Indexes: `(status, published_at DESC)`, `(course_id)`.
Rule (service layer): teachers may only use `audience='course'` for their own courses.

### chat_sessions / chat_messages
```
chat_sessions
 ├── id          uuid PK
 ├── user_id     uuid NOT NULL → users.id ON DELETE CASCADE
 ├── title       text NULL
 └── created_at, updated_at

chat_messages
 ├── id          uuid PK
 ├── session_id  uuid NOT NULL → chat_sessions.id ON DELETE CASCADE
 ├── role        chat_role NOT NULL
 ├── content     text NOT NULL
 ├── created_at  timestamptz default now()
```
Index: `(session_id, created_at)`.

### audit_logs
```
audit_logs
 ├── id           bigserial PK
 ├── actor_id     uuid NULL → users.id
 ├── action       text NOT NULL         -- e.g. user.role_changed
 ├── entity_type  text NOT NULL
 ├── entity_id    text NULL
 ├── metadata     jsonb default '{}'
 ├── ip_address   inet NULL
 └── created_at   timestamptz default now()
```
Index: `(created_at DESC)`, `(actor_id)`.

## 5. Derived Data (no duplicate storage)
- **Leaderboard (Task Points):** computed from `task_completions` and held in Redis; rebuilt from DB on cold start and reconciled nightly. Exam marks are **not** used.
  ```sql
  -- Overall Top 4
  SELECT tc.student_id,
         SUM(tc.points_awarded) AS points,
         COUNT(*)               AS tasks_completed,
         MAX(tc.completed_at)   AS last_completed_at
  FROM task_completions tc
  JOIN users u ON u.id = tc.student_id AND u.status = 'active'
  WHERE tc.status = 'completed'
  GROUP BY tc.student_id
  HAVING SUM(tc.points_awarded) > 0
  ORDER BY points DESC, last_completed_at ASC
  LIMIT 4;
  -- Course scope: JOIN tasks t ON t.id = tc.task_id WHERE t.course_id = :course_id
  ```
  Redis score = `points + (1 − epoch_seconds(last_completed_at) / 1e10)` (tie-break: earlier wins), set absolutely via `ZADD`.
- **Course progress:** `passed published exams / total published exams` per enrollment (cached in `enrollments.progress_percent` on result creation).
- **Analytics:** aggregate queries over `results`, `exam_attempts`, `exams` (cached in Redis).

## 6. Important Queries
1. Exams available to a student (enrolled, published, within window, attempts left).
2. Active attempt for a student (blocks AI exam-help).
3. Grading: join `attempt_answers` → `question_options.is_correct`.
4. Top 4 leaderboard (above) and "my rank" (`ZREVRANK` in Redis).
5. Course completion check (all published exams passed).
6. Teacher analytics: exams, submissions, avg score, pass rate per teacher.
7. Notice feed filtered by audience/course/expiry.
8. Award points (idempotent): `INSERT INTO task_completions ... ON CONFLICT (task_id, student_id) DO NOTHING` inside the grading/approval transaction.
9. Student points summary: total, tasks completed, history (`task_completions` joined to `tasks`).
10. Teacher approval queue: `status='pending_review'` for tasks in own courses.

## 7. Seed / Dummy Data Requirements
- 3 departments, 1 admin, 3 teachers, 20 students.
- 4 courses (1 per teacher + 1 shared), 2 exams per course with 10 MCQs each.
- Enrollments for all students; ~40 results with varied scores (Result pages).
- ~6 tasks per course (exam tasks + assignment tasks, points 10–100) and ~60 task completions (completed / pending / rejected / one revoked) with varied totals to test the leaderboard, including **ties**.
- 5 notices (mix of admin/teacher, pinned, expired).
- 1 revoked + 2 valid certificates.
Seed script: `scripts/seed.py` (dev/staging only; never run in production).

## 8. Database Security
- Enable **RLS on all tables** with **no policies** for `anon`/`authenticated` roles → direct Supabase client access is denied. Backend uses a dedicated DB role / service connection.
- Service-role key and DB URL only in backend env.
- Storage buckets private; PDFs/photos served via backend or short-lived signed URLs.
- `is_correct` never selected in student-facing queries pre-submission.
- Parameterized queries only (SQLAlchemy). No raw string SQL with user input.
- Daily automated backups (Supabase), PITR if plan allows.
- PII minimal; soft delete (`status='deleted'`) for users; audit log immutable (no update/delete from app).
- `points_awarded` is written only by backend services (snapshot of `tasks.points`); no API accepts points from clients. Revokes are audit-logged.