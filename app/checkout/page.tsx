"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin, Plus, Check, Zap, Smartphone, CreditCard, Landmark, Wallet, Banknote, Loader2, CheckCircle2, Wrench,
} from "lucide-react";
import { cartTotals, useCartStore } from "@/lib/store/cartStore";
import { useUserStore } from "@/lib/store/userStore";
import { getProduct } from "@/lib/data/products";
import { formatINR, estimateDeliveryMinutes, formatMinutes, cn } from "@/lib/utils";
import { apiPlaceOrder } from "@/lib/api/mockApi";
import { Address } from "@/lib/types";
import { useToastStore } from "@/lib/store/toastStore";

const steps = ["Address", "Delivery", "Payment", "Confirmation"] as const;

const paymentMethods = [
  { key: "upi", label: "UPI", Icon: Smartphone, desc: "Pay via Google Pay, PhonePe, Paytm & more" },
  { key: "card", label: "Credit / Debit Card", Icon: CreditCard, desc: "Visa, Mastercard, RuPay accepted" },
  { key: "netbanking", label: "Net Banking", Icon: Landmark, desc: "All major banks supported" },
  { key: "emi", label: "EMI", Icon: Wallet, desc: "No-cost EMI on select cards" },
  { key: "cod", label: "Cash on Delivery", Icon: Banknote, desc: "Available for orders under ₹50,000" },
];

export default function CheckoutPage() {
  const router = useRouter();
  const items = useCartStore((s) => s.items.filter((i) => !i.savedForLater));
  const clearCart = useCartStore((s) => s.clear);
  const addresses = useUserStore((s) => s.addresses);
  const addAddress = useUserStore((s) => s.addAddress);
  const addOrder = useUserStore((s) => s.addOrder);
  const push = useToastStore((s) => s.push);

  const [stepIdx, setStepIdx] = useState(0);
  const [selectedAddressId, setSelectedAddressId] = useState(addresses.find((a) => a.isDefault)?.id ?? addresses[0]?.id);
  const [showAddForm, setShowAddForm] = useState(false);
  const [installationRequested, setInstallationRequested] = useState(false);
  const [payment, setPayment] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [placedOrderId, setPlacedOrderId] = useState<string | null>(null);

  const totals = cartTotals(items);
  const selectedAddress = addresses.find((a) => a.id === selectedAddressId);
  const hasInstallable = useMemo(
    () => items.some((i) => getProduct(i.productId)?.installationAvailable),
    [items]
  );
  const maxEta = useMemo(() => {
    let max = 0;
    for (const item of items) {
      const p = getProduct(item.productId);
      if (!p) continue;
      const eta = estimateDeliveryMinutes(p.size, p.retailers[0]?.distanceKm ?? 3, item.quantity);
      max = Math.max(max, eta);
    }
    return max || 30;
  }, [items]);

  if (items.length === 0 && !placedOrderId) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <h1 className="text-xl font-bold text-white">Your cart is empty</h1>
        <p className="mt-2 text-sm text-white/50">Add something to your cart before checking out.</p>
        <Link href="/products" className="focus-ring mt-5 inline-block rounded-full bg-rush-gradient px-6 py-3 text-sm font-bold text-white">
          Browse products
        </Link>
      </div>
    );
  }

  function goNext() {
    if (stepIdx === 0 && !selectedAddress) {
      push("Please select a delivery address", "error");
      return;
    }
    if (stepIdx === 2) {
      if (!payment) {
        push("Please choose a payment method", "error");
        return;
      }
      void placeOrder();
      return;
    }
    setStepIdx((s) => Math.min(s + 1, steps.length - 1));
  }

  async function placeOrder() {
    if (!selectedAddress) return;
    setProcessing(true);
    try {
      const order = await apiPlaceOrder({
        items: items.map((i) => {
          const p = getProduct(i.productId)!;
          return { productId: p.id, name: p.name, image: p.color, price: p.price, quantity: i.quantity };
        }),
        address: selectedAddress,
        paymentMethod: paymentMethods.find((p) => p.key === payment)?.label ?? "UPI",
        subtotal: totals.subtotal,
        deliveryFee: totals.deliveryFee,
        platformFee: totals.platformFee,
        discount: totals.discount,
        total: totals.total,
        installationRequested,
      });
      addOrder(order);
      clearCart();
      setPlacedOrderId(order.id);
      setStepIdx(3);
      push("Order placed successfully!", "success");
    } catch {
      push("Payment failed. Please try again.", "error");
    } finally {
      setProcessing(false);
    }
  }

  function addNewAddress(formData: FormData) {
    const addr: Address = {
      id: `addr-${Date.now()}`,
      label: String(formData.get("label") || "Other"),
      line1: String(formData.get("line1") || ""),
      line2: String(formData.get("line2") || ""),
      city: String(formData.get("city") || ""),
      state: String(formData.get("state") || ""),
      pincode: String(formData.get("pincode") || ""),
    };
    addAddress(addr);
    setSelectedAddressId(addr.id);
    setShowAddForm(false);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-6">
      <h1 className="mb-2 text-2xl font-extrabold tracking-tight text-white">Checkout</h1>

      {/* Stepper */}
      <div className="mb-8 flex items-center gap-2">
        {steps.map((label, i) => (
          <div key={label} className="flex flex-1 items-center gap-2">
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition",
                i < stepIdx || (i === 3 && placedOrderId) ? "bg-emerald-500 text-white" :
                i === stepIdx ? "bg-rush-gradient text-white" : "bg-white/10 text-white/40"
              )}
            >
              {i < stepIdx || (i === 3 && placedOrderId && i <= stepIdx) ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <span className={cn("hidden text-xs font-medium sm:block", i === stepIdx ? "text-white" : "text-white/40")}>{label}</span>
            {i < steps.length - 1 && <div className="h-px flex-1 bg-white/10" />}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {stepIdx === 0 && (
          <motion.div key="address" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-3">
            {addresses.map((addr) => (
              <button
                key={addr.id}
                onClick={() => setSelectedAddressId(addr.id)}
                className={cn(
                  "focus-ring flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition",
                  selectedAddressId === addr.id ? "border-rush bg-rush/10" : "border-white/10 bg-white/[0.03] hover:border-white/20"
                )}
              >
                <MapPin className={cn("mt-0.5 h-4 w-4 shrink-0", selectedAddressId === addr.id ? "text-rush-cyan" : "text-white/40")} />
                <div>
                  <p className="text-sm font-bold text-white">{addr.label}</p>
                  <p className="text-xs text-white/55">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ""}, {addr.city}, {addr.state} - {addr.pincode}</p>
                </div>
              </button>
            ))}

            {!showAddForm ? (
              <button
                onClick={() => setShowAddForm(true)}
                className="focus-ring flex w-full items-center gap-2 rounded-2xl border border-dashed border-white/20 p-4 text-sm font-medium text-white/60 hover:border-rush-cyan/50 hover:text-white"
              >
                <Plus className="h-4 w-4" /> Add a new address
              </button>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  addNewAddress(new FormData(e.currentTarget));
                }}
                className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4"
              >
                <div className="grid grid-cols-2 gap-3">
                  <input name="label" placeholder="Label (Home, Office)" required className="focus-ring rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                  <input name="pincode" placeholder="Pincode" required className="focus-ring rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                </div>
                <input name="line1" placeholder="Flat, House no., Building" required className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                <input name="line2" placeholder="Area, Street (optional)" className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                <div className="grid grid-cols-2 gap-3">
                  <input name="city" placeholder="City" required className="focus-ring rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                  <input name="state" placeholder="State" required className="focus-ring rounded-lg border border-white/10 bg-navy-800 px-3 py-2 text-sm text-white placeholder:text-white/30" />
                </div>
                <div className="flex gap-2">
                  <button type="submit" className="focus-ring rounded-full bg-rush-gradient px-5 py-2 text-xs font-bold text-white">Save address</button>
                  <button type="button" onClick={() => setShowAddForm(false)} className="focus-ring rounded-full border border-white/15 px-5 py-2 text-xs font-medium text-white/60">Cancel</button>
                </div>
              </form>
            )}
          </motion.div>
        )}

        {stepIdx === 1 && (
          <motion.div key="delivery" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-3">
            <div className="flex items-start gap-3 rounded-2xl border border-rush bg-rush/10 p-4">
              <Zap className="mt-0.5 h-5 w-5 shrink-0 text-rush-cyan" />
              <div>
                <p className="text-sm font-bold text-white">Rush Delivery</p>
                <p className="text-xs text-white/60">Estimated arrival in {formatMinutes(maxEta)} from the nearest retail partner.*</p>
              </div>
            </div>
            {hasInstallable && (
              <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <input
                  type="checkbox"
                  checked={installationRequested}
                  onChange={(e) => setInstallationRequested(e.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-rush"
                />
                <div>
                  <p className="flex items-center gap-1.5 text-sm font-bold text-white"><Wrench className="h-4 w-4 text-rush-cyan" /> Request installation</p>
                  <p className="text-xs text-white/50">A trained technician will set up your large appliance after delivery.</p>
                </div>
              </label>
            )}
            <p className="text-xs text-white/35">*Delivery time is an estimate and may vary with traffic, weather and partner availability.</p>
          </motion.div>
        )}

        {stepIdx === 2 && (
          <motion.div key="payment" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-3">
            {paymentMethods.map((m) => (
              <button
                key={m.key}
                onClick={() => setPayment(m.key)}
                className={cn(
                  "focus-ring flex w-full items-center gap-3 rounded-2xl border p-4 text-left transition",
                  payment === m.key ? "border-rush bg-rush/10" : "border-white/10 bg-white/[0.03] hover:border-white/20"
                )}
              >
                <m.Icon className={cn("h-5 w-5", payment === m.key ? "text-rush-cyan" : "text-white/40")} />
                <div className="flex-1">
                  <p className="text-sm font-bold text-white">{m.label}</p>
                  <p className="text-xs text-white/45">{m.desc}</p>
                </div>
                {payment === m.key && <Check className="h-4 w-4 text-rush-cyan" />}
              </button>
            ))}
            <p className="text-xs text-white/35">This is a simulated checkout. No real payment information is collected or processed.</p>
          </motion.div>
        )}

        {stepIdx === 3 && placedOrderId && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center gap-4 rounded-3xl border border-emerald-500/30 bg-emerald-500/[0.06] p-10 text-center"
          >
            <CheckCircle2 className="h-14 w-14 text-emerald-400" />
            <h2 className="text-2xl font-extrabold text-white">Order Confirmed!</h2>
            <p className="text-sm text-white/60">
              Your order <span className="font-semibold text-white">#{placedOrderId}</span> has been placed. The nearby
              retail partner has been notified.
            </p>
            <div className="mt-2 flex flex-col gap-3 sm:flex-row">
              <Link href={`/orders/${placedOrderId}`} className="focus-ring rounded-full bg-rush-gradient px-6 py-3 text-sm font-bold text-white shadow-glow-sm">
                Track your order
              </Link>
              <Link href="/products" className="focus-ring rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white/70">
                Continue shopping
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {stepIdx < 3 && (
        <div className="mt-8 flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div>
            <p className="text-xs text-white/40">Total payable</p>
            <p className="text-lg font-bold text-white">{formatINR(totals.total)}</p>
          </div>
          <div className="flex gap-2">
            {stepIdx > 0 && (
              <button onClick={() => setStepIdx((s) => s - 1)} className="focus-ring rounded-full border border-white/15 px-5 py-3 text-sm font-medium text-white/70">
                Back
              </button>
            )}
            <button
              onClick={goNext}
              disabled={processing}
              className="focus-ring flex items-center gap-2 rounded-full bg-rush-gradient px-6 py-3 text-sm font-bold text-white shadow-glow-sm disabled:opacity-60"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Processing…
                </>
              ) : stepIdx === 2 ? (
                "PLACE ORDER"
              ) : (
                "CONTINUE"
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
