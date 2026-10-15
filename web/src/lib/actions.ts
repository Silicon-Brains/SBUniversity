"use server";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { DEMO_COOKIE, DEMO_USERS, ROLE_HOME, type Role } from "./auth";

export async function demoSignIn(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const password = String(formData.get("password") ?? "");
  const role = (Object.keys(DEMO_USERS) as Role[]).find(
    (r) => DEMO_USERS[r].email === email && DEMO_USERS[r].password === password,
  );
  if (!role) redirect("/sign-in?error=1");
  (await cookies()).set(DEMO_COOKIE, role, { httpOnly: true, sameSite: "lax", path: "/", maxAge: 60 * 60 * 8 });
  redirect(ROLE_HOME[role]);
}

export async function demoSignOut() {
  (await cookies()).delete(DEMO_COOKIE);
  redirect("/");
}
