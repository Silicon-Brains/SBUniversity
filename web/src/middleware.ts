import { NextResponse, type NextRequest } from "next/server";
import { clerkMiddleware } from "@clerk/nextjs/server";

type Role = "student" | "teacher" | "admin";
const HOME: Record<Role, string> = {
  student: "/student/dashboard",
  teacher: "/teacher/dashboard",
  admin: "/admin/users",
};
const SCOPED: Role[] = ["student", "teacher", "admin"];
const SHARED = ["/ranking", "/notices", "/assistant"];

/**
 * Returns a redirect response when the visitor should not view `path`.
 *
 * @param role  - Role from JWT claims. `undefined` means authenticated but
 *                no role in the JWT yet (page-level guard will handle it).
 *                `null` means not signed in at all.
 */
function decide(req: NextRequest, role: Role | null | undefined) {
  const path = req.nextUrl.pathname;
  const scope = SCOPED.find(
    (r) => path === `/${r}` || path.startsWith(`/${r}/`),
  );
  const isShared = SHARED.some((p) => path.startsWith(p));

  // Not a protected path — let it through
  if (!scope && !isShared) return null;

  // Not authenticated at all → sign-in
  if (role === null) return NextResponse.redirect(new URL("/sign-in", req.url));

  // Authenticated but JWT has no role yet → let through; page guard handles it
  if (role === undefined) return null;

  // Authenticated with a role, but in the wrong scope → redirect to their home
  if (scope && scope !== role)
    return NextResponse.redirect(new URL(HOME[role], req.url));

  return null;
}

function nextWithHeaders(req: NextRequest) {
  const requestHeaders = new Headers(req.headers);
  requestHeaders.set("x-pathname", req.nextUrl.pathname);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

// Demo mode: role comes from a cookie
const demoMiddleware = (req: NextRequest) =>
  decide(req, req.cookies.get("sbu_demo")?.value as Role | undefined) ??
  nextWithHeaders(req);

// Production mode: role comes from Clerk JWT claims
const prodMiddleware = clerkMiddleware(async (auth, req) => {
  const { sessionClaims } = await auth();
  const claims = sessionClaims as Record<string, unknown> | undefined;

  // Not signed in
  if (!claims) return decide(req, null) ?? nextWithHeaders(req);

  // Read role only from JWT — never assume "student" as fallback.
  // If role isn't in the JWT, it stays `undefined` and the page component
  // (which calls currentUser()) will do the authoritative role check.
  const metadata = (
    claims?.metadata ?? claims?.publicMetadata ?? claims?.public_metadata
  ) as Record<string, unknown> | undefined;
  const role: Role | undefined =
    (metadata?.role as Role | undefined) ??
    (claims?.role as Role | undefined) ??
    undefined;

  return decide(req, role) ?? nextWithHeaders(req);
});

export default process.env.NEXT_PUBLIC_DEMO_MODE === "true"
  ? demoMiddleware
  : prodMiddleware;

export const config = { matcher: ["/((?!_next|.*\\..*).*)" ] };
