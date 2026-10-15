"use client";
import React, { useState } from "react";
import { SignUp } from "@clerk/nextjs";
import { GraduationCap, Sparkles, Shield } from "lucide-react";
import Link from "next/link";
import { DemoLogin } from "@/components/features/DemoLogin";

export default function SignUpPage() {
  const [useDemoMode, setUseDemoMode] = useState(false);

  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-green-700 p-12 text-cream-100 lg:flex">
        <Link href="/" className="flex items-center gap-2 font-heading text-lg font-bold text-cream-50">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-cream-200 text-green-900">
            <GraduationCap size={20} aria-hidden />
          </span>
          SBUniversity
        </Link>
        <div>
          <h2 className="max-w-md font-heading text-3xl font-bold leading-snug !text-cream-50">
            Join the SBUniversity Academic Platform.
          </h2>
          <p className="mt-3 max-w-md text-cream-200">
            Create your account to take course examinations, earn Task Points, and collect verifiable credentials.
          </p>
        </div>
        <p className="text-sm text-cream-200">© 2026 SBUniversity</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md space-y-4">
          <div className="flex items-center justify-between border-b border-cream-200 pb-3">
            <div>
              <h1 className="text-2xl font-bold text-green-900">Create an account</h1>
              <p className="text-xs text-ink-muted">Sign up to get your university student credential.</p>
            </div>

            {/* Quick Mode Toggle for Local Testing */}
            <button
              type="button"
              onClick={() => setUseDemoMode(!useDemoMode)}
              className="rounded-lg border border-cream-300 bg-cream-100 px-2.5 py-1 text-xs font-semibold text-green-900 hover:bg-cream-200 transition-colors"
            >
              {useDemoMode ? "Use Clerk OAuth" : "1-Click Demo Accounts"}
            </button>
          </div>

          {useDemoMode ? (
            <div className="rounded-xl border border-cream-300 bg-white p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-green-700 bg-green-50 p-2 rounded-lg">
                <Sparkles size={14} className="text-bordo-700" />
                <span>One-Click Development Accounts (No Google OAuth required)</span>
              </div>
              <DemoLogin error={false} />
            </div>
          ) : (
            <div className="space-y-4">
              <SignUp
                routing="hash"
                signInUrl="/sign-in"
                fallbackRedirectUrl="/portal"
                appearance={{
                  variables: {
                    colorPrimary: "#6C151E",
                  },
                }}
              />

              {/* Troubleshooting hint for Brave Shields / Ad Blockers */}
              <div className="rounded-xl border border-cream-300 bg-cream-100/60 p-3.5 text-xs text-ink-muted space-y-2">
                <p className="font-semibold text-green-900 flex items-center gap-1.5">
                  <Shield size={13} className="text-green-700" />
                  Sign-up card stuck on a loading spinner?
                </p>
                <p>
                  If you are using <b>Brave Browser</b> or an <b>Ad Blocker / Privacy extension</b>, please disable Brave Shields or pause your ad blocker for <code>localhost</code> (Clerk&apos;s bot protection and cross-origin authentication scripts are blocked by default).
                </p>
                <p>
                  Alternatively, switch to <b>1-Click Demo Accounts</b> at the top right to start testing immediately, or visit{" "}
                  <Link href="/sign-in" className="font-bold text-green-700 underline">
                    Sign In
                  </Link>{" "}
                  if you already have an account.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
