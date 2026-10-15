# SBUniversity Web

Next.js 15 (App Router, TypeScript strict) + Tailwind CSS 3. Light theme, Bordo/Green/Cream palette (60:30:10) from `design.md`.

## Run
```bash
npm install
cp .env.example .env.local
npm run dev        # http://localhost:3000
```

## Demo accounts (`NEXT_PUBLIC_DEMO_MODE=true`)
| Role | Email | Password |
|---|---|---|
| Student | student@sbu.demo | Student@123 |
| Teacher | teacher@sbu.demo | Teacher@123 |
| Admin | admin@sbu.demo | Admin@123 |

Demo mode uses an httpOnly cookie and mock data in `src/lib/mock.ts`. **Set `NEXT_PUBLIC_DEMO_MODE=false` before deploying.**

## Production (Clerk)
1. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`.
2. Clerk Dashboard → Sessions → customize token: `{ "metadata": "{{user.public_metadata}}" }` so `middleware.ts` can read `role`.
3. Admin sets `publicMetadata.role` (`student` default, `teacher`, `admin`).
4. Replace `src/lib/mock.ts` calls with `api()` from `src/lib/api.ts` (FastAPI `/api/v1`).

## Structure
```
src/app/(app)/{student,teacher,admin,ranking,notices}   role-gated pages
src/components/ui        Button, Card, Badge, Toast primitives
src/components/shell     Shell (sidebar + topbar, mobile drawer)
src/components/features  TaskList, RankBoard, ApprovalQueue, UsersTable
src/lib                  auth, actions, api, mock
src/middleware.ts        role gating (layer 1 of 3; the API enforces RBAC too)
```

## Next (see phases.md)
Exam runner, results + PDF download (`downloadPdf`), certificates + `/verify/[code]`, ID card, notices CRUD, Aarsh Intelligence chat, SSE ranking stream, admin analytics.
