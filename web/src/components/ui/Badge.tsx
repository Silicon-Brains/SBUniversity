import clsx from "clsx";
import { AlertTriangle, Check, Clock, X } from "lucide-react";
import type { ReactNode } from "react";

const tone = {
  neutral: "bg-cream-200 text-green-900",
  info: "bg-green-100 text-green-700",
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  urgent: "bg-bordo-50 text-bordo-700",
};
const icon = { success: Check, warning: Clock, danger: X, urgent: AlertTriangle } as const;

export function Badge({ tone: t = "neutral", children }: { tone?: keyof typeof tone; children: ReactNode }) {
  const Icon = icon[t as keyof typeof icon];
  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", tone[t])}>
      {Icon && <Icon size={12} aria-hidden />}{children}
    </span>
  );
}

export function PointsChip({ points, earned }: { points: number; earned?: boolean }) {
  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold", earned ? "bg-green-100 text-green-700" : "bg-cream-200 text-green-900")}>
      {earned && <Check size={12} aria-hidden />}+{points} pts
    </span>
  );
}
