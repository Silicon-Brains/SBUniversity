"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Badge, PointsChip } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import { api, getDevAuthToken } from "@/lib/api";
import {
  CheckCircle2,
  Clock,
  FileText,
  Link as LinkIcon,
  Send,
  X,
  Loader2,
  AlertCircle,
} from "lucide-react";

export interface TaskItem {
  id: string;
  course_id: string;
  course_title?: string;
  title: string;
  description?: string | null;
  type: "exam" | "assignment";
  verification: "auto" | "teacher_approval";
  points: number;
  due_at?: string | null;
  my_status?: "pending_review" | "completed" | "rejected" | "revoked" | null;
  points_earned?: number;
}

const filters = ["all", "open", "pending", "done"] as const;
const label = {
  all: "All Tasks",
  open: "Open Tasks",
  pending: "Pending Faculty Review",
  done: "Completed & Awarded",
};

export function TaskList({ initial }: { initial?: TaskItem[] }) {
  const { getToken } = useAuth();
  const toast = useToast();

  const [items, setItems] = useState<TaskItem[]>(initial ?? []);
  const [loading, setLoading] = useState(!initial || initial.length === 0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");

  const [submittingTask, setSubmittingTask] = useState<TaskItem | null>(null);
  const [submissionNote, setSubmissionNote] = useState("");
  const [submissionUrl, setSubmissionUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("student");
    }
    return token;
  }, [getToken]);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const token = await resolveToken();
      const data = await api<TaskItem[]>("/tasks", token ?? undefined);
      setItems(data);
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
      setLoadError(err instanceof Error ? err.message : "Failed to load tasks.");
    } finally {
      setLoading(false);
    }
  }, [resolveToken]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  function getComputedStatus(t: TaskItem): "open" | "pending" | "done" {
    if (t.my_status === "completed") return "done";
    if (t.my_status === "pending_review") return "pending";
    return "open";
  }

  const shown = items.filter((t) => {
    const s = getComputedStatus(t);
    return filter === "all" || s === filter;
  });

  function handleOpenSubmit(task: TaskItem) {
    setSubmittingTask(task);
    setSubmissionNote("");
    setSubmissionUrl("");
  }

  async function handleConfirmSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!submittingTask) return;

    setIsSubmitting(true);
    try {
      const token = await resolveToken();
      await api(
        `/tasks/${submittingTask.id}/complete`,
        token ?? undefined,
        {
          method: "POST",
          body: JSON.stringify({
            note: submissionNote.trim() || undefined,
            url: submissionUrl.trim() || undefined,
          }),
        }
      );

      // Refresh list from DB
      await loadTasks();
      toast(`Submitted "${submittingTask.title}" successfully! Points will be credited.`);
      setSubmittingTask(null);
    } catch (err: any) {
      toast(err?.message || "Failed to submit task.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      {/* Filter Tabs */}
      <div className="mb-6 flex flex-wrap gap-2" role="tablist" aria-label="Filter tasks">
        {filters.map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            onClick={() => setFilter(f)}
            className={`h-10 rounded-full px-4 text-xs font-semibold transition-all ${
              filter === f
                ? "bg-green-700 text-cream-50 shadow-sm"
                : "bg-white text-green-700 ring-1 ring-cream-300 hover:bg-green-50"
            }`}
          >
            {label[f]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-56 items-center justify-center rounded-2xl border border-cream-300 bg-white">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : loadError ? (
        <Card className="p-8 text-center">
          <p className="text-sm text-danger">{loadError}</p>
          <Button variant="secondary" size="sm" className="mt-4" onClick={() => void loadTasks()}>
            Try Again
          </Button>
        </Card>
      ) : shown.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-cream-300 bg-white p-12 text-center">
          <CheckCircle2 className="mx-auto h-12 w-12 text-cream-400" />
          <h3 className="mt-3 font-heading text-lg font-bold text-green-900">No Tasks in this category</h3>
          <p className="mt-1 text-sm text-ink-muted">
            All caught up or no active tasks available under the selected filter.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {shown.map((t) => {
            const status = getComputedStatus(t);
            const dueStr = t.due_at
              ? new Date(t.due_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })
              : "Ongoing";

            return (
              <Card
                key={t.id}
                className="flex flex-col justify-between gap-3 p-5 sm:p-6 transition-all hover:shadow-md"
              >
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-heading text-base font-bold text-green-900">{t.title}</h3>
                    {status === "open" && <Badge tone="info">Open</Badge>}
                    {status === "pending" && <Badge tone="warning">Pending Review</Badge>}
                    {status === "done" && <Badge tone="success">Completed</Badge>}
                  </div>

                  <p className="text-xs text-ink-muted">
                    {t.course_title || "Course Task"} · Due: {dueStr} ·{" "}
                    {t.type === "exam" ? "Awarded on passing exam" : "Requires faculty approval"}
                  </p>

                  {t.description && (
                    <p className="text-xs text-ink line-clamp-2 mt-1">{t.description}</p>
                  )}
                </div>

                <div className="mt-auto flex items-center justify-between gap-3 border-t border-cream-200 pt-3">
                  <PointsChip points={t.points} earned={status === "done"} />
                  {status === "open" &&
                    (t.type === "exam" ? (
                      <Button href="/student/exams" size="sm" variant="secondary">
                        Go to Exam
                      </Button>
                    ) : (
                      <Button variant="primary" size="sm" onClick={() => handleOpenSubmit(t)}>
                        Submit for Review
                      </Button>
                    ))}
                  {status === "pending" && (
                    <span className="text-xs font-medium text-warning flex items-center gap-1">
                      <Clock size={13} /> Awaiting Faculty
                    </span>
                  )}
                  {status === "done" && (
                    <span className="text-xs font-medium text-success flex items-center gap-1">
                      <CheckCircle2 size={13} /> Points Credited
                    </span>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Task Submission Modal */}
      {submittingTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-green-900/50 backdrop-blur-sm"
            onClick={() => setSubmittingTask(null)}
          />
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-cream-300">
            <div className="flex items-start justify-between gap-3 border-b border-cream-200 pb-3">
              <div>
                <h3 className="font-heading text-lg font-bold text-green-900">
                  Submit Task for Faculty Review
                </h3>
                <p className="text-xs text-ink-muted">{submittingTask.title}</p>
              </div>
              <button
                onClick={() => setSubmittingTask(null)}
                className="rounded-lg p-1 text-ink-muted hover:bg-cream-100 hover:text-ink"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleConfirmSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Submission Notes / Text Summary
                </label>
                <textarea
                  rows={3}
                  required
                  value={submissionNote}
                  onChange={(e) => setSubmissionNote(e.target.value)}
                  placeholder="Describe your solution, methodology, or answers..."
                  className="w-full rounded-lg border border-cream-300 p-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Project / Repository / Drive URL (Optional)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-ink-muted">
                    <LinkIcon size={14} />
                  </span>
                  <input
                    type="url"
                    value={submissionUrl}
                    onChange={(e) => setSubmissionUrl(e.target.value)}
                    placeholder="https://github.com/... or Google Drive link"
                    className="h-10 w-full rounded-lg border border-cream-300 pl-9 pr-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-cream-200">
                <button
                  type="button"
                  onClick={() => setSubmittingTask(null)}
                  className="h-9 rounded-lg border border-cream-300 px-4 text-xs font-semibold text-ink-muted hover:bg-cream-100"
                >
                  Cancel
                </button>
                <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 size={14} className="animate-spin mr-1.5" /> Submitting...
                    </>
                  ) : (
                    <>
                      <Send size={14} /> Submit Task
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
