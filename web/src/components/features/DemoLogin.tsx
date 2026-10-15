"use client";
import { useState } from "react";
import { demoSignIn } from "@/lib/actions";
import { Button } from "@/components/ui/Button";

const ACCOUNTS = [
  { role: "Student", name: "Aarav Sharma", email: "student@sbu.demo", password: "Student@123" },
  { role: "Teacher", name: "Dr. Meera Iyer", email: "teacher@sbu.demo", password: "Teacher@123" },
  { role: "Admin", name: "Rohan Desai", email: "admin@sbu.demo", password: "Admin@123" },
];
const field = "h-11 w-full rounded-lg border border-cream-300 bg-white px-3 text-base text-ink placeholder:text-ink-placeholder";

export function DemoLogin({ error }: { error: boolean }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  return (
    <form action={demoSignIn} className="space-y-4">
      <div>
        <p className="mb-2 text-sm font-medium text-green-900">Try a demo account</p>
        <div className="grid gap-2 sm:grid-cols-3">
          {ACCOUNTS.map((a) => (
            <button key={a.role} type="button" onClick={() => { setEmail(a.email); setPassword(a.password); }}
              className="rounded-lg border border-cream-300 bg-white p-3 text-left hover:bg-cream-100">
              <span className="block text-sm font-semibold text-green-700">{a.role}</span>
              <span className="block truncate text-xs text-ink-muted">{a.name}</span>
            </button>
          ))}
        </div>
      </div>
      <div>
        <label htmlFor="email" className="mb-1 block text-sm font-medium text-green-900">Email</label>
        <input id="email" name="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
      </div>
      <div>
        <label htmlFor="password" className="mb-1 block text-sm font-medium text-green-900">Password</label>
        <input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className={field} />
      </div>
      {error && <p role="alert" className="rounded-lg bg-danger-bg px-3 py-2 text-sm text-danger">Email or password is incorrect. Pick a demo account above to fill them in.</p>}
      <Button variant="primary" size="lg" className="w-full">Sign in</Button>
    </form>
  );
}
