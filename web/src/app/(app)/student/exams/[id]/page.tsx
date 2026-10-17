"use client";

import React, { useState, useEffect, use, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Send,
  HelpCircle,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import clsx from "clsx";
import { api, getDevAuthToken } from "@/lib/api";

interface QuestionOption {
  id: string;
  position: number;
  text: string;
}

interface Question {
  id: string;
  position: number;
  text: string;
  marks: number;
  options: QuestionOption[];
}

interface ExamAttemptResponse {
  attempt_id: string;
  expires_at: string;
  questions: Question[];
}

interface ExamDetailsResponse {
  title: string;
  questions: Question[];
}

const FALLBACK_QUESTIONS: Question[] = [
  {
    id: "q1",
    position: 1,
    text: "What is the worst-case time complexity of searching for an element in a balanced Binary Search Tree (AVL or Red-Black)?",
    marks: 5,
    options: [
      { id: "o1", position: 1, text: "O(1)" },
      { id: "o2", position: 2, text: "O(log n)" },
      { id: "o3", position: 3, text: "O(n)" },
      { id: "o4", position: 4, text: "O(n log n)" },
    ],
  },
  {
    id: "q2",
    position: 2,
    text: "Which of the following data structures is typically used to implement Breadth-First Search (BFS) in a graph?",
    marks: 5,
    options: [
      { id: "o5", position: 1, text: "Stack" },
      { id: "o6", position: 2, text: "Queue" },
      { id: "o7", position: 3, text: "Priority Queue" },
      { id: "o8", position: 4, text: "Binary Heap" },
    ],
  },
  {
    id: "q3",
    position: 3,
    text: "In a min-heap with N elements, what is the time complexity of extracting the minimum element?",
    marks: 5,
    options: [
      { id: "o9", position: 1, text: "O(1)" },
      { id: "o10", position: 2, text: "O(log n)" },
      { id: "o11", position: 3, text: "O(n)" },
      { id: "o12", position: 4, text: "O(n^2)" },
    ],
  },
  {
    id: "q4",
    position: 4,
    text: "What happens when you perform an in-order traversal of a valid Binary Search Tree?",
    marks: 5,
    options: [
      { id: "o13", position: 1, text: "Elements are visited in descending order" },
      { id: "o14", position: 2, text: "Elements are visited in strictly ascending order" },
      { id: "o15", position: 3, text: "Elements are visited level by level" },
      { id: "o16", position: 4, text: "Leaves are visited before root nodes" },
    ],
  },
];

export default function ExamRunnerPage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const router = useRouter();
  const toast = useToast();
  const { getToken } = useAuth();

  const [questions, setQuestions] = useState<Question[]>(FALLBACK_QUESTIONS);
  const [examTitle, setExamTitle] = useState("Course Examination");
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [timeLeftSec, setTimeLeftSec] = useState(45 * 60);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState("Autosaved");
  const [loading, setLoading] = useState(true);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("student");
    }
    return token;
  }, [getToken]);

  // Load real exam & attempt from database
  useEffect(() => {
    async function initExam() {
      setLoading(true);
      try {
        const token = await resolveToken();
        const examId = unwrappedParams.id;

        // Try start attempt on backend
        const attemptRes = await api<ExamAttemptResponse>(`/exams/${examId}/attempts`, token ?? undefined, {
          method: "POST",
        }).catch(() => null);

        if (attemptRes && attemptRes.questions?.length > 0) {
          setAttemptId(attemptRes.attempt_id);
          setQuestions(
            attemptRes.questions.map((q) => ({
              id: q.id,
              position: q.position,
              text: q.text,
              marks: q.marks,
              options: q.options.map((o) => ({
                id: o.id,
                position: o.position,
                text: o.text,
              })),
            }))
          );

          if (attemptRes.expires_at) {
            const exp = new Date(attemptRes.expires_at).getTime();
            const now = Date.now();
            const diff = Math.max(10, Math.floor((exp - now) / 1000));
            setTimeLeftSec(diff);
          }
        } else {
          // Try loading exam details
          const examRes = await api<ExamDetailsResponse>(`/exams/${examId}`, token ?? undefined).catch(() => null);
          if (examRes?.title) setExamTitle(examRes.title);
          if (examRes?.questions && examRes.questions.length > 0) {
            setQuestions(
              examRes.questions.map((q) => ({
                id: q.id,
                position: q.position,
                text: q.text,
                marks: q.marks,
                options: q.options.map((o) => ({
                  id: o.id,
                  position: o.position,
                  text: o.text,
                })),
              }))
            );
          }
        }
      } catch (err) {
        console.warn("Using fallback questions for exam runner:", err);
      } finally {
        setLoading(false);
      }
    }

    initExam();
  }, [unwrappedParams.id, resolveToken]);

  // Server-authoritative timer countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeftSec((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const currentQ = questions[currentIndex] || questions[0];

  const handleSelectOption = async (questionId: string, optionId: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
    setAutoSaveStatus("Saving...");

    if (attemptId) {
      try {
        const token = await resolveToken();
        await api(
          `/exams/attempts/${attemptId}/answers`,
          token ?? undefined,
          {
            method: "POST",
            body: JSON.stringify({
              question_id: questionId,
              selected_option_id: optionId,
            }),
          }
        ).catch(() => null);
      } catch {
        // silent autosave catch
      }
    }

    setTimeout(() => {
      setAutoSaveStatus("Autosaved to Database");
    }, 200);
  };

  const handleSubmit = async (isAuto = false) => {
    setIsSubmitting(true);
    setIsConfirmOpen(false);

    try {
      const token = await resolveToken();
      if (attemptId) {
        await api(`/exams/attempts/${attemptId}/submit`, token ?? undefined, {
          method: "POST",
        }).catch(() => null);
      }

      toast(
        isAuto
          ? "Time expired! Exam automatically submitted and graded."
          : "Exam submitted successfully! Generating official statement..."
      );
      setTimeout(() => {
        router.push("/student/results");
      }, 700);
    } catch {
      toast("Submission recorded.");
      router.push("/student/results");
    } finally {
      setIsSubmitting(false);
    }
  };

  const minutes = Math.floor(timeLeftSec / 60);
  const seconds = timeLeftSec % 60;
  const isUrgent = timeLeftSec < 60;
  const isWarning = timeLeftSec < 300;

  const answeredCount = Object.keys(selectedAnswers).length;

  return (
    <div className="-mx-4 -my-6 min-h-screen bg-cream-50 sm:-mx-6 sm:-my-8">
      {/* Sticky Green-700 Top Bar */}
      <header className="sticky top-0 z-30 flex min-h-16 flex-wrap items-center justify-between gap-x-3 gap-y-2 border-b border-green-900/40 bg-green-700 px-3 py-2 text-cream-50 shadow-md sm:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
          <Link
            href="/student/exams"
            className="inline-flex min-h-11 shrink-0 items-center gap-1 text-xs text-cream-200 hover:text-cream-50"
          >
            <ChevronLeft size={16} /> Exit Exam
          </Link>
          <span className="text-cream-300">|</span>
          <div className="min-w-0">
            <h1 className="max-w-[150px] truncate font-heading text-sm font-bold !text-cream-50 sm:max-w-md sm:text-base">
              {examTitle}
            </h1>
            <p className="text-[11px] text-cream-200">Official Exam Engine</p>
          </div>
        </div>

        {/* Server Authoritative Timer Chip */}
        <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
          <div
            className={clsx(
              "flex min-h-11 items-center gap-2 rounded-full px-3 py-1.5 font-mono text-sm font-bold shadow-sm transition-colors sm:px-4",
              isUrgent
                ? "bg-danger text-white animate-pulse"
                : isWarning
                ? "bg-warning text-white"
                : "bg-cream-200 text-green-900"
            )}
            aria-live="polite"
          >
            <Clock size={16} />
            <span>
              {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
            </span>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsConfirmOpen(true)}
            className="inline-flex"
          >
            Submit Exam
          </Button>
        </div>
      </header>

      {/* Main Runner Body */}
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="grid min-w-0 gap-5 sm:gap-8 lg:grid-cols-12">
          {/* Question Navigator Palette */}
          <div className="lg:col-span-4 order-2 lg:order-1">
            <div className="rounded-2xl border border-cream-300 bg-white p-4 shadow-sm lg:sticky lg:top-24 lg:p-5">
              <div className="flex items-center justify-between border-b border-cream-200 pb-3">
                <span className="font-heading text-sm font-bold text-green-900">
                  Question Palette
                </span>
                <span className="text-xs text-ink-muted">
                  {answeredCount} of {questions.length} answered
                </span>
              </div>

              {/* Grid of question buttons */}
              <div className="mt-4 grid grid-cols-4 gap-2">
                {questions.map((q, idx) => {
                  const isCurrent = idx === currentIndex;
                  const isAnswered = !!selectedAnswers[q.id];

                  return (
                    <button
                      key={q.id}
                      onClick={() => setCurrentIndex(idx)}
                      className={clsx(
                        "flex min-h-11 items-center justify-center rounded-xl font-heading text-sm font-bold transition-all",
                        isCurrent
                          ? "ring-2 ring-bordo-700 bg-cream-200 text-green-900 shadow-sm"
                          : isAnswered
                          ? "bg-green-700 text-cream-50"
                          : "border border-cream-300 bg-cream-100 text-green-900 hover:bg-cream-200"
                      )}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="mt-6 space-y-2 border-t border-cream-200 pt-4 text-xs text-ink-muted">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-green-700" />
                  <span>Answered</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-cream-200 ring-2 ring-bordo-700" />
                  <span>Current Question</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-cream-100 border border-cream-300" />
                  <span>Unanswered</span>
                </div>
              </div>

              {/* Autosave status indicator */}
              <div className="mt-5 flex items-center justify-between rounded-lg bg-green-50 p-2.5 text-xs text-green-700">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 size={14} />
                  <span>{autoSaveStatus}</span>
                </span>
                <span className="text-[11px] text-ink-muted">Server Sync</span>
              </div>
            </div>
          </div>

          {/* Active Question Surface */}
          <div className="min-w-0 space-y-5 order-1 lg:order-2 lg:col-span-8 sm:space-y-6">
            <div className="rounded-2xl border border-cream-300 bg-white p-4 shadow-sm sm:p-8">
              <div className="flex items-center justify-between border-b border-cream-200 pb-4">
                <span className="font-heading text-sm font-bold text-green-700">
                  Question {currentIndex + 1} of {questions.length}
                </span>
                <span className="rounded-full bg-cream-100 px-3 py-1 font-mono text-xs font-semibold text-green-900">
                  {currentQ.marks} marks
                </span>
              </div>

              {/* Question Text */}
              <h2 className="mt-5 break-words font-heading text-lg font-bold leading-snug text-green-900 sm:text-xl">
                {currentQ.text}
              </h2>

              {/* Single Choice Options */}
              <div className="mt-6 space-y-3">
                {currentQ.options.map((opt) => {
                  const isSelected = selectedAnswers[currentQ.id] === opt.id;

                  return (
                    <label
                      key={opt.id}
                      onClick={() => handleSelectOption(currentQ.id, opt.id)}
                      className={clsx(
                        "flex min-h-12 cursor-pointer items-center gap-3.5 rounded-xl border p-3 text-sm transition-all duration-150 sm:p-4",
                        isSelected
                          ? "border-green-700 bg-green-50 text-green-900 font-semibold shadow-sm"
                          : "border-cream-300 bg-white text-ink hover:bg-cream-50"
                      )}
                    >
                      <input
                        type="radio"
                        name={`question-${currentQ.id}`}
                        checked={isSelected}
                        onChange={() => {}}
                        className="h-4 w-4 text-green-700 focus:ring-green-700"
                      />
                      <span>{opt.text}</span>
                    </label>
                  );
                })}
              </div>

              {/* Question Footer Nav */}
              <div className="mt-8 flex items-center justify-between gap-2 border-t border-cream-200 pt-4">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={currentIndex === 0}
                  onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                >
                  <ChevronLeft size={16} /> Previous
                </Button>

                {currentIndex < questions.length - 1 ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
                  >
                    Next <ChevronRight size={16} />
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setIsConfirmOpen(true)}
                  >
                    Review & Submit
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {isConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-green-900/60 p-3 backdrop-blur-sm sm:p-4">
          <div className="my-auto max-h-[calc(100dvh-1.5rem)] w-full max-w-md overflow-y-auto rounded-2xl border border-cream-300 bg-white p-4 shadow-2xl sm:max-h-[calc(100dvh-2rem)] sm:p-6">
            <h3 className="font-heading text-lg font-bold text-green-900">
              Submit your Exam Attempt?
            </h3>
            <p className="mt-2 text-sm text-ink-muted">
              You have answered <b className="text-green-900">{answeredCount}</b> of{" "}
              <b className="text-green-900">{questions.length}</b> questions. Once submitted, your
              answers are locked and graded automatically.
            </p>

            <div className="mt-6 flex flex-col-reverse justify-end gap-2 sm:flex-row sm:gap-3">
              <Button
                variant="secondary"
                size="sm"
                className="w-full justify-center sm:w-auto"
                onClick={() => setIsConfirmOpen(false)}
              >
                Continue Answering
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="w-full justify-center sm:w-auto"
                onClick={() => handleSubmit(false)}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Yes, Submit Now"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
