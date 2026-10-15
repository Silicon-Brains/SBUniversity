"use client";
import { Button } from "@/components/ui/Button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="rounded-xl bg-danger-bg p-6 text-danger">
      <h2 className="text-lg font-semibold !text-danger">Something went wrong</h2>
      <p className="mt-1">We couldn&apos;t load this page. Try again in a moment.</p>
      <Button variant="danger" className="mt-4" onClick={reset}>Try again</Button>
    </div>
  );
}
