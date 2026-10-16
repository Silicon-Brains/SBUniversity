import { redirect } from "next/navigation";
import { getSession, ROLE_HOME, DEMO } from "@/lib/auth";
import { getBaseUrl } from "@/lib/api";

/**
 * Smart portal entry — syncs user to backend database,
 * reads the Clerk role from metadata and redirects to the correct dashboard:
 *   admin   → /admin/users
 *   teacher → /teacher/dashboard
 *   student → /student/dashboard
 */
export default async function PortalPage() {
  const session = await getSession();
  if (!session) redirect("/sign-in");

  // Sync newly registered or logged-in user with backend database
  if (!DEMO) {
    try {
      const { auth } = await import("@clerk/nextjs/server");
      const { getToken } = await auth();
      const token = await getToken();
      if (token) {
        const baseUrl = getBaseUrl();
        await fetch(`${baseUrl}/me`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        }).catch(() => null);
      }
    } catch {
      // continue to dashboard
    }
  }

  redirect(ROLE_HOME[session.role]);
}
