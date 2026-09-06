"use client";

import Link from "next/link";
import { Package, ChevronRight, FileText } from "lucide-react";
import { useUserStore } from "@/lib/store/userStore";
import { ORDER_STEPS } from "@/lib/api/mockApi";
import { formatINR, cn } from "@/lib/utils";

export default function OrdersPage() {
  const orders = useUserStore((s) => s.orders);

  if (orders.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-4 px-4 py-24 text-center">
        <Package className="h-14 w-14 text-white/20" />
        <h1 className="text-2xl font-bold text-white">NO ORDERS YET.</h1>
        <p className="text-sm text-white/50">Once you place an order, you can track it here.</p>
        <Link href="/products" className="focus-ring rounded-full bg-rush-gradient px-7 py-3 text-sm font-bold text-white shadow-glow-sm">
          SHOP NOW
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-6">
      <h1 className="mb-6 text-2xl font-extrabold tracking-tight text-white">Your Orders</h1>
      <div className="space-y-4">
        {orders.map((order) => {
          const statusLabel = ORDER_STEPS.find((s) => s.key === order.status)?.label ?? "Processing";
          const delivered = order.status === "delivered";
          return (
            <Link
              key={order.id}
              href={`/orders/${order.id}`}
              className="focus-ring flex items-center gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 transition hover:border-rush/40"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-rush-gradient/15">
                <FileText className="h-5 w-5 text-rush-cyan" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-white">#{order.id}</p>
                  <span className={cn("shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold", delivered ? "bg-emerald-500/15 text-emerald-400" : "bg-rush/15 text-rush-cyan")}>
                    {statusLabel}
                  </span>
                </div>
                <p className="truncate text-xs text-white/50">{order.items.map((i) => i.name).join(", ")}</p>
                <p className="mt-1 text-xs text-white/35">{new Date(order.createdAt).toLocaleString()} · {formatINR(order.total)}</p>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-white/30" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
