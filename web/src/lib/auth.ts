import { cookies } from "next/headers";

export type Role = "student" | "teacher" | "admin";
export const DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
export const DEMO_COOKIE = "sbu_demo";

export const DEMO_USERS: Record<Role, { name: string; email: string; password: string }> = {
  student: { name: "Aarav Sharma", email: "student@sbu.demo", password: "Student@123" },
  teacher: { name: "Dr. Meera Iyer", email: "teacher@sbu.demo", password: "Teacher@123" },
  admin: { name: "Rohan Desai", email: "admin@sbu.demo", password: "Admin@123" },
};

export const ROLE_HOME: Record<Role, string> = {
  student: "/student/dashboard",
  teacher: "/teacher/dashboard",
  admin: "/admin/users",
};

export interface Session { role: Role; name: string }

/** Server-side session. Role comes from the verified Clerk claim (or demo cookie) — never from the client. */
export async function getSession(): Promise<Session | null> {
  if (DEMO) {
    const role = (await cookies()).get(DEMO_COOKIE)?.value as Role | undefined;
    return role && role in DEMO_USERS ? { role, name: DEMO_USERS[role].name } : null;
  }
  const { currentUser } = await import("@clerk/nextjs/server");
  const user = await currentUser();
  if (!user) return null;
  const rawRole =
    (user.publicMetadata?.role as Role | undefined) ??
    (user.privateMetadata?.role as Role | undefined) ??
    (user.unsafeMetadata?.role as Role | undefined) ??
    "student";
  return { role: rawRole, name: user.fullName ?? user.firstName ?? "User" };
}
