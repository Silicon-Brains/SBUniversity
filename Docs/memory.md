# memory.md — SBUniversity Project Memory / Current State

> Update this file after every meaningful change.

## Current Phase
**Phase 0 — Documentation Foundation** (complete pending owner confirmation of assumptions)

## Current Task
Review documentation and confirm assumptions A1–A11 (PRD.md §17), especially the Task Points model (A3, A9–A11).

## Project Snapshot
- **Name:** SBUniversity
- **Frontend:** Next.js (App Router, TS) + Tailwind CSS
- **Backend:** FastAPI, Python 3.13 (interpreted from "python13.3")
- **DB:** Supabase PostgreSQL (backend-only access)
- **Auth:** Clerk — roles: student, teacher, admin
- **AI:** Google Gemini → chatbot "Aarsh Intelligence"
- **Cache/Realtime:** Redis (cache, leaderboard, rate-limit, pub/sub)
- **PDFs:** Generated in backend (ReportLab); downloaded in frontend as Blob
- **Brand colors:** Bordo `#6C151E`, Green `#0F3D3A`, Cream `#F5DABF` (60:30:10)
- **Live Ranking:** by **Task Points**, auto-awarded on task completion (Redis ZSET + SSE)

## Completed
- [x] PRD.md
- [x] architecture.md
- [x] database.md
- [x] rules.md
- [x] phases.md
- [x] design.md
- [x] memory.md
- [x] System_Design.md

## Completed Files
All 8 docs in `SBUniversity-docs/`.

## Files Currently Being Modified
None.

## Pending
- [ ] Owner confirms assumptions (A1–A11) incl. Task Points model
- [ ] Create Clerk, Supabase, Redis, Gemini accounts/keys
- [ ] Start Phase 1 — Project Setup

## Known Bugs
None (no code yet).

## Current Errors
None.

## Important Decisions
| # | Decision | Date |
|---|---|---|
| D1 | Modular monolith FastAPI; browser never talks to Supabase directly | Oct 14, 2026 |
| D2 | Role stored in Clerk publicMetadata + mirrored in DB; admin-only role changes | Oct 14, 2026 |
| D3 | Course progress = % published exams passed; certificate at 100% (no lessons in MVP) | Oct 14, 2026 |
| D4 | ~~Ranking by exam marks~~ **superseded by D8** — Redis ZSET + SSE for live remain | Oct 14, 2026 |
| D5 | ReportLab for PDF generation in backend | Oct 14, 2026 |
| D6 | Gemini model name configurable via `GEMINI_MODEL` env | Oct 14, 2026 |
| D8 | Live Ranking = total **Task Points** (all-time). Exam tasks auto-created on exam publish and auto-complete on pass; assignment tasks need teacher approval; points awarded once per (task, student) in the same DB transaction; tie-break = earliest to reach total; exam marks don't affect rank | Oct 14, 2026 |
| D9 | Leaderboard score recomputed from DB and set absolutely in Redis (no ZINCRBY); revoke instead of delete | Oct 14, 2026 |
| D7 | Palette 60% Cream+White / 30% Green / 10% Bordo; bordo never on green; functional colors are minimal exceptions | Oct 14, 2026 |

## Recent Changes
- Oct 14, 2026: Initial documentation set created.
- Oct 14, 2026: **Color palette changed** from blue/indigo/gold to **Bordo `#6C151E` / Green `#0F3D3A` / Cream `#F5DABF`** using the 60:30:10 rule (white as neutral). Updated `design.md` (v0.2), `rules.md` (§19), `phases.md` (Phase 2, 13). No architecture/DB changes.
- Oct 14, 2026: **Ranking model changed** from exam marks to **Task Points** (automated on task completion). New tables `tasks`, `task_completions`; new endpoints `/tasks/*`, `/student/points`, admin revoke; new pages `/student/tasks`, `/teacher/tasks`; ranking flow, rules (§20), phases (6, 7, 10, 12) and design (Ranking, Task card) updated. Docs updated: PRD, architecture, database, rules, phases, design, memory, System_Design.

## Next Task
Confirm assumptions → begin **Phase 1 — Project Setup** (create both repos, configs, CI).

## Deployment Status
Not deployed. No environments created yet.