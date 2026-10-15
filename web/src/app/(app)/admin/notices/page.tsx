"use client";
import React, { useState } from "react";
import {
  Megaphone,
  Plus,
  Pin,
  Trash2,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Users,
} from "lucide-react";
import { PageHeader, Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";

interface NoticeItem {
  id: string;
  title: string;
  body: string;
  author: string;
  priority: "normal" | "important" | "urgent";
  targetRole: "all" | "student" | "teacher";
  pinned: boolean;
  date: string;
}

const MOCK_ADMIN_NOTICES: NoticeItem[] = [
  {
    id: "n-1",
    title: "Midterm Examination Schedule Published",
    body: "The Data Structures midterm examination opens on Oct 18 and closes Oct 20 at 6 PM. All students have 1 attempt of 45 minutes duration.",
    author: "Dr. Meera Iyer (Faculty)",
    priority: "important",
    targetRole: "all",
    pinned: true,
    date: "Oct 12, 2026",
  },
  {
    id: "n-2",
    title: "Scheduled Portal Maintenance & Upgrades",
    body: "Academic result generation and certificate verification will undergo scheduled maintenance tonight between 1:00 AM and 2:00 AM IST.",
    author: "Rohan Desai (Admin)",
    priority: "urgent",
    targetRole: "all",
    pinned: true,
    date: "Oct 14, 2026",
  },
  {
    id: "n-3",
    title: "Central Library Operating Hours Adjusted",
    body: "The central library and digital study labs will close at 4:00 PM this Friday for infrastructure upgrades.",
    author: "Rohan Desai (Admin)",
    priority: "normal",
    targetRole: "all",
    pinned: false,
    date: "Oct 10, 2026",
  },
];

export default function AdminNoticesPage() {
  const [notices, setNotices] = useState(MOCK_ADMIN_NOTICES);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState<"normal" | "important" | "urgent">("normal");
  const [newTarget, setNewTarget] = useState<"all" | "student" | "teacher">("all");
  const [isPinned, setIsPinned] = useState(false);

  const toast = useToast();

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newBody.trim()) return;

    const newNotice: NoticeItem = {
      id: `n-${Date.now()}`,
      title: newTitle.trim(),
      body: newBody.trim(),
      author: "Admin Registry",
      priority: newPriority,
      targetRole: newTarget,
      pinned: isPinned,
      date: "Just now",
    };

    setNotices([newNotice, ...notices]);
    setIsModalOpen(false);
    setNewTitle("");
    setNewBody("");
    setIsPinned(false);
    toast("New university notice published.");
  };

  const togglePin = (id: string) => {
    setNotices((prev) =>
      prev.map((n) => (n.id === id ? { ...n, pinned: !n.pinned } : n))
    );
    toast("Notice pin status updated.");
  };

  const deleteNotice = (id: string) => {
    setNotices((prev) => prev.filter((n) => n.id !== id));
    toast("Notice removed.");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notice Board Control"
        subtitle="Publish, pin, and manage broadcast announcements across the student and faculty body."
        action={
          <Button variant="primary" size="md" onClick={() => setIsModalOpen(true)}>
            <Plus size={16} /> Broadcast New Notice
          </Button>
        }
      />

      <div className="space-y-4">
        {notices.map((n) => (
          <Card key={n.id} className="p-5 sm:p-6 space-y-3 transition-all hover:shadow-md">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-cream-200 pb-3">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-heading text-base font-bold text-green-900">{n.title}</h3>
                {n.pinned && (
                  <Badge tone="info">
                    <Pin size={11} className="mr-0.5" /> Pinned
                  </Badge>
                )}
                {n.priority === "urgent" && <Badge tone="urgent">Urgent</Badge>}
                {n.priority === "important" && <Badge tone="info">Important</Badge>}
                {n.priority === "normal" && <Badge tone="neutral">General</Badge>}
                <span className="rounded bg-cream-100 px-2 py-0.5 text-[11px] font-medium text-green-900 capitalize">
                  Target: {n.targetRole}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => togglePin(n.id)}
                  className={`rounded-lg p-1.5 transition-colors ${
                    n.pinned
                      ? "bg-cream-200 text-green-900"
                      : "text-ink-muted hover:bg-cream-100"
                  }`}
                  title={n.pinned ? "Unpin notice" : "Pin notice to top"}
                >
                  <Pin size={16} />
                </button>
                <button
                  onClick={() => deleteNotice(n.id)}
                  className="rounded-lg p-1.5 text-danger hover:bg-danger-bg"
                  title="Delete notice"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>

            <p className="text-sm text-ink leading-relaxed">{n.body}</p>

            <div className="flex items-center justify-between pt-2 text-xs text-ink-muted">
              <span>Author: <b className="text-ink">{n.author}</b></span>
              <span>{n.date}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Broadcast Notice Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-green-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-cream-300 bg-white p-6 shadow-2xl">
            <h3 className="font-heading text-lg font-bold text-green-900 border-b border-cream-200 pb-3">
              Broadcast University Announcement
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
                  className="h-10 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-green-900 mb-1">
                    Priority Level
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as any)}
                    className="h-10 w-full rounded-lg border border-cream-300 bg-white px-2 text-xs text-ink focus:border-green-700 focus:outline-none"
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
                    onChange={(e) => setNewTarget(e.target.value as any)}
                    className="h-10 w-full rounded-lg border border-cream-300 bg-white px-2 text-xs text-ink focus:border-green-700 focus:outline-none"
                  >
                    <option value="all">All University Members</option>
                    <option value="student">Students Only</option>
                    <option value="teacher">Teachers & Faculty Only</option>
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

              <label className="flex items-center gap-2 text-xs font-medium text-green-900 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPinned}
                  onChange={(e) => setIsPinned(e.target.checked)}
                  className="h-4 w-4 text-green-700 rounded focus:ring-green-700"
                />
                <span>Pin this notice to top of Notice Board</span>
              </label>

              <div className="flex justify-end gap-2 border-t border-cream-200 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Publish Notice
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
