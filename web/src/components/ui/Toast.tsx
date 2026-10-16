"use client";
import { CheckCircle2 } from "lucide-react";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

const Ctx = createContext<(msg: string) => void>(() => {});
export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [msgs, setMsgs] = useState<{ id: number; text: string }[]>([]);
  const push = useCallback((text: string) => {
    const id = Date.now();
    setMsgs((m) => [...m, { id, text }]);
    setTimeout(() => setMsgs((m) => m.filter((x) => x.id !== id)), 4000);
  }, []);
  return (
    <Ctx.Provider value={push}>
      {children}
      <div aria-live="polite" className="fixed inset-x-3 top-[calc(env(safe-area-inset-top)+0.75rem)] z-50 flex flex-col items-end gap-2 sm:left-auto sm:w-80">
        {msgs.map((m) => (
          <div key={m.id} className="flex w-full min-w-0 items-center gap-2 rounded-lg border border-success bg-white px-4 py-3 text-sm shadow-md">
            <CheckCircle2 size={18} className="shrink-0 text-success" aria-hidden />
            <span className="min-w-0 break-words">{m.text}</span>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
