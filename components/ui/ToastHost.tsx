"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, XCircle } from "lucide-react";
import { useToastStore } from "@/lib/store/toastStore";
import { cn } from "@/lib/utils";

const iconMap = { success: CheckCircle2, error: XCircle, info: Info };

export default function ToastHost() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  return (
    <div className="pointer-events-none fixed bottom-20 left-1/2 z-[90] flex w-full max-w-sm -translate-x-1/2 flex-col gap-2 px-4 md:bottom-6">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = iconMap[toast.variant ?? "info"];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 16, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25 }}
              onClick={() => dismiss(toast.id)}
              className={cn(
                "glass pointer-events-auto flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm font-medium shadow-card",
                toast.variant === "success" && "text-emerald-300",
                toast.variant === "error" && "text-rose-300",
                toast.variant === "info" && "text-white"
              )}
              role="status"
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{toast.message}</span>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
