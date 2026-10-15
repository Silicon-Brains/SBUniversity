import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { Shell } from "@/components/shell/Shell";
import { DEMO, getSession, ROLE_HOME, Role } from "@/lib/auth";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/sign-in");
  return <Shell role={session.role} name={session.name} demo={DEMO}>{children}</Shell>;
}
