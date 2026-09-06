"use client";

import { useState } from "react";
import { LayoutDashboard, Package, Boxes, Clock, CheckCircle2, IndianRupee } from "lucide-react";
import { initialPartnerOrders, initialPartnerInventory, PartnerOrder, PartnerOrderStatus } from "@/lib/data/partnerDashboard";
import { formatINR, cn } from "@/lib/utils";
import { useToastStore } from "@/lib/store/toastStore";

type Tab = "overview" | "orders" | "inventory";

const statusLabels: Record<PartnerOrderStatus, string> = {
  new: "New",
  accepted: "Accepted",
  packed: "Packed",
  ready: "Ready for pickup",
  picked_up: "Picked up",
  rejected: "Rejected",
};

const statusFlow: Record<PartnerOrderStatus, PartnerOrderStatus | null> = {
  new: "accepted",
  accepted: "packed",
  packed: "ready",
  ready: "picked_up",
  picked_up: null,
  rejected: null,
};

export default function PartnerDashboardPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [orders, setOrders] = useState<PartnerOrder[]>(initialPartnerOrders);
  const [inventory, setInventory] = useState(initialPartnerInventory);
  const push = useToastStore((s) => s.push);

  const todayOrders = orders.length;
  const pending = orders.filter((o) => o.pickupStatus !== "picked_up" && o.pickupStatus !== "rejected").length;
  const completed = orders.filter((o) => o.pickupStatus === "picked_up").length;
  const revenue = orders.filter((o) => o.pickupStatus === "picked_up").reduce((s, o) => s + o.value, 0);
  const inStock = inventory.filter((i) => i.available).length;

  function advance(id: string) {
    setOrders((prev) =>
      prev.map((o) => {
        if (o.id !== id) return o;
        const next = statusFlow[o.pickupStatus];
        if (!next) return o;
        return { ...o, pickupStatus: next, deliveryStatus: statusLabels[next] };
      })
    );
    push("Order status updated", "success");
  }

  function reject(id: string) {
    setOrders((prev) => prev.map((o) => (o.id === id ? { ...o, pickupStatus: "rejected", deliveryStatus: "Rejected" } : o)));
    push("Order rejected", "error");
  }

  function toggleAvailability(id: string) {
    setInventory((prev) => prev.map((i) => (i.id === id ? { ...i, available: !i.available } : i)));
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <div className="mb-6 flex items-center gap-2">
        <LayoutDashboard className="h-6 w-6 text-rush-cyan" />
        <h1 className="text-2xl font-extrabold tracking-tight text-white">Retail Partner Dashboard</h1>
      </div>

      <div className="mb-6 flex gap-2 border-b border-white/10">
        {(["overview", "orders", "inventory"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "focus-ring border-b-2 px-1 pb-3 text-sm font-semibold capitalize transition",
              tab === t ? "border-rush-cyan text-white" : "border-transparent text-white/40 hover:text-white/70"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <StatCard icon={Package} label="Today's orders" value={String(todayOrders)} />
          <StatCard icon={Clock} label="Pending orders" value={String(pending)} />
          <StatCard icon={CheckCircle2} label="Completed orders" value={String(completed)} />
          <StatCard icon={IndianRupee} label="Revenue (fulfilled)" value={formatINR(revenue)} />
          <StatCard icon={Boxes} label="Products in stock" value={String(inStock)} />
        </div>
      )}

      {tab === "orders" && (
        <div className="overflow-x-auto rounded-2xl border border-white/[0.07]">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-white/[0.04] text-xs uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">Order ID</th>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Customer Area</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t border-white/[0.06]">
                  <td className="px-4 py-3 font-medium text-white">#{o.id}</td>
                  <td className="px-4 py-3 text-white/70">{o.product}</td>
                  <td className="px-4 py-3 text-white/70">{o.customerArea}</td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      "rounded-full px-2.5 py-1 text-xs font-semibold",
                      o.pickupStatus === "rejected" ? "bg-rose-500/15 text-rose-400" :
                      o.pickupStatus === "picked_up" ? "bg-emerald-500/15 text-emerald-400" : "bg-rush/15 text-rush-cyan"
                    )}>
                      {statusLabels[o.pickupStatus]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {o.pickupStatus === "new" && (
                        <>
                          <button onClick={() => advance(o.id)} className="focus-ring rounded-full bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/25">
                            Accept
                          </button>
                          <button onClick={() => reject(o.id)} className="focus-ring rounded-full bg-rose-500/15 px-3 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-500/25">
                            Reject
                          </button>
                        </>
                      )}
                      {o.pickupStatus === "accepted" && (
                        <button onClick={() => advance(o.id)} className="focus-ring rounded-full bg-rush/15 px-3 py-1.5 text-xs font-semibold text-rush-cyan hover:bg-rush/25">
                          Mark packed
                        </button>
                      )}
                      {o.pickupStatus === "packed" && (
                        <button onClick={() => advance(o.id)} className="focus-ring rounded-full bg-rush/15 px-3 py-1.5 text-xs font-semibold text-rush-cyan hover:bg-rush/25">
                          Ready for pickup
                        </button>
                      )}
                      {(o.pickupStatus === "ready" || o.pickupStatus === "picked_up" || o.pickupStatus === "rejected") && (
                        <span className="text-xs text-white/30">No actions</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "inventory" && (
        <div className="overflow-x-auto rounded-2xl border border-white/[0.07]">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-white/[0.04] text-xs uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Stock</th>
                <th className="px-4 py-3">Availability</th>
                <th className="px-4 py-3">Delivery radius</th>
              </tr>
            </thead>
            <tbody>
              {inventory.map((item) => (
                <tr key={item.id} className="border-t border-white/[0.06]">
                  <td className="px-4 py-3 font-medium text-white">{item.product}</td>
                  <td className="px-4 py-3 text-white/50">{item.sku}</td>
                  <td className="px-4 py-3 text-white/70">{formatINR(item.price)}</td>
                  <td className="px-4 py-3 text-white/70">{item.stock}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleAvailability(item.id)}
                      className={cn(
                        "rounded-full px-2.5 py-1 text-xs font-semibold transition",
                        item.available ? "bg-emerald-500/15 text-emerald-400" : "bg-white/10 text-white/40"
                      )}
                    >
                      {item.available ? "Available" : "Unavailable"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-white/70">{item.deliveryRadiusKm} km</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
      <Icon className="mb-2 h-4 w-4 text-rush-cyan" />
      <p className="text-lg font-extrabold text-white">{value}</p>
      <p className="mt-0.5 text-[11px] text-white/45">{label}</p>
    </div>
  );
}
