"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import clsx from "clsx";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  UserMinus,
  UserPlus,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import { api, ApiError, getDevAuthToken } from "@/lib/api";

/* ─── Types ─────────────────────────────────────────────────────────────── */
type UserRole = "student" | "teacher" | "admin";
type UserStatus = "active" | "suspended" | "deleted";

interface UserStats {
  total: number;
  students: number;
  teachers: number;
  admins: number;
}

interface ApiUser {
  id: string;
  clerk_user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  avatar_url?: string | null;
  created_at: string;
  student_profile?: {
    student_code: string;
    batch_year?: number | null;
    department?: { name: string } | null;
  } | null;
  teacher_profile?: {
    employee_code: string;
    designation?: string | null;
    department?: { name: string } | null;
  } | null;
}

interface PaginatedResponse {
  items: ApiUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/* ─── Confirmation Modal ─────────────────────────────────────────────────── */
interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  variant: "danger" | "primary";
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmModal({
  open,
  title,
  message,
  confirmLabel,
  variant,
  loading,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-3 sm:items-center sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-green-900/50 backdrop-blur-sm"
        onClick={onCancel}
      />
      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-action-title"
        className="relative my-auto max-h-[calc(100dvh-1.5rem)] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-4 shadow-2xl sm:max-h-[calc(100dvh-2rem)] sm:p-6"
      >
        <div className="mb-4 flex items-start gap-3">
          <span
            className={clsx(
              "mt-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-full",
              variant === "danger"
                ? "bg-danger-bg text-danger"
                : "bg-green-100 text-green-700"
            )}
          >
            {variant === "danger" ? (
              <AlertTriangle size={20} />
            ) : (
              <ShieldCheck size={20} />
            )}
          </span>
          <div>
            <h3 id="confirm-action-title" className="font-heading text-base font-bold text-green-900">
              {title}
            </h3>
            <p className="mt-1 text-sm text-ink-muted">{message}</p>
          </div>
        </div>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
          <Button variant="ghost" size="sm" className="w-full justify-center sm:w-auto" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={variant}
            size="sm"
            onClick={onConfirm}
            disabled={loading}
            className={clsx(
              "w-full justify-center sm:w-auto",
              variant === "primary" &&
                "bg-green-700 text-white hover:bg-green-800 border-transparent"
            )}
          >
            {loading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : null}
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Avatar initials ────────────────────────────────────────────────────── */
function Avatar({ name, url }: { name: string; url?: string | null }) {
  if (url) {
    return (
      <img
        src={url}
        alt={name}
        className="h-8 w-8 rounded-full object-cover ring-1 ring-cream-300"
      />
    );
  }
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-green-100 font-heading text-xs font-bold text-green-800 ring-1 ring-cream-300">
      {initials}
    </span>
  );
}

/* ─── Skeleton row ───────────────────────────────────────────────────────── */
function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {[200, 140, 80, 80, 80, 100].map((w, i) => (
        <td key={i} className="px-5 py-4">
          <div
            className="h-4 rounded bg-cream-200"
            style={{ width: w }}
          />
        </td>
      ))}
    </tr>
  );
}

/* ─── Role badge colour ──────────────────────────────────────────────────── */
const ROLE_TONE: Record<UserRole, "neutral" | "info" | "urgent"> = {
  student: "neutral",
  teacher: "info",
  admin: "urgent",
};

/* ─── Main component ─────────────────────────────────────────────────────── */
export function UsersTable({ initial }: { initial?: unknown }) {
  const { getToken } = useAuth();
  const toast = useToast();

  /* ── State ── */
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 12;

  const [q, setQ] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | UserRole>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ── Live stats state ── */
  const [stats, setStats] = useState<UserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      let token = await getToken();
      if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
        token = getDevAuthToken("admin");
      }
      const data = await api<UserStats>("/admin/users/stats", token ?? undefined);
      setStats(data);
    } catch {
      // keep previous stats if any
    } finally {
      setStatsLoading(false);
    }
  }, [getToken]);

  /* ── Confirm modal state ── */
  const [confirm, setConfirm] = useState<{
    open: boolean;
    title: string;
    message: string;
    confirmLabel: string;
    variant: "danger" | "primary";
    onConfirm: () => Promise<void>;
  }>({ open: false, title: "", message: "", confirmLabel: "", variant: "danger", onConfirm: async () => {} });
  const [confirmLoading, setConfirmLoading] = useState(false);

  /* ── Debounce search ── */
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedQ, setDebouncedQ] = useState("");
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedQ(q), 350);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [q]);

  /* ── Fetch users & live stats ── */
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let token = await getToken();
      if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
        token = getDevAuthToken("admin");
      }
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      });
      if (roleFilter !== "all") params.set("role", roleFilter);
      if (debouncedQ.trim()) params.set("search", debouncedQ.trim());

      const data = await api<PaginatedResponse>(
        `/admin/users?${params.toString()}`,
        token ?? undefined
      );
      setUsers(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to load users.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [getToken, page, roleFilter, debouncedQ]);

  useEffect(() => {
    fetchUsers();
    fetchStats();
  }, [fetchUsers, fetchStats]);

  /* Reset page when filter/search changes */
  useEffect(() => { setPage(1); }, [roleFilter, debouncedQ]);

  /* ── PATCH role ── */
  const handleRoleChange = (user: ApiUser, newRole: UserRole) => {
    if (newRole === user.role) return;
    setConfirm({
      open: true,
      title: `Change role to ${newRole}`,
      message: `Are you sure you want to change ${user.full_name}'s role from "${user.role}" to "${newRole}"? This affects their access immediately.`,
      confirmLabel: `Yes, make ${newRole}`,
      variant: newRole === "admin" ? "primary" : "danger",
      onConfirm: async () => {
        let token = await getToken();
        if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
          token = getDevAuthToken("admin");
        }
        await api(`/admin/users/${user.id}/role`, token ?? undefined, {
          method: "PATCH",
          body: JSON.stringify({ role: newRole }),
        });
        setUsers((prev) =>
          prev.map((u) => (u.id === user.id ? { ...u, role: newRole } : u))
        );
        fetchStats();
        toast(`✅ ${user.full_name} is now ${newRole}`);
      },
    });
  };

  /* ── PATCH status (suspend / reactivate) ── */
  const handleStatusToggle = (user: ApiUser) => {
    const isSuspending = user.status === "active";
    setConfirm({
      open: true,
      title: isSuspending ? `Suspend ${user.full_name}?` : `Reactivate ${user.full_name}?`,
      message: isSuspending
        ? `This will block ${user.full_name} from accessing the platform until reactivated.`
        : `This will restore full access for ${user.full_name}.`,
      confirmLabel: isSuspending ? "Yes, suspend" : "Yes, reactivate",
      variant: isSuspending ? "danger" : "primary",
      onConfirm: async () => {
        const newStatus: UserStatus = isSuspending ? "suspended" : "active";
        let token = await getToken();
        if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
          token = getDevAuthToken("admin");
        }
        await api(`/admin/users/${user.id}/status`, token ?? undefined, {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        });
        setUsers((prev) =>
          prev.map((u) => (u.id === user.id ? { ...u, status: newStatus } : u))
        );
        fetchStats();
        toast(
          isSuspending
            ? `🚫 ${user.full_name} has been suspended.`
            : `✅ ${user.full_name} has been reactivated.`
        );
      },
    });
  };

  const handleDeleteUser = (user: ApiUser) => {
    setConfirm({
      open: true,
      title: `Permanently delete ${user.full_name}?`,
      message: `This permanently deletes ${user.full_name}'s identity-provider account and database account, including their student-owned submissions and personal records. Authored course material is retained without its creator. This cannot be undone.`,
      confirmLabel: "Delete account permanently",
      variant: "danger",
      onConfirm: async () => {
        let token = await getToken();
        if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
          token = getDevAuthToken("admin");
        }
        await api(`/admin/users/${user.id}`, token ?? undefined, { method: "DELETE" });
        setUsers((previous) => previous.filter((item) => item.id !== user.id));
        setTotal((previous) => Math.max(0, previous - 1));
        setTotalPages(Math.max(1, Math.ceil((total - 1) / PAGE_SIZE)));
        if (users.length === 1 && page > 1) setPage((previous) => previous - 1);
        void fetchStats();
        toast(`Permanently deleted ${user.full_name}'s account.`);
      },
    });
  };

  /* ── Execute confirmed action ── */
  const handleConfirm = async () => {
    setConfirmLoading(true);
    try {
      await confirm.onConfirm();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Action failed. Please try again.";
      toast(`❌ ${msg}`);
    } finally {
      setConfirmLoading(false);
      setConfirm((c) => ({ ...c, open: false }));
    }
  };

  /* ── Department label ── */
  const getDept = (u: ApiUser) =>
    u.student_profile?.department?.name ??
    u.teacher_profile?.department?.name ??
    "—";

  const getCode = (u: ApiUser) =>
    u.student_profile?.student_code ?? u.teacher_profile?.employee_code ?? null;

  /* ─────────────────────────────────────────────────────────────────────── */
  return (
    <>
      <ConfirmModal
        open={confirm.open}
        title={confirm.title}
        message={confirm.message}
        confirmLabel={confirm.confirmLabel}
        variant={confirm.variant}
        loading={confirmLoading}
        onConfirm={handleConfirm}
        onCancel={() => setConfirm((c) => ({ ...c, open: false }))}
      />

      {/* ── Live KPI Stat Cards ── */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          value={stats ? stats.total : statsLoading ? "…" : "—"}
          label="Total users"
          hint="All registered accounts"
        />
        <StatCard
          value={stats ? stats.students : statsLoading ? "…" : "—"}
          label="Students"
          hint="Active learner accounts"
        />
        <StatCard
          value={stats ? stats.teachers : statsLoading ? "…" : "—"}
          label="Teachers"
          hint="Faculty & instructors"
        />
        <StatCard
          value={stats ? stats.admins : statsLoading ? "…" : "—"}
          label="Admins"
          hint="Platform administrators"
        />
      </div>

      <div className="space-y-4">
        {/* ── Controls ── */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative w-full sm:max-w-xs">
            <Search
              size={16}
              className="absolute inset-y-0 left-3 my-auto text-ink-placeholder"
            />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search name, email, code…"
              className="h-11 w-full rounded-lg border border-cream-300 bg-white pl-9 pr-9 text-sm text-ink placeholder:text-ink-placeholder focus:border-green-700 focus:outline-none"
            />
            {q && (
              <button
                onClick={() => setQ("")}
                className="absolute inset-y-0 right-1 my-auto grid h-10 w-10 place-items-center rounded text-ink-placeholder hover:text-ink"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Role filter pills */}
            {(["all", "student", "teacher", "admin"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRoleFilter(r)}
                className={clsx(
                  "min-h-11 rounded-lg px-3 text-xs font-semibold capitalize transition-colors",
                  roleFilter === r
                    ? "bg-green-700 text-cream-50 shadow-sm"
                    : "bg-white text-green-700 border border-cream-300 hover:bg-cream-100"
                )}
              >
                {r === "all" ? "All Roles" : `${r}s`}
              </button>
            ))}

            {/* Refresh */}
            <button
              onClick={() => {
                fetchUsers();
                fetchStats();
              }}
              disabled={loading || statsLoading}
              title="Refresh"
              className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-cream-300 bg-white text-green-700 hover:bg-cream-100 disabled:opacity-50"
            >
              <RefreshCw size={15} className={clsx((loading || statsLoading) && "animate-spin")} />
            </button>
          </div>
        </div>

        {/* ── Summary line ── */}
        {!loading && !error && (
          <p className="text-xs text-ink-muted">
            Showing{" "}
            <span className="font-semibold text-green-900">
              {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)}
            </span>{" "}
            of <span className="font-semibold text-green-900">{total}</span> users
          </p>
        )}

        {/* ── Error banner ── */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger">
            <AlertTriangle size={16} className="shrink-0" />
            <span>{error}</span>
            <button
              onClick={fetchUsers}
              className="ml-auto text-xs underline underline-offset-2 hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* ── Table ── */}
        <div className="hidden max-w-full overflow-x-auto rounded-xl border border-cream-300 bg-white shadow-sm md:block">
          <table className="w-full min-w-[780px] text-left text-sm">
            <thead className="bg-cream-100 text-xs font-semibold uppercase tracking-wide text-green-900">
              <tr>
                <th className="px-5 py-3.5">User</th>
                <th className="px-5 py-3.5">Department / Code</th>
                <th className="px-5 py-3.5">Role</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Joined</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cream-200">
              {loading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <SkeletonRow key={i} />
                  ))
                : users.map((u) => (
                    <tr
                      key={u.id}
                      className="group transition-colors hover:bg-cream-50/60"
                    >
                      {/* User cell */}
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <Avatar name={u.full_name} url={u.avatar_url} />
                          <div className="min-w-0">
                            <div className="truncate font-semibold text-green-900">
                              {u.full_name}
                            </div>
                            <div className="truncate text-xs text-ink-muted">
                              {u.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Dept / code */}
                      <td className="px-5 py-3.5">
                        <div className="text-xs text-ink">{getDept(u)}</div>
                        {getCode(u) && (
                          <div className="font-mono text-[11px] text-green-700">
                            {getCode(u)}
                          </div>
                        )}
                      </td>

                      {/* Role selector */}
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <Badge tone={ROLE_TONE[u.role]}>
                            {u.role}
                          </Badge>
                          <select
                            aria-label={`Change role for ${u.full_name}`}
                            value={u.role}
                            onChange={(e) =>
                              handleRoleChange(u, e.target.value as UserRole)
                            }
                            className="h-7 rounded border border-cream-300 bg-cream-50 px-1.5 text-xs font-medium text-green-900 capitalize focus:border-green-700 focus:outline-none cursor-pointer hover:border-green-400"
                          >
                            <option value="student">Student</option>
                            <option value="teacher">Teacher</option>
                            <option value="admin">Admin</option>
                          </select>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="px-5 py-3.5">
                        {u.status === "active" ? (
                          <Badge tone="success">Active</Badge>
                        ) : u.status === "suspended" ? (
                          <Badge tone="danger">Suspended</Badge>
                        ) : (
                          <Badge tone="neutral">Deleted</Badge>
                        )}
                      </td>

                      {/* Joined */}
                      <td className="px-5 py-3.5 text-xs text-ink-muted">
                        {new Date(u.created_at).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-3.5 text-right">
                        <div className="flex justify-end gap-2">
                          {u.status !== "deleted" && (
                            <Button
                              size="sm"
                              variant={u.status === "active" ? "danger" : "secondary"}
                              onClick={() => handleStatusToggle(u)}
                              className="gap-1.5"
                            >
                              {u.status === "active" ? (
                                <>
                                  <UserMinus size={13} aria-hidden />
                                  Suspend
                                </>
                              ) : (
                                <>
                                  <UserPlus size={13} aria-hidden />
                                  Reactivate
                                </>
                              )}
                            </Button>
                          )}
                          <Button size="sm" variant="danger" onClick={() => handleDeleteUser(u)} className="gap-1.5">
                            <Trash2 size={13} aria-hidden /> Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}

              {/* Empty state */}
              {!loading && !error && users.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-16 text-center">
                    <CheckCircle2
                      size={36}
                      className="mx-auto mb-3 text-cream-300"
                    />
                    <p className="text-sm font-medium text-ink-muted">
                      No users match your filters.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 md:hidden">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="animate-pulse rounded-xl border border-cream-300 bg-white p-4 shadow-sm"
              >
                <div className="h-4 w-2/3 rounded bg-cream-200" />
                <div className="mt-3 h-3 w-1/2 rounded bg-cream-200" />
                <div className="mt-4 h-10 rounded bg-cream-100" />
              </div>
            ))
          ) : users.length === 0 ? (
            !error && (
              <div className="rounded-xl border border-cream-300 bg-white px-4 py-10 text-center">
                <CheckCircle2 size={36} className="mx-auto mb-3 text-cream-300" />
                <p className="text-sm font-medium text-ink-muted">
                  No users match your filters.
                </p>
              </div>
            )
          ) : (
            users.map((u) => (
              <article
                key={u.id}
                className="min-w-0 rounded-xl border border-cream-300 bg-white p-4 shadow-sm"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <Avatar name={u.full_name} url={u.avatar_url} />
                  <div className="min-w-0 flex-1">
                    <p className="break-words font-semibold text-green-900">{u.full_name}</p>
                    <p className="break-all text-xs text-ink-muted">{u.email}</p>
                  </div>
                  {u.status === "active" ? (
                    <Badge tone="success">Active</Badge>
                  ) : u.status === "suspended" ? (
                    <Badge tone="danger">Suspended</Badge>
                  ) : (
                    <Badge tone="neutral">Deleted</Badge>
                  )}
                </div>

                <dl className="mt-4 grid grid-cols-2 gap-x-3 gap-y-3 border-t border-cream-200 pt-3 text-xs">
                  <div className="min-w-0">
                    <dt className="text-ink-muted">Department / Code</dt>
                    <dd className="mt-0.5 break-words font-medium text-ink">
                      {getDept(u)}
                      {getCode(u) && (
                        <span className="block break-all font-mono text-[11px] text-green-700">
                          {getCode(u)}
                        </span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">Joined</dt>
                    <dd className="mt-0.5 font-medium text-ink">
                      {new Date(u.created_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </dd>
                  </div>
                  <div className="col-span-2 flex flex-wrap items-center gap-2">
                    <dt className="text-ink-muted">Role</dt>
                    <dd className="flex flex-wrap items-center gap-2">
                      <Badge tone={ROLE_TONE[u.role]}>{u.role}</Badge>
                      <select
                        aria-label={`Change role for ${u.full_name}`}
                        value={u.role}
                        onChange={(e) => handleRoleChange(u, e.target.value as UserRole)}
                        className="min-h-11 rounded-lg border border-cream-300 bg-cream-50 px-3 text-xs font-medium capitalize text-green-900 focus:border-green-700 focus:outline-none"
                      >
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                      </select>
                    </dd>
                  </div>
                </dl>

                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {u.status !== "deleted" && (
                    <Button
                      size="sm"
                      variant={u.status === "active" ? "danger" : "secondary"}
                      onClick={() => handleStatusToggle(u)}
                      className="min-h-11 justify-center gap-1.5"
                    >
                      {u.status === "active" ? (
                        <>
                          <UserMinus size={14} aria-hidden />
                          Suspend
                        </>
                      ) : (
                        <>
                          <UserPlus size={14} aria-hidden />
                          Reactivate
                        </>
                      )}
                    </Button>
                  )}
                  <Button size="sm" variant="danger" onClick={() => handleDeleteUser(u)} className="min-h-11 justify-center gap-1.5">
                    <Trash2 size={14} aria-hidden /> Delete account
                  </Button>
                </div>
              </article>
            ))
          )}
        </div>

        {/* ── Pagination ── */}
        {totalPages > 1 && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-ink-muted">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="gap-1"
              >
                <ChevronLeft size={14} /> Prev
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || loading}
                className="gap-1"
              >
                Next <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
