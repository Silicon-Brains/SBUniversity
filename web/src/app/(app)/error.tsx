"use client";
import { Button } from "@/components/ui/Button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="min-w-0 rounded-xl bg-danger-bg p-4 text-danger sm:p-6">
      <h2 className="text-lg font-semibold !text-danger">Something went wrong</h2>
      <p className="mt-1 break-words">We couldn&apos;t load this page. Try again in a moment.</p>
      <Button variant="danger" className="mt-4" onClick={reset}>Try again</Button>
    </div>
  );
}
