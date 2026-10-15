"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  Clock,
  HelpCircle,
  Award,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Loader2,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, PageHeader } from "@/components/ui/Card";
import { PointsChip, Badge } from "@/components/ui/Badge";
import { api, getDevAuthToken } from "@/lib/api";

interface ApiExam {
  id: string;
  course_id: string;
  course_title?: string;
  title: string;
  instructions?: string | null;
  duration_minutes: number;
  total_marks: number;
  pass_marks: number;
  start_at: string;
  end_at: string;
  status: "draft" | "published" | "closed";
  questions_count?: number;
  task_points?: number;
}

export default function ExamsPage() {
  const { getToken } = useAuth();
  const [exams, setExams] = useState<ApiExam[]>([]);
  const [loading, setLoading] = useState(true);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("student");
    }
    return token;
  }, [getToken]);

  const loadExams = useCallback(async () => {
    setLoading(true);
    try {
      const token = await resolveToken();
      const data = await api<ApiExam[]>("/exams", token ?? undefined).catch(() => []);
      setExams(data || []);
    } catch (err) {
      console.error("Failed to load exams:", err);
    } finally {
      setLoading(false);
    }
  }, [resolveToken]);

  useEffect(() => {
    loadExams();
  }, [loadExams]);

  return (
    <>
      <PageHeader
        title="Course Examinations"
        subtitle="Exams open strictly within their scheduled window. Server-side timers and autosave ensure reliable testing."
        action={
          <span className="flex items-center gap-2 text-sm text-ink-muted">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-success" />
            Live Sync
          </span>
        }
      />

      {loading ? (
        <div className="flex h-56 items-center justify-center rounded-2xl border border-cream-300 bg-white">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : exams.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-cream-300 bg-white p-12 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-cream-400" />
          <h3 className="mt-3 font-heading text-lg font-bold text-green-900">
            No Active Course Examinations
          </h3>
          <p className="mt-1 text-sm text-ink-muted">
            There are currently no scheduled exams for your enrolled courses. Check back soon or consult the notice board.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {exams.map((e) => {
            const now = new Date();
            const start = new Date(e.start_at);
            const end = new Date(e.end_at);
            const isLive = e.status === "published" && now >= start && now <= end;
            const isUpcoming = e.status === "published" && now < start;
            const isClosed = e.status === "closed" || now > end;

            const windowStr = `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;

            return (
              <Card
                key={e.id}
                className="flex flex-col justify-between gap-4 transition-all hover:shadow-md"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-heading text-base font-bold text-green-900">
                      {e.title}
                    </h3>
                    {isLive ? (
                      <Badge tone="success">
                        <CheckCircle2 size={12} className="mr-1" /> Open Now
                      </Badge>
                    ) : isUpcoming ? (
                      <Badge tone="warning">
                        <Clock size={12} className="mr-1" /> Scheduled
                      </Badge>
                    ) : (
                      <Badge tone="neutral">Closed</Badge>
                    )}
                  </div>

                  <p className="text-xs text-ink-muted">
                    Course: <b className="text-ink">{e.course_title || "Academic Course"}</b>
                  </p>

                  <div className="flex items-center gap-1.5 text-xs text-ink-muted">
                    <Calendar size={13} className="text-green-700" />
                    <span>Window: {windowStr}</span>
                  </div>

                  <div className="flex flex-wrap gap-4 text-xs text-ink-muted pt-1">
                    <span className="inline-flex items-center gap-1">
                      <HelpCircle size={14} className="text-green-700" />
                      {e.questions_count ?? 10} Multiple Choice Questions
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Clock size={14} className="text-green-700" />
                      {e.duration_minutes} Minutes Duration
                    </span>
                  </div>
                </div>

                <div className="mt-auto flex items-center justify-between border-t border-cream-200 pt-3">
                  <PointsChip points={e.task_points ?? 0} />
                  {isLive ? (
                    <Button href={`/student/exams/${e.id}`} variant="primary" size="sm">
                      Start Exam Now
                    </Button>
                  ) : isUpcoming ? (
                    <Button variant="secondary" size="sm" disabled>
                      Opens {start.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </Button>
                  ) : (
                    <Button href="/student/results" variant="secondary" size="sm">
                      View Results
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
