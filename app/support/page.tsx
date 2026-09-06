"use client";

import { useState } from "react";
import { HelpCircle, Mail, MessageCircle, Phone, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToastStore } from "@/lib/store/toastStore";

const faqs = [
  {
    id: "returns",
    q: "What is the return policy?",
    a: "Most products are eligible for a 7-day easy replacement if they arrive damaged, defective or different from what was ordered. Return eligibility is shown on each product page.",
  },
  {
    id: "warranty",
    q: "How does warranty work?",
    a: "Products carry the manufacturer's standard warranty, honored through the retail partner or manufacturer's authorized service network. Extended warranty is available on select large appliances.",
  },
  {
    id: "installation",
    q: "How do I request installation?",
    a: "For eligible large appliances (TVs, ACs, refrigerators, washing machines), you can request installation at checkout or from the product page. A technician will contact you after delivery.",
  },
  {
    id: "delivery",
    q: "How is delivery time estimated?",
    a: "Delivery estimates are calculated based on nearby retail partner distance, product size, stock availability and delivery partner availability. They are estimates, not guarantees.",
  },
  {
    id: "cancel",
    q: "Can I cancel my order?",
    a: "Orders can be cancelled before they are marked 'On the way'. Once out for delivery, please contact support to arrange a return instead.",
  },
];

export default function SupportPage() {
  const [openId, setOpenId] = useState<string | null>("returns");
  const push = useToastStore((s) => s.push);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 md:px-6">
      <div className="mb-8 text-center">
        <HelpCircle className="mx-auto mb-3 h-10 w-10 text-rush-cyan" />
        <h1 className="text-2xl font-extrabold tracking-tight text-white">Help Center</h1>
        <p className="mt-2 text-sm text-white/50">We&apos;re here to help with orders, delivery, returns and more.</p>
      </div>

      <div className="mb-10 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <a href="tel:+911800000000" className="focus-ring flex flex-col items-center gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 text-center hover:border-rush/40">
          <Phone className="h-5 w-5 text-rush-cyan" />
          <span className="text-sm font-semibold text-white">Call us</span>
          <span className="text-xs text-white/40">1800-000-000</span>
        </a>
        <a href="mailto:support@techrush.example" className="focus-ring flex flex-col items-center gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 text-center hover:border-rush/40">
          <Mail className="h-5 w-5 text-rush-cyan" />
          <span className="text-sm font-semibold text-white">Email us</span>
          <span className="text-xs text-white/40">support@techrush.example</span>
        </a>
        <button
          onClick={() => push("Live chat coming soon in the prototype.", "info")}
          className="focus-ring flex flex-col items-center gap-2 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 text-center hover:border-rush/40"
        >
          <MessageCircle className="h-5 w-5 text-rush-cyan" />
          <span className="text-sm font-semibold text-white">Live chat</span>
          <span className="text-xs text-white/40">Avg. reply in 2 min</span>
        </button>
      </div>

      <div className="space-y-2">
        {faqs.map((faq) => (
          <div key={faq.id} id={faq.id} className="rounded-xl border border-white/[0.07] bg-white/[0.02]">
            <button
              onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
              className="focus-ring flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left"
            >
              <span className="text-sm font-semibold text-white">{faq.q}</span>
              <ChevronDown className={cn("h-4 w-4 shrink-0 text-white/40 transition", openId === faq.id && "rotate-180")} />
            </button>
            {openId === faq.id && <p className="px-4 pb-4 text-sm text-white/55">{faq.a}</p>}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          push("Your message has been sent. Our team will reach out shortly.", "success");
          e.currentTarget.reset();
        }}
        className="mt-10 space-y-3 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5"
      >
        <h2 className="text-sm font-bold uppercase tracking-wide text-white/50">Still need help?</h2>
        <input required placeholder="Your name" className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2.5 text-sm text-white placeholder:text-white/30" />
        <input required type="email" placeholder="Email address" className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2.5 text-sm text-white placeholder:text-white/30" />
        <textarea required placeholder="How can we help?" rows={4} className="focus-ring w-full rounded-lg border border-white/10 bg-navy-800 px-3 py-2.5 text-sm text-white placeholder:text-white/30" />
        <button type="submit" className="focus-ring rounded-full bg-rush-gradient px-6 py-2.5 text-sm font-bold text-white">Send message</button>
      </form>
    </div>
  );
}
