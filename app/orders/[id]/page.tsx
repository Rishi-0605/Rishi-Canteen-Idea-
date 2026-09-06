"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useParams } from "next/navigation";
import { Check, Circle, MapPin, Phone, MessageCircle, Store, Home as HomeIcon, Bike, PackageSearch } from "lucide-react";
import { useUserStore } from "@/lib/store/userStore";
import { ORDER_STEPS, nextOrderStatus } from "@/lib/api/mockApi";
import { formatINR, cn } from "@/lib/utils";
import { useToastStore } from "@/lib/store/toastStore";
import { TrackingSkeleton } from "@/components/ui/Skeletons";

export default function OrderTrackingPage() {
  const params = useParams<{ id: string }>();
  const orders = useUserStore((s) => s.orders);
  const updateStatus = useUserStore((s) => s.updateOrderStatus);
  const push = useToastStore((s) => s.push);
  const [loading, setLoading] = useState(true);
  const [minutesLeft, setMinutesLeft] = useState<number | null>(null);

  const order = orders.find((o) => o.id === params.id);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (order) setMinutesLeft(order.etaMinutes);
  }, [order?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!order || order.status === "delivered") return;
    const interval = setInterval(() => {
      setMinutesLeft((m) => (m !== null && m > 0 ? m - 1 : 0));
      updateStatus(order.id, nextOrderStatus(order.status));
    }, 3000);
    return () => clearInterval(interval);
  }, [order?.id, order?.status, updateStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const currentIdx = order ? ORDER_STEPS.findIndex((s) => s.key === order.status) : 0;
  const progressPct = useMemo(() => (currentIdx / (ORDER_STEPS.length - 1)) * 100, [currentIdx]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 md:px-6">
        <TrackingSkeleton />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <PackageSearch className="mx-auto mb-4 h-12 w-12 text-white/20" />
        <h1 className="text-xl font-bold text-white">Order not found</h1>
        <p className="mt-2 text-sm text-white/50">We couldn&apos;t find this order in your account.</p>
        <Link href="/orders" className="focus-ring mt-5 inline-block rounded-full bg-rush-gradient px-6 py-3 text-sm font-bold text-white">
          View all orders
        </Link>
      </div>
    );
  }

  const delivered = order.status === "delivered";

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-extrabold text-white">Order #{order.id}</h1>
          <p className="text-sm text-white/50">{order.items.map((i) => i.name).join(", ")}</p>
        </div>
        <span className={cn("rounded-full px-3 py-1 text-xs font-semibold", delivered ? "bg-emerald-500/15 text-emerald-400" : "bg-rush/15 text-rush-cyan")}>
          {delivered ? "Delivered" : "In progress"}
        </span>
      </div>

      {/* Mock map */}
      <div className="relative mb-8 h-56 overflow-hidden rounded-2xl border border-white/10 bg-navy-800/60">
        <div className="absolute inset-0 [background-image:linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] [background-size:24px_24px]" />
        <div className="absolute left-[10%] top-1/2 -translate-y-1/2 flex flex-col items-center gap-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-rush/40 bg-navy-900 shadow-glow-sm">
            <Store className="h-4 w-4 text-rush-cyan" />
          </div>
          <span className="text-[10px] text-white/50">{order.retailer.name}</span>
        </div>
        <div className="absolute right-[10%] top-1/2 -translate-y-1/2 flex flex-col items-center gap-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-emerald-400/40 bg-navy-900 shadow-glow-sm">
            <HomeIcon className="h-4 w-4 text-emerald-400" />
          </div>
          <span className="text-[10px] text-white/50">Your location</span>
        </div>
        <div className="absolute left-[10%] right-[10%] top-1/2 h-[2px] -translate-y-1/2 bg-white/10" />
        <motion.div
          className="absolute top-1/2 flex -translate-y-1/2 flex-col items-center gap-1"
          animate={{ left: `${10 + progressPct * 0.8}%` }}
          transition={{ duration: 1, ease: "easeInOut" }}
          style={{ left: "10%" }}
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-rush-gradient shadow-glow">
            <Bike className="h-4 w-4 text-white" />
          </div>
        </motion.div>
      </div>

      {!delivered && minutesLeft !== null && (
        <div className="mb-8 flex items-center justify-between rounded-2xl border border-rush/30 bg-rush/10 p-4">
          <div>
            <p className="text-xs text-white/50">Estimated arrival</p>
            <p className="text-2xl font-extrabold text-white">{minutesLeft} MIN</p>
          </div>
          <MapPin className="h-6 w-6 text-rush-cyan" />
        </div>
      )}

      {/* Timeline */}
      <div className="mb-8 space-y-5">
        {ORDER_STEPS.map((step, i) => {
          const done = i <= currentIdx;
          const active = i === currentIdx && !delivered;
          return (
            <div key={step.key} className="flex items-center gap-3">
              <motion.div
                animate={active ? { scale: [1, 1.2, 1] } : {}}
                transition={{ repeat: active ? Infinity : 0, duration: 1.4 }}
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border",
                  done ? "border-emerald-400 bg-emerald-400/20 text-emerald-400" : "border-white/20 text-white/20"
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : <Circle className="h-2 w-2 fill-current" />}
              </motion.div>
              <span className={cn("text-sm", done ? "font-medium text-white" : "text-white/40")}>{step.label}</span>
            </div>
          );
        })}
      </div>

      <div className="mb-8 flex flex-col gap-3 sm:flex-row">
        <button
          onClick={() => push("Connecting you to the delivery partner…", "info")}
          className="focus-ring flex flex-1 items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 py-3 text-sm font-semibold text-white hover:border-rush-cyan/40"
        >
          <Phone className="h-4 w-4" /> Call delivery partner
        </button>
        <Link
          href="/support"
          className="focus-ring flex flex-1 items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 py-3 text-sm font-semibold text-white hover:border-rush-cyan/40"
        >
          <MessageCircle className="h-4 w-4" /> Contact support
        </Link>
      </div>

      <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-white/50">Order Summary</h2>
        <div className="space-y-2 text-sm">
          {order.items.map((item) => (
            <div key={item.productId} className="flex justify-between text-white/70">
              <span>{item.name} × {item.quantity}</span>
              <span>{formatINR(item.price * item.quantity)}</span>
            </div>
          ))}
          <div className="my-2 border-t border-white/10" />
          <div className="flex justify-between font-bold text-white"><span>Total paid</span><span>{formatINR(order.total)}</span></div>
          <div className="flex justify-between text-white/50"><span>Payment method</span><span>{order.paymentMethod}</span></div>
          <div className="flex justify-between text-white/50"><span>Delivery address</span><span className="text-right">{order.address.line1}, {order.address.city}</span></div>
          {order.installationRequested && <div className="flex justify-between text-white/50"><span>Installation</span><span>Requested</span></div>}
        </div>
      </div>
    </div>
  );
}
