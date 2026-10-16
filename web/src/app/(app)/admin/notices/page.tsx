"use client";
import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  Megaphone,
  Plus,
  Pin,
  Trash2,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { PageHeader, Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { api, getDevAuthToken } from "@/lib/api";

interface NoticeItem {
  id: string;
  title: string;
  body: string;
  author_name?: string | null;
  priority: "normal" | "important" | "urgent";
  audience: "all" | "students" | "teachers" | "course";
  is_pinned: boolean;
  created_at: string;
}

export default function AdminNoticesPage() {
  const { getToken } = useAuth();
  const [notices, setNotices] = useState<NoticeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState<"normal" | "important" | "urgent">("normal");
  const [newTarget, setNewTarget] = useState<"all" | "students" | "teachers">("all");
  const [isPinned, setIsPinned] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const toast = useToast();

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("admin");
    }
    return token;
  }, [getToken]);

  const loadNotices = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const token = await resolveToken();
      const data = await api<NoticeItem[]>("/admin/notices", token ?? undefined);
      setNotices(data);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load notices.");
    } finally {
      setLoading(false);
    }
  }, [resolveToken]);

  useEffect(() => {
    void loadNotices();
  }, [loadNotices]);

  const resetForm = () => {
    setNewTitle("");
    setNewBody("");
    setNewPriority("normal");
    setNewTarget("all");
    setIsPinned(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newBody.trim()) return;

    setIsSaving(true);
    try {
      const token = await resolveToken();
      await api<NoticeItem>("/notices", token ?? undefined, {
        method: "POST",
        body: JSON.stringify({
          title: newTitle.trim(),
          body: newBody.trim(),
          audience: newTarget,
          priority: newPriority,
          is_pinned: isPinned,
        }),
      });
      await loadNotices();
      setIsModalOpen(false);
      resetForm();
      toast("New university notice published.");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to publish notice.");
    } finally {
      setIsSaving(false);
    }
  };

  const togglePin = async (id: string) => {
    setProcessingId(id);
    try {
      const token = await resolveToken();
      await api(`/admin/notices/${id}/pin`, token ?? undefined, { method: "POST" });
      await loadNotices();
      toast("Notice pin status updated.");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to update notice pin.");
    } finally {
      setProcessingId(null);
    }
  };

  const deleteNotice = async (id: string) => {
    setProcessingId(id);
    try {
      const token = await resolveToken();
      await api(`/notices/${id}`, token ?? undefined, { method: "DELETE" });
      setNotices((prev) => prev.filter((notice) => notice.id !== id));
      toast("Notice removed.");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to delete notice.");
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notice Board Control"
        subtitle="Publish, pin, and manage broadcast announcements across the student and faculty body."
        action={
          <Button variant="primary" size="md" className="w-full justify-center sm:w-auto" onClick={() => setIsModalOpen(true)}>
            <Plus size={16} /> Broadcast New Notice
          </Button>
        }
      />

      {loading ? (
        <div className="flex h-56 items-center justify-center rounded-2xl border border-cream-300 bg-white">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : loadError ? (
        <Card className="p-8 text-center">
          <p className="text-sm text-danger">{loadError}</p>
          <Button variant="secondary" size="sm" className="mt-4" onClick={() => void loadNotices()}>
            <RefreshCw size={14} /> Try Again
          </Button>
        </Card>
      ) : notices.length === 0 ? (
        <Card className="p-10 text-center">
          <Megaphone className="mx-auto h-10 w-10 text-cream-400" />
          <p className="mt-3 text-sm text-ink-muted">No notices have been published.</p>
        </Card>
      ) : (
      <div className="space-y-4">
        {notices.map((n) => (
          <Card key={n.id} className="p-5 sm:p-6 space-y-3 transition-all hover:shadow-md">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-cream-200 pb-3">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="break-words font-heading text-base font-bold text-green-900">{n.title}</h3>
                {n.is_pinned && (
                  <Badge tone="info">
                    <Pin size={11} className="mr-0.5" /> Pinned
                  </Badge>
                )}
                {n.priority === "urgent" && <Badge tone="urgent">Urgent</Badge>}
                {n.priority === "important" && <Badge tone="info">Important</Badge>}
                {n.priority === "normal" && <Badge tone="neutral">General</Badge>}
                <span className="rounded bg-cream-100 px-2 py-0.5 text-[11px] font-medium text-green-900 capitalize">
                  Target: {n.audience}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => togglePin(n.id)}
                  disabled={processingId === n.id}
                  className={`grid min-h-11 min-w-11 place-items-center rounded-lg transition-colors ${
                    n.is_pinned
                      ? "bg-cream-200 text-green-900"
                      : "text-ink-muted hover:bg-cream-100"
                  }`}
                  title={n.is_pinned ? "Unpin notice" : "Pin notice to top"}
                >
                  <Pin size={16} />
                </button>
                <button
                  onClick={() => deleteNotice(n.id)}
                  disabled={processingId === n.id}
                  className="grid min-h-11 min-w-11 place-items-center rounded-lg text-danger hover:bg-danger-bg"
                  title="Delete notice"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>

            <p className="break-words text-sm leading-relaxed text-ink">{n.body}</p>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 text-xs text-ink-muted">
              <span className="break-words">Author: <b className="text-ink">{n.author_name || "Administration"}</b></span>
              <span>{new Date(n.created_at).toLocaleDateString()}</span>
            </div>
          </Card>
        ))}
      </div>
      )}

      {/* Broadcast Notice Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-green-900/60 p-3 backdrop-blur-sm sm:items-center sm:p-4">
          <div role="dialog" aria-modal="true" aria-labelledby="broadcast-notice-title" className="my-auto max-h-[calc(100dvh-1.5rem)] w-full max-w-lg overflow-y-auto rounded-2xl border border-cream-300 bg-white p-4 shadow-2xl sm:max-h-[calc(100dvh-2rem)] sm:p-6">
            <h3 className="font-heading text-lg font-bold text-green-900 border-b border-cream-200 pb-3">
              <span id="broadcast-notice-title">Broadcast University Announcement</span>
            </h3>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Notice Title
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Schedule for Final Exam Registration"
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-green-900 mb-1">
                    Priority Level
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as NoticeItem["priority"])}
                    className="h-11 w-full rounded-lg border border-cream-300 bg-white px-2 text-xs text-ink focus:border-green-700 focus:outline-none"
                  >
                    <option value="normal">Normal / General</option>
                    <option value="important">Important</option>
                    <option value="urgent">Urgent Announcement</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-green-900 mb-1">
                    Target Audience
                  </label>
                  <select
                    value={newTarget}
                    onChange={(e) => setNewTarget(e.target.value as "all" | "students" | "teachers")}
                    className="h-11 w-full rounded-lg border border-cream-300 bg-white px-2 text-xs text-ink focus:border-green-700 focus:outline-none"
                  >
                    <option value="all">All University Members</option>
                    <option value="students">Students Only</option>
                    <option value="teachers">Teachers & Faculty Only</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Announcement Content
                </label>
                <textarea
                  required
                  rows={4}
                  value={newBody}
                  onChange={(e) => setNewBody(e.target.value)}
                  placeholder="Provide detailed instructions or notice information..."
                  className="w-full rounded-lg border border-cream-300 bg-white p-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <label               className="flex min-h-11 items-center gap-2 text-xs font-medium text-green-900 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPinned}
                  onChange={(e) => setIsPinned(e.target.checked)}
                  className="h-4 w-4 text-green-700 rounded focus:ring-green-700"
                />
                <span>Pin this notice to top of Notice Board</span>
              </label>

              <div className="flex flex-col-reverse gap-2 border-t border-cream-200 pt-4 sm:flex-row sm:justify-end">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsModalOpen(false);
                    resetForm();
                  }}
                  disabled={isSaving}
                  className="w-full justify-center sm:w-auto"
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" disabled={isSaving} className="w-full justify-center sm:w-auto">
                  {isSaving ? <Loader2 size={14} className="animate-spin" /> : "Publish Notice"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
