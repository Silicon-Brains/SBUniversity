import { CommunityChat } from "@/components/features/CommunityChat";
import { getSession } from "@/lib/auth";

export const metadata = {
  title: "Community Chat",
};

export default async function CommunityChatPage() {
  const session = await getSession();
  return (
    <div className="min-w-0">
      <CommunityChat role={session?.role ?? "student"} />
    </div>
  );
}
