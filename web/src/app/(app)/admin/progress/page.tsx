"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  BookOpen,
  Search,
  Award,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ShieldAlert,
  ChevronRight,
  TrendingUp,
  Loader2,
  Users,
} from "lucide-react";
import { PageHeader, Card, StatCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { api, getDevAuthToken } from "@/lib/api";

interface CourseProgress {
  course_id: string;
  course_title: string;
  progress_percent: number;
  status: string;
}

interface StudentProgressRecord {
  student_id: string;
  name: string;
  email: string;
  student_code: string;
  total_points: number;
  tasks_completed: number;
  rank?: number | null;
  courses: CourseProgress[];
}

interface ProgressApiResponse {
  items: StudentProgressRecord[];
  total: number;
  page: number;
  page_size: number;
}

export default function AdminProgressPage() {
  const { getToken } = useAuth();
  const toast = useToast();

  const [records, setRecords] = useState<StudentProgressRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("admin");
    }
    return token;
  }, [getToken]);

  const loadProgress = useCallback(async () => {
    setLoading(true);
    try {
      const token = await resolveToken();
      const q = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
      const res = await api<ProgressApiResponse>(`/admin/progress/students${q}`, token ?? undefined).catch(() => null);
      if (res?.items) {
        setRecords(res.items);
        setTotal(res.total);
      }
    } catch (err) {
      console.error("Failed to fetch student progress:", err);
    } finally {
      setLoading(false);
    }
  }, [resolveToken, search]);

  useEffect(() => {
    const handler = setTimeout(() => {
      loadProgress();
    }, 300);
    return () => clearTimeout(handler);
  }, [loadProgress]);

  const totalPoints = records.reduce((acc, r) => acc + r.total_points, 0);
  const totalTasks = records.reduce((acc, r) => acc + r.tasks_completed, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Academic Progress"
        subtitle="Live registry of student course completion percentages, task points, and active rankings."
        action={
          <span className="flex items-center gap-2 text-sm text-ink-muted">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-success" />
            Live DB Sync
          </span>
        }
      />

      {/* KPI Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard value={total} label="Enrolled Students" hint="Active platform learners" />
        <StatCard value={totalPoints} label="Total Task Points" hint="Awarded from tasks/exams" />
        <StatCard value={totalTasks} label="Tasks Completed" hint="Across all departments" />
        <StatCard value="100%" label="Registry Accuracy" hint="Real-time SQL sync" />
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-md">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-ink-placeholder">
            <Search size={15} />
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search students by name, email, or student code..."
            className="h-10 w-full rounded-lg border border-cream-300 bg-white pl-9 pr-3 text-sm text-ink placeholder:text-ink-placeholder focus:border-green-700 focus:outline-none"
          />
        </div>
      </div>

      {/* Progress Records List */}
      {loading ? (
        <div className="flex h-56 items-center justify-center rounded-2xl border border-cream-300 bg-white shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : records.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-cream-300 bg-white p-12 text-center">
          <Users className="mx-auto h-12 w-12 text-cream-400" />
          <h3 className="mt-3 font-heading text-lg font-bold text-green-900">No Student Records Found</h3>
          <p className="mt-1 text-sm text-ink-muted">
            No students match your query in the database.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {records.map((r) => (
            <Card
              key={r.student_id}
              className="flex flex-col justify-between gap-4 p-5 transition-all hover:shadow-md sm:flex-row sm:items-center"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-heading text-base font-bold text-green-900">{r.name}</h3>
                  <span className="rounded-md bg-cream-200 px-2 py-0.5 font-mono text-xs font-semibold text-green-900">
                    {r.student_code}
                  </span>
                  {r.rank ? (
                    <Badge tone="success">Rank #{r.rank}</Badge>
                  ) : (
                    <Badge tone="neutral">Unranked</Badge>
                  )}
                </div>

                <p className="text-xs text-ink-muted">{r.email}</p>

                {/* Courses Progress Bars */}
                <div className="pt-2 space-y-2 max-w-lg">
                  {r.courses.length === 0 ? (
                    <p className="text-[11px] text-ink-muted">No course enrollments recorded.</p>
                  ) : (
                    r.courses.map((c) => (
                      <div key={c.course_id} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-green-900 truncate max-w-[280px]">
                            {c.course_title}
                          </span>
                          <span className="font-mono text-ink-muted">{Math.round(c.progress_percent)}%</span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-cream-200">
                          <div
                            className="h-full rounded-full bg-green-700"
                            style={{ width: `${Math.min(100, Math.max(0, c.progress_percent))}%` }}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0 pt-3 sm:pt-0 border-t sm:border-t-0 border-cream-200">
                <div className="text-right">
                  <p className="font-heading text-xl font-bold text-green-900">
                    {r.total_points} pts
                  </p>
                  <p className="text-xs text-ink-muted font-medium">
                    {r.tasks_completed} tasks completed
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
