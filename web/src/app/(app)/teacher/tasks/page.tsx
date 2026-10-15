import { PageHeader } from "@/components/ui/Card";
import { ApprovalQueue } from "@/components/features/ApprovalQueue";

export const metadata = { title: "Task Approvals – SBUniversity Faculty" };

export default function TeacherTasks() {
  return (
    <>
      <PageHeader
        title="Student Task Approvals"
        subtitle="Review and approve student lab assignment submissions to award live Task Points."
        action={
          <span className="flex items-center gap-2 text-sm text-ink-muted">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-success" />
            Live Sync
          </span>
        }
      />
      <ApprovalQueue />
    </>
  );
}
