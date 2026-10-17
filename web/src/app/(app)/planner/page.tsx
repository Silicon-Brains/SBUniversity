import { LearnPlanner } from "@/components/features/LearnPlanner";
import { getSession } from "@/lib/auth";

export const metadata = {
  title: "SB Learn Planner",
};

export default async function LearnPlannerPage() {
  const session = await getSession();
  return <LearnPlanner role={session?.role ?? "student"} />;
}
