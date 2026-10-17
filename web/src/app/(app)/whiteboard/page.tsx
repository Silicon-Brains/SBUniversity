import { LiveWhiteboard } from "@/components/features/LiveWhiteboard";
import { getSession } from "@/lib/auth";

export const metadata = {
  title: "Live Classroom",
};

export default async function LiveWhiteboardPage() {
  const session = await getSession();
  return <LiveWhiteboard role={session?.role ?? "student"} />;
}
