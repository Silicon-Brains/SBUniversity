"use client";
import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Plus,
  Clock,
  HelpCircle,
  Users,
  CheckCircle2,
  AlertCircle,
  Award,
  ChevronRight,
  MoreVertical,
} from "lucide-react";
import { PageHeader, Card, StatCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, PointsChip } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";

interface TeacherExam {
  id: string;
  title: string;
  courseTitle: string;
  status: "draft" | "published" | "closed";
  durationMinutes: number;
  questionCount: number;
  submissionsCount: number;
  avgScore: number;
  passRate: number;
  taskPoints: number;
  window: string;
}

const MOCK_TEACHER_EXAMS: TeacherExam[] = [
  {
    id: "ex-101",
    title: "Data Structures Midterm Examination",
    courseTitle: "Data Structures & Algorithms",
    status: "published",
    durationMinutes: 45,
    questionCount: 20,
    submissionsCount: 42,
    avgScore: 78.4,
    passRate: 85.7,
    taskPoints: 50,
    window: "Oct 18, 09:00 – Oct 20, 18:00",
  },
  {
    id: "ex-102",
    title: "Algorithms Unit Test 1 — Asymptotic Analysis",
    courseTitle: "Design & Analysis of Algorithms",
    status: "published",
    durationMinutes: 30,
    questionCount: 15,
    submissionsCount: 38,
    avgScore: 82.1,
    passRate: 92.1,
    taskPoints: 40,
    window: "Oct 26, 10:00 – Oct 27, 20:00",
  },
  {
    id: "ex-103",
    title: "Binary Trees & Graph Traversal Quiz",
    courseTitle: "Data Structures & Algorithms",
    status: "draft",
    durationMinutes: 25,
    questionCount: 10,
    submissionsCount: 0,
    avgScore: 0,
    passRate: 0,
    taskPoints: 30,
    window: "Nov 02, 09:00 – Nov 03, 17:00",
  },
];

export default function TeacherExamsPage() {
  const [examsList, setExamsList] = useState(MOCK_TEACHER_EXAMS);
  const toast = useToast();

  const handleCloseExam = (id: string) => {
    setExamsList((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: "closed" as const } : e))
    );
    toast("Exam closed to new student submissions.");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Manage Course Examinations"
        subtitle="Create, configure, and monitor timed MCQ exams with automated Task Points."
        action={
          <Button href="/teacher/exams/new" variant="primary" size="md">
            <Plus size={16} /> Create New Exam
          </Button>
        }
      />

      {/* KPI Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard value={examsList.length} label="Total Managed Exams" />
        <StatCard
          value={examsList.filter((e) => e.status === "published").length}
          label="Live Published Exams"
        />
        <StatCard
          value={examsList.reduce((acc, e) => acc + e.submissionsCount, 0)}
          label="Total Submissions Graded"
        />
        <StatCard value="88.9%" label="Average Faculty Pass Rate" />
      </div>

      {/* Exams List */}
      <div className="space-y-4">
        {examsList.map((exam) => (
          <Card key={exam.id} className="p-5 sm:p-6 transition-all hover:shadow-md">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-heading text-lg font-bold text-green-900">
                    {exam.title}
                  </h3>
                  {exam.status === "published" && (
                    <Badge tone="success">
                      <CheckCircle2 size={12} className="mr-1" /> Published
                    </Badge>
                  )}
                  {exam.status === "draft" && (
                    <Badge tone="warning">
                      <Clock size={12} className="mr-1" /> Draft Mode
                    </Badge>
                  )}
                  {exam.status === "closed" && (
                    <Badge tone="danger">
                      Closed
                    </Badge>
                  )}
                  <PointsChip points={exam.taskPoints} />
                </div>

                <p className="text-xs text-ink-muted">
                  Course: <b className="text-ink">{exam.courseTitle}</b> · Scheduled: {exam.window}
                </p>

                <div className="flex flex-wrap gap-4 pt-2 text-xs text-ink-muted">
                  <span className="inline-flex items-center gap-1.5">
                    <HelpCircle size={14} className="text-green-700" />
                    {exam.questionCount} Questions
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <Clock size={14} className="text-green-700" />
                    {exam.durationMinutes} Minutes
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <Users size={14} className="text-green-700" />
                    {exam.submissionsCount} Submissions
                  </span>
                  {exam.submissionsCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 font-semibold text-green-900">
                      Pass Rate: {exam.passRate}% (Avg: {exam.avgScore}%)
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2 sm:pt-0">
                {exam.status === "draft" && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setExamsList((l) =>
                        l.map((e) => (e.id === exam.id ? { ...e, status: "published" as const } : e))
                      );
                      toast(`Published ${exam.title} with +${exam.taskPoints} Task Points!`);
                    }}
                  >
                    Publish Now
                  </Button>
                )}

                {exam.status === "published" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleCloseExam(exam.id)}
                  >
                    Close Exam
                  </Button>
                )}

                <Button href={`/student/exams/1`} variant="secondary" size="sm">
                  Preview Runner
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
