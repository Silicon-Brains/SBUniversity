"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import { BookOpen, Loader2, Plus, Users, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import { api, getDevAuthToken } from "@/lib/api";

interface AdminCourse {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  is_published: boolean;
  enrolled_students: number;
}

interface CreateCourseResponse extends AdminCourse {}

function defaultCourseCode() {
  return `OU-${new Date().getFullYear()}-01`;
}

export function AdminCourses() {
  const { getToken } = useAuth();
  const toast = useToast();
  const [courses, setCourses] = useState<AdminCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [code, setCode] = useState(defaultCourseCode);
  const [title, setTitle] = useState("OpenUniversity Course");
  const [description, setDescription] = useState("");
  const [enrollAll, setEnrollAll] = useState(true);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("admin");
    }
    return token;
  }, [getToken]);

  const loadCourses = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const token = await resolveToken();
      setCourses(await api<AdminCourse[]>("/admin/courses", token ?? undefined));
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load courses.");
    } finally {
      setLoading(false);
    }
  }, [resolveToken]);

  useEffect(() => {
    void loadCourses();
  }, [loadCourses]);

  async function createCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setLoadError(null);
    try {
      const token = await resolveToken();
      const created = await api<CreateCourseResponse>("/admin/courses", token ?? undefined, {
        method: "POST",
        body: JSON.stringify({
          code: code.trim(),
          title: title.trim(),
          description: description.trim() || undefined,
          is_published: true,
          enroll_all_active_students: enrollAll,
        }),
      });
      setCourses((current) => [created, ...current]);
      toast(
        `Created ${created.title} and enrolled ${created.enrolled_students} active student${created.enrolled_students === 1 ? "" : "s"}.`
      );
      setIsOpen(false);
      setCode(defaultCourseCode());
      setTitle("OpenUniversity Course");
      setDescription("");
      setEnrollAll(true);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to create course.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <>
      <div className="mb-6 flex justify-end">
        <Button variant="primary" className="w-full justify-center sm:w-auto" onClick={() => setIsOpen(true)}>
          <Plus size={16} /> Create OpenUniversity Course
        </Button>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-cream-300 bg-white">
          <Loader2 className="h-7 w-7 animate-spin text-green-700" />
        </div>
      ) : loadError && courses.length === 0 ? (
        <Card className="p-8 text-center">
          <p role="alert" className="text-sm text-danger">{loadError}</p>
          <Button variant="secondary" size="sm" className="mt-4" onClick={() => void loadCourses()}>
            Retry
          </Button>
        </Card>
      ) : courses.length === 0 ? (
        <Card className="p-10 text-center">
          <BookOpen className="mx-auto h-10 w-10 text-cream-400" />
          <h2 className="mt-3 font-heading text-lg font-bold text-green-900">No courses yet</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Create an OpenUniversity course and enroll all active students with one action.
          </p>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {courses.map((course) => (
            <Card key={course.id} className="min-w-0 p-4 sm:p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-bold uppercase tracking-wide text-green-700">{course.code}</p>
                  <h2 className="mt-1 break-words font-heading text-lg font-bold text-green-900">{course.title}</h2>
                </div>
                <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                  course.is_published ? "bg-green-100 text-green-800" : "bg-cream-200 text-ink-muted"
                }`}>
                  {course.is_published ? "Published" : "Draft"}
                </span>
              </div>
              {course.description && (
                <p className="mt-3 line-clamp-3 text-sm text-ink-muted">{course.description}</p>
              )}
              <div className="mt-5 flex min-w-0 items-start gap-2 border-t border-cream-200 pt-4 text-sm text-ink-muted">
                <Users size={16} className="text-green-700" />
                <span className="break-words">{course.enrolled_students} active student{course.enrolled_students === 1 ? "" : "s"} enrolled</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {loadError && courses.length > 0 && (
        <p role="alert" className="mt-4 text-sm text-danger">{loadError}</p>
      )}

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-3 sm:items-center sm:p-4">
          <button
            type="button"
            aria-label="Close course creator"
            className="absolute inset-0 bg-green-900/50 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-course-title"
            className="relative my-auto max-h-[calc(100dvh-1.5rem)] w-full max-w-xl overflow-y-auto rounded-2xl border border-cream-300 bg-white p-4 shadow-2xl sm:max-h-[calc(100dvh-2rem)] sm:p-6"
          >
            <div className="mb-5 flex items-start justify-between border-b border-cream-200 pb-3">
              <div>
                <h2 id="create-course-title" className="font-heading text-xl font-bold text-green-900">
                  Create OpenUniversity Course
                </h2>
                <p className="mt-1 text-sm text-ink-muted">
                  The course is published and available to its enrolled students.
                </p>
              </div>
              <button
                type="button"
                aria-label="Close"
                onClick={() => setIsOpen(false)}
                className="grid min-h-11 min-w-11 shrink-0 place-items-center rounded-lg text-ink-muted hover:bg-cream-100"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={createCourse} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-green-900">
                  Course code
                  <input
                    required
                    minLength={2}
                    maxLength={50}
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    className="mt-1 h-10 w-full rounded-lg border border-cream-300 px-3 text-sm font-normal text-ink"
                  />
                </label>
                <label className="block text-sm font-semibold text-green-900">
                  Course name
                  <input
                    required
                    minLength={2}
                    maxLength={200}
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    className="mt-1 h-10 w-full rounded-lg border border-cream-300 px-3 text-sm font-normal text-ink"
                  />
                </label>
              </div>
              <label className="block text-sm font-semibold text-green-900">
                Description (optional)
                <textarea
                  rows={3}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-cream-300 p-3 text-sm font-normal text-ink"
                  placeholder="Describe this course"
                />
              </label>
              <label className="flex items-start gap-3 rounded-xl border border-cream-300 p-4 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={enrollAll}
                  onChange={(event) => setEnrollAll(event.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  <span className="block font-semibold text-green-900">Enroll all active students</span>
                  <span className="mt-1 block text-xs text-ink-muted">
                    Selected by default. Every active student in the database will be enrolled when this course is created.
                  </span>
                </span>
              </label>
              {loadError && <p role="alert" className="text-sm text-danger">{loadError}</p>}
              <div className="flex flex-col-reverse gap-2 border-t border-cream-200 pt-4 sm:flex-row sm:justify-end sm:gap-3">
                <Button type="button" variant="secondary" size="sm" className="w-full justify-center sm:w-auto" onClick={() => setIsOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" className="w-full justify-center sm:w-auto" disabled={isSaving}>
                  {isSaving ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
                  Create and enroll
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
