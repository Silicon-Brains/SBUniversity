"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Award,
  BarChart3,
  Bot,
  CheckCircle2,
  Clock,
  FileCheck2,
  GraduationCap,
  IdCard,
  QrCode,
  Search,
  ShieldCheck,
  Sparkles,
  Trophy,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge, PointsChip } from "@/components/ui/Badge";

const features = [
  {
    icon: FileCheck2,
    title: "Timed Exams You Can Trust",
    text: "Server-authoritative timers and autosave keep every attempt tamper-proof and resilient, even on intermittent connectivity.",
  },
  {
    icon: Trophy,
    title: "Automated Live Ranking",
    text: "Earn Task Points automatically by passing exams and completing assignments. Live Top-4 podium updates the instant points are approved.",
  },
  {
    icon: Award,
    title: "Cryptographically Verified Certificates",
    text: "Every certificate features a unique permanent code and QR that employers or universities can verify instantly with zero login.",
  },
  {
    icon: IdCard,
    title: "Official Virtual Student ID",
    text: "Every learner receives a digital student credential complete with verified student code, department, and scan-ready QR code.",
  },
  {
    icon: Sparkles,
    title: "Aarsh Intelligence AI Tutor",
    text: "An academic study assistant powered by Gemini that clarifies difficult concepts, guided by strict anti-cheat proctoring rules.",
  },
  {
    icon: BarChart3,
    title: "Actionable Faculty & Admin Analytics",
    text: "Real-time insight into student progress, exam score distributions, submission queues, and course completion velocity.",
  },
];

const steps = [
  {
    step: "01",
    title: "Enroll & Sign In",
    desc: "Access your personalized portal with single sign-on via Clerk and obtain your official Virtual ID.",
  },
  {
    step: "02",
    title: "Master Course Exams & Tasks",
    desc: "Complete coursework, participate in timed MCQ assessments, and submit practical assignments for faculty review.",
  },
  {
    step: "03",
    title: "Climb Rankings & Earn Credentials",
    desc: "Accumulate Task Points, ascend the Live Top-4 podium, and automatically receive verified course completion certificates.",
  },
];

export default function Landing() {
  const [verifyCode, setVerifyCode] = useState("");
  const router = useRouter();

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    if (verifyCode.trim()) {
      router.push(`/verify/${encodeURIComponent(verifyCode.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-cream-50 text-ink">
      {/* Top Header */}
      <header className="sticky top-0 z-30 border-b border-cream-300 bg-cream-50/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5 font-heading text-lg font-bold text-green-700">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-green-700 text-cream-200 shadow-sm">
              <GraduationCap size={20} aria-hidden />
            </span>
            <span>SBUniversity</span>
          </Link>

          <div className="flex items-center gap-2.5">
            <Link
              href="/verify"
              className="hidden text-xs font-semibold text-green-700 hover:text-green-900 sm:inline-flex items-center gap-1"
            >
              <ShieldCheck size={14} /> Verify Credential
            </Link>
            <Button href="/sign-in" variant="secondary" size="sm">
              Sign In
            </Button>
            <Button href="/sign-up" variant="primary" size="sm">
              Sign Up
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-b from-cream-100 to-cream-50 pb-16 pt-12 lg:pt-20 lg:pb-24">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-12">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-cream-300 bg-white px-3.5 py-1 text-xs font-semibold text-green-900 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
                <span>Next-Generation Academic Platform · v2026</span>
              </div>

              <h1 className="font-heading text-4xl font-bold leading-tight text-green-900 sm:text-5xl lg:text-5xl">
                Learn, test, and achieve verified academic distinction.
              </h1>

              <p className="max-w-xl text-lg text-ink-muted leading-relaxed">
                SBUniversity unifies rigorous timed examinations, automated Task Point rankings, official verifiable credentials, and Gemini-powered AI tutoring into one cohesive learning portal.
              </p>

              <div className="flex flex-wrap items-center gap-3.5 pt-2">
                <Button href="/sign-up" variant="primary" size="lg">
                  Create Account (Sign Up)
                </Button>
                <Button href="/sign-in" variant="secondary" size="lg">
                  Portal Sign In
                </Button>
                <Button href="#verify-section" variant="ghost" size="lg">
                  Verify a Certificate
                </Button>
              </div>

              {/* Public Live Statistics Counter */}
              <div className="grid grid-cols-3 gap-4 border-t border-cream-300 pt-6">
                <div>
                  <p className="font-heading text-2xl font-bold text-green-700 sm:text-3xl">4,800+</p>
                  <p className="text-xs text-ink-muted">Enrolled Students</p>
                </div>
                <div>
                  <p className="font-heading text-2xl font-bold text-green-700 sm:text-3xl">98.4%</p>
                  <p className="text-xs text-ink-muted">Exam Completion</p>
                </div>
                <div>
                  <p className="font-heading text-2xl font-bold text-green-700 sm:text-3xl">100%</p>
                  <p className="text-xs text-ink-muted">Verifiable PDFs</p>
                </div>
              </div>
            </div>

            {/* Live Podium Preview Card */}
            <div className="lg:col-span-5">
              <div className="relative rounded-2xl border border-cream-300 bg-white p-6 shadow-xl">
                <div className="mb-4 flex items-center justify-between border-b border-cream-200 pb-3">
                  <div className="flex items-center gap-2">
                    <Trophy size={18} className="text-rank-gold" />
                    <h2 className="font-heading text-base font-bold text-green-900">
                      Top Performers Podium
                    </h2>
                  </div>
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-green-700">
                    <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
                    Live
                  </span>
                </div>

                <div className="space-y-3">
                  {[
                    { rank: 1, name: "Isha Patil", points: 520, badge: "Gold #1", medal: "bg-rank-gold" },
                    { rank: 2, name: "Kabir Nair", points: 455, badge: "Silver #2", medal: "bg-rank-silver" },
                    { rank: 3, name: "Sneha Joshi", points: 410, badge: "Bronze #3", medal: "bg-rank-bronze" },
                    { rank: 4, name: "Vikram Rao", points: 300, badge: "Honors #4", medal: "bg-green-700" },
                  ].map((s) => (
                    <div
                      key={s.name}
                      className="flex items-center gap-3.5 rounded-xl border border-cream-200 bg-cream-50/60 p-3 transition-colors hover:bg-cream-100/60"
                    >
                      <span className={`grid h-8 w-8 place-items-center rounded-full text-xs font-bold text-white ${s.medal}`}>
                        {s.rank}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-semibold text-sm text-green-900">{s.name}</p>
                        <p className="text-[11px] text-ink-muted">{s.badge}</p>
                      </div>
                      <span className="font-heading font-bold text-sm text-bordo-700">
                        +{s.points} pts
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 rounded-xl bg-green-50 p-3 text-center text-xs text-green-900">
                  <span>Task Points update automatically upon exam or task completion</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Public Credential Verification Section (PRD §7.2 requirement) */}
        <section id="verify-section" className="border-y border-cream-300 bg-cream-200 py-16">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-semibold text-green-900 shadow-sm mb-3">
              <ShieldCheck size={14} className="text-green-700" /> Tamper-Evident Verification
            </span>
            <h2 className="font-heading text-3xl font-bold text-green-900">
              Verify Any University Credential
            </h2>
            <p className="mx-auto mt-2 max-w-xl text-sm text-ink-muted">
              Validate the authenticity of any SBUniversity Course Certificate or Student ID Card issued by our registrar.
            </p>

            <form onSubmit={handleVerify} className="mx-auto mt-6 flex max-w-xl flex-col gap-2 sm:flex-row">
              <div className="relative flex-1">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-ink-placeholder">
                  <Search size={18} />
                </span>
                <input
                  type="text"
                  required
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value)}
                  placeholder="Enter Certificate Code (e.g. SBU-CERT-2026-PY01)"
                  className="h-12 w-full rounded-xl border border-cream-300 bg-white pl-11 pr-4 text-sm font-mono text-ink placeholder:text-ink-placeholder focus:border-green-700 focus:outline-none shadow-sm"
                />
              </div>
              <Button type="submit" variant="primary" size="lg">
                Verify Credential
              </Button>
            </form>
          </div>
        </section>

        {/* Features Grid */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="text-center">
            <h2 className="font-heading text-3xl font-bold text-green-900 sm:text-4xl">
              Engineered for Modern Academic Excellence
            </h2>
            <p className="mx-auto mt-2 max-w-2xl text-ink-muted text-sm sm:text-base">
              A single platform eliminating manual exam paper grading, forged certificates, and disconnected tools.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, text }) => (
              <Card key={title} className="flex flex-col p-6 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
                <span className="grid h-12 w-12 place-items-center rounded-xl bg-green-50 text-green-700 shadow-sm">
                  <Icon size={24} aria-hidden />
                </span>
                <h3 className="mt-4 font-heading text-lg font-bold text-green-900">{title}</h3>
                <p className="mt-2 text-sm text-ink-muted leading-relaxed">{text}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how" className="bg-green-700 text-cream-50 py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="text-center">
              <span className="text-xs uppercase font-bold tracking-widest text-cream-300">
                Seamless Learner Journey
              </span>
              <h2 className="mt-1 font-heading text-3xl font-bold !text-cream-50 sm:text-4xl">
                How SBUniversity Works
              </h2>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-3">
              {steps.map((s) => (
                <div key={s.step} className="rounded-2xl bg-green-600/90 p-6 border border-green-500/40 shadow-lg">
                  <span className="font-heading text-3xl font-bold text-cream-200">{s.step}</span>
                  <h3 className="mt-3 font-heading text-lg font-bold !text-cream-50">{s.title}</h3>
                  <p className="mt-2 text-sm text-cream-100/90 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>

            <div className="mt-12 flex flex-wrap justify-center gap-3.5">
              <Button
                href="/sign-up"
                className="border-cream-200 bg-cream-200 text-green-900 hover:bg-cream-100 font-bold"
                size="lg"
              >
                Create Student Account (Sign Up)
              </Button>
              <Button
                href="/sign-in"
                className="border border-cream-200 bg-transparent text-cream-50 hover:bg-green-600 font-bold"
                size="lg"
              >
                Portal Sign In
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-cream-300 bg-white py-10 text-xs text-ink-muted">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <span className="grid h-6 w-6 place-items-center rounded bg-green-700 text-cream-200 text-xs font-bold">
              SBU
            </span>
            <span className="font-semibold text-green-900">SBUniversity Academic Platform</span>
          </div>
          <div className="flex flex-wrap gap-6">
            <Link href="/verify" className="hover:underline">Verify Credential</Link>
            <Link href="/ranking" className="hover:underline">Live Leaderboard</Link>
            <Link href="/notices" className="hover:underline">University Notices</Link>
            <Link href="/sign-in" className="hover:underline">Sign In</Link>
            <Link href="/sign-up" className="font-semibold text-green-900 hover:underline">Sign Up</Link>
          </div>
          <p>© 2026 SBUniversity. Built to academic precision standards.</p>
        </div>
      </footer>
    </div>
  );
}
