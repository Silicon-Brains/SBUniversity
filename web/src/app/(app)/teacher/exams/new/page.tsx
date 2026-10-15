"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, Trash2, CheckCircle2, AlertCircle, Clock, Sparkles } from "lucide-react";
import { PageHeader, Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

interface OptionDraft {
  text: string;
  isCorrect: boolean;
}

interface QuestionDraft {
  text: string;
  marks: number;
  options: OptionDraft[];
  explanation: string;
}

export default function NewExamPage() {
  const router = useRouter();
  const toast = useToast();

  const [course, setCourse] = useState("Data Structures & Algorithms");
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("Attempt all questions. Server timer runs continuously.");
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [passMarks, setPassMarks] = useState(10);
  const [taskPoints, setTaskPoints] = useState(50);
  const [negativeMarking, setNegativeMarking] = useState(0);

  const [questions, setQuestions] = useState<QuestionDraft[]>([
    {
      text: "What is the worst-case time complexity of QuickSort when the pivot is chosen poorly?",
      marks: 5,
      explanation: "Worst case occurs with already sorted arrays and naive pivot choice: O(n^2).",
      options: [
        { text: "O(n log n)", isCorrect: false },
        { text: "O(n^2)", isCorrect: true },
        { text: "O(log n)", isCorrect: false },
        { text: "O(n)", isCorrect: false },
      ],
    },
    {
      text: "Which traversal of a Binary Search Tree produces values in strictly sorted order?",
      marks: 5,
      explanation: "In-order traversal visits Left, Root, Right, producing sorted elements.",
      options: [
        { text: "Pre-order Traversal", isCorrect: false },
        { text: "Post-order Traversal", isCorrect: false },
        { text: "In-order Traversal", isCorrect: true },
        { text: "Level-order Traversal", isCorrect: false },
      ],
    },
  ]);

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      {
        text: "",
        marks: 5,
        explanation: "",
        options: [
          { text: "", isCorrect: true },
          { text: "", isCorrect: false },
          { text: "", isCorrect: false },
          { text: "", isCorrect: false },
        ],
      },
    ]);
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, i) => i !== index));
  };

  const updateQuestionText = (index: number, text: string) => {
    setQuestions((prev) =>
      prev.map((q, i) => (i === index ? { ...q, text } : q))
    );
  };

  const updateOptionText = (qIndex: number, optIndex: number, text: string) => {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qIndex
          ? {
              ...q,
              options: q.options.map((opt, oi) => (oi === optIndex ? { ...opt, text } : opt)),
            }
          : q
      )
    );
  };

  const setCorrectOption = (qIndex: number, optIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qIndex
          ? {
              ...q,
              options: q.options.map((opt, oi) => ({
                ...opt,
                isCorrect: oi === optIndex,
              })),
            }
          : q
      )
    );
  };

  const handleSubmit = (publishImmediately: boolean) => {
    if (!title.trim()) {
      toast("Please enter an exam title.");
      return;
    }
    toast(
      publishImmediately
        ? `Exam "${title}" published with +${taskPoints} Task Points!`
        : `Exam draft "${title}" saved successfully.`
    );
    setTimeout(() => {
      router.push("/teacher/exams");
    }, 600);
  };

  const totalCalculatedMarks = questions.reduce((sum, q) => sum + (Number(q.marks) || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button href="/teacher/exams" variant="secondary" size="sm">
          <ArrowLeft size={14} /> Back to Exams
        </Button>
      </div>

      <PageHeader
        title="Create New Examination"
        subtitle="Configure exam details, duration, question bank, and linked Task Points."
      />

      <div className="grid gap-8 lg:grid-cols-12 lg:items-start">
        {/* Left Form: Exam Configuration */}
        <div className="space-y-6 lg:col-span-8">
          <Card className="p-6 space-y-4">
            <h3 className="font-heading text-lg font-bold text-green-900 border-b border-cream-200 pb-3">
              1. Basic Information & Parameters
            </h3>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Exam Title
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Advanced Graph Algorithms Midterm"
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Select Course
                </label>
                <select
                  value={course}
                  onChange={(e) => setCourse(e.target.value)}
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                >
                  <option>Data Structures & Algorithms</option>
                  <option>Design & Analysis of Algorithms</option>
                  <option>Python Programming Fundamentals</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Duration (Minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="180"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Pass Marks
                </label>
                <input
                  type="number"
                  min="0"
                  value={passMarks}
                  onChange={(e) => setPassMarks(Number(e.target.value))}
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Task Points Awarded on Passing
                </label>
                <input
                  type="number"
                  min="0"
                  value={taskPoints}
                  onChange={(e) => setTaskPoints(Number(e.target.value))}
                  className="h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm font-bold text-bordo-700 focus:border-green-700 focus:outline-none"
                />
                <span className="text-[11px] text-ink-muted">Earned automatically when student passes</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-green-900 mb-1">
                Candidate Instructions
              </label>
              <textarea
                rows={2}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="w-full rounded-lg border border-cream-300 bg-white p-3 text-sm text-ink focus:border-green-700 focus:outline-none"
              />
            </div>
          </Card>

          {/* Question Bank Builder */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-heading text-lg font-bold text-green-900">
                  2. Question Bank ({questions.length} Questions)
                </h3>
                <p className="text-xs text-ink-muted">Single choice MCQ with automated evaluation</p>
              </div>
              <Button type="button" variant="secondary" size="sm" onClick={addQuestion}>
                <Plus size={15} /> Add Question
              </Button>
            </div>

            {questions.map((q, qIndex) => (
              <Card key={qIndex} className="p-5 space-y-4 border-l-4 border-l-green-700">
                <div className="flex items-center justify-between border-b border-cream-200 pb-2">
                  <span className="font-heading text-sm font-bold text-green-900">
                    Question #{qIndex + 1}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-ink-muted">Marks: 5.0</span>
                    {questions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeQuestion(qIndex)}
                        className="text-danger hover:text-danger/80"
                        title="Remove Question"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-ink-muted mb-1">
                    Question Prompt
                  </label>
                  <textarea
                    rows={2}
                    value={q.text}
                    onChange={(e) => updateQuestionText(qIndex, e.target.value)}
                    placeholder="Enter the question text here..."
                    className="w-full rounded-lg border border-cream-300 bg-white p-2.5 text-sm text-ink focus:border-green-700 focus:outline-none"
                  />
                </div>

                {/* Options */}
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-green-900">
                    Options (Select radio for single correct answer):
                  </label>
                  {q.options.map((opt, optIndex) => (
                    <div key={optIndex} className="flex items-center gap-2.5">
                      <input
                        type="radio"
                        name={`correct-${qIndex}`}
                        checked={opt.isCorrect}
                        onChange={() => setCorrectOption(qIndex, optIndex)}
                        className="h-4 w-4 text-green-700 focus:ring-green-700 cursor-pointer"
                        title="Mark as correct answer"
                      />
                      <input
                        type="text"
                        value={opt.text}
                        onChange={(e) => updateOptionText(qIndex, optIndex, e.target.value)}
                        placeholder={`Option ${optIndex + 1}`}
                        className={`h-9 flex-1 rounded-lg border px-3 text-xs focus:outline-none ${
                          opt.isCorrect
                            ? "border-green-700 bg-green-50 font-semibold text-green-900"
                            : "border-cream-300 bg-white text-ink"
                        }`}
                      />
                      {opt.isCorrect && (
                        <span className="text-[11px] font-bold text-success flex items-center gap-1">
                          <CheckCircle2 size={13} /> Correct
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Right Sticky Sidebar: Summary & Publish Actions */}
        <div className="space-y-6 lg:col-span-4">
          <Card className="sticky top-24 p-5 space-y-4">
            <h4 className="font-heading text-base font-bold text-green-900 border-b border-cream-200 pb-2">
              Exam Summary
            </h4>

            <div className="space-y-2 text-xs text-ink-muted">
              <div className="flex justify-between">
                <span>Total Questions:</span>
                <span className="font-bold text-ink">{questions.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Total Marks:</span>
                <span className="font-bold text-ink">{totalCalculatedMarks}</span>
              </div>
              <div className="flex justify-between">
                <span>Pass Marks:</span>
                <span className="font-bold text-ink">{passMarks}</span>
              </div>
              <div className="flex justify-between">
                <span>Duration:</span>
                <span className="font-bold text-ink">{durationMinutes} mins</span>
              </div>
              <div className="flex justify-between border-t border-cream-200 pt-2">
                <span>Linked Task Points:</span>
                <span className="font-bold text-bordo-700">+{taskPoints} pts</span>
              </div>
            </div>

            <div className="border-t border-cream-200 pt-3 space-y-2">
              <Button
                type="button"
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => handleSubmit(true)}
              >
                Publish Exam Now
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="md"
                className="w-full"
                onClick={() => handleSubmit(false)}
              >
                Save as Draft
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
