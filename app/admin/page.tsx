"use client";

import { useState } from "react";
import {
  ShieldCheck, IndianRupee, ShoppingBag, Users, Store, Bike, Clock, XCircle, Package, MessageSquareWarning,
} from "lucide-react";
import {
  adminOverviewStats, topCategories, topProducts, adminOrders, adminPartners, deliveryPartners, supportTickets,
} from "@/lib/data/adminDashboard";
import { products } from "@/lib/data/products";
import { formatINR, cn } from "@/lib/utils";

type Tab = "overview" | "orders" | "partners" | "products" | "delivery" | "support";

const tabs: { key: Tab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "orders", label: "Orders" },
  { key: "partners", label: "Partners" },
  { key: "products", label: "Products & Inventory" },
  { key: "delivery", label: "Delivery" },
  { key: "support", label: "Support" },
];

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <div className="mb-6 flex items-center gap-2">
        <ShieldCheck className="h-6 w-6 text-rush-cyan" />
        <h1 className="text-2xl font-extrabold tracking-tight text-white">Admin Dashboard</h1>
      </div>

      <div className="no-scrollbar mb-6 flex gap-2 overflow-x-auto border-b border-white/10">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "focus-ring shrink-0 border-b-2 px-1 pb-3 text-sm font-semibold transition",
              tab === t.key ? "border-rush-cyan text-white" : "border-transparent text-white/40 hover:text-white/70"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab />}
      {tab === "orders" && <OrdersTab />}
      {tab === "partners" && <PartnersTab />}
      {tab === "products" && <ProductsTab />}
      {tab === "delivery" && <DeliveryTab />}
      {tab === "support" && <SupportTab />}
    </div>
  );
}

function OverviewTab() {
  const s = adminOverviewStats;
  return (
    <div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat icon={IndianRupee} label="GMV (this month)" value={formatINR(s.gmv)} />
        <Stat icon={ShoppingBag} label="Total orders" value={s.orders.toLocaleString("en-IN")} />
        <Stat icon={Users} label="Active users" value={s.activeUsers.toLocaleString("en-IN")} />
        <Stat icon={Store} label="Retail partners" value={String(s.retailPartners)} />
        <Stat icon={Bike} label="Delivery partners" value={String(s.deliveryPartners)} />
        <Stat icon={Clock} label="Avg. delivery time" value={`${s.avgDeliveryMinutes} min`} />
        <Stat icon={XCircle} label="Cancellation rate" value={`${s.cancellationRate}%`} />
        <Stat icon={Package} label="Live catalog size" value={`${products.length} SKUs`} />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-white/50">Top Categories</h2>
          <div className="space-y-3">
            {topCategories.map((c) => (
              <div key={c.name}>
                <div className="mb-1 flex justify-between text-xs text-white/60">
                  <span>{c.name}</span>
                  <span>{c.share}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-rush-gradient" style={{ width: `${c.share}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-white/50">Top Products</h2>
          <div className="space-y-3 text-sm">
            {topProducts.map((p, i) => (
              <div key={p.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10 text-xs font-bold text-white/60">{i + 1}</span>
                  <span className="text-white/80">{p.name}</span>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-white">{formatINR(p.revenue)}</p>
                  <p className="text-[11px] text-white/40">{p.orders} orders</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
      <Icon className="mb-2 h-4 w-4 text-rush-cyan" />
      <p className="text-lg font-extrabold text-white">{value}</p>
      <p className="mt-0.5 text-[11px] text-white/45">{label}</p>
    </div>
  );
}

function OrdersTab() {
  return (
    <Table
      head={["Order ID", "Customer", "Product", "Partner", "Status", "Total"]}
      rows={adminOrders.map((o) => [
        `#${o.id}`,
        o.customer,
        o.product,
        o.partner,
        <StatusPill key="s" status={o.status} />,
        formatINR(o.total),
      ])}
    />
  );
}

function PartnersTab() {
  return (
    <Table
      head={["Partner", "Type", "Area", "Orders", "Rating", "Status"]}
      rows={adminPartners.map((p) => [
        p.name,
        p.type,
        p.area,
        String(p.orders),
        `${p.rating}★`,
        <StatusPill key="s" status={p.status} />,
      ])}
    />
  );
}

function ProductsTab() {
  const rows = products.slice(0, 20).map((p) => {
    const totalStock = p.retailers.reduce((s, r) => s + r.stock, 0);
    return [
      p.name,
      p.brand,
      p.category.replace("-", " "),
      formatINR(p.price),
      String(totalStock),
      totalStock > 0 ? <StatusPill key="s" status="Active" /> : <StatusPill key="s" status="Suspended" label="Out of stock" />,
    ];
  });
  return <Table head={["Product", "Brand", "Category", "Price", "Total Stock", "Status"]} rows={rows} />;
}

function DeliveryTab() {
  return (
    <Table
      head={["Delivery Partner", "Zone", "Active", "Completed Today", "Rating", "Status"]}
      rows={deliveryPartners.map((d) => [
        d.name,
        d.zone,
        String(d.activeDeliveries),
        String(d.completedToday),
        `${d.rating}★`,
        <StatusPill key="s" status={d.status} />,
      ])}
    />
  );
}

function SupportTab() {
  return (
    <div className="space-y-3">
      {supportTickets.map((t) => (
        <div key={t.id} className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.03] p-4">
          <MessageSquareWarning className={cn("h-4 w-4 shrink-0", t.priority === "High" ? "text-rose-400" : t.priority === "Medium" ? "text-amber-400" : "text-white/40")} />
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{t.subject}</p>
            <p className="text-xs text-white/45">{t.customer} · {t.priority} priority</p>
          </div>
          <StatusPill status={t.status} />
        </div>
      ))}
    </div>
  );
}

function StatusPill({ status, label }: { status: string; label?: string }) {
  const positive = ["Delivered", "Active", "Online", "Resolved"].includes(status);
  const negative = ["Cancelled", "Suspended", "Offline"].includes(status);
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2.5 py-1 text-xs font-semibold",
        positive && "bg-emerald-500/15 text-emerald-400",
        negative && "bg-rose-500/15 text-rose-400",
        !positive && !negative && "bg-rush/15 text-rush-cyan"
      )}
    >
      {label ?? status}
    </span>
  );
}

function Table({ head, rows }: { head: string[]; rows: React.ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-white/[0.07]">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-white/[0.04] text-xs uppercase tracking-wide text-white/40">
          <tr>
            {head.map((h) => (
              <th key={h} className="px-4 py-3">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-white/[0.06]">
              {row.map((cell, j) => (
                <td key={j} className={cn("px-4 py-3", j === 0 ? "font-medium text-white" : "text-white/70")}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
