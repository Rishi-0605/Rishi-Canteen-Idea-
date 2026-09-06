import Link from "next/link";
import { Facebook, Instagram, Linkedin, Twitter } from "lucide-react";
import Logo from "@/components/ui/Logo";

const columns = [
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Careers", href: "/about#careers" },
      { label: "Contact", href: "/support" },
      { label: "Partner with us", href: "/partner" },
    ],
  },
  {
    title: "Customer",
    links: [
      { label: "Help Center", href: "/support" },
      { label: "Track Order", href: "/orders" },
      { label: "Returns", href: "/support#returns" },
      { label: "Warranty", href: "/support#warranty" },
      { label: "Installation", href: "/support#installation" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Terms", href: "/legal/terms" },
      { label: "Privacy", href: "/legal/privacy" },
      { label: "Refund Policy", href: "/legal/refunds" },
      { label: "Shipping Policy", href: "/legal/shipping" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-white/[0.06] bg-navy-950 pb-24 pt-14 md:pb-14">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-5">
          <div className="col-span-2">
            <Logo size="md" />
            <p className="mt-3 max-w-xs text-sm text-white/50">TECHNOLOGY. DELIVERED FASTER.</p>
            <div className="mt-5 flex gap-3">
              {[Instagram, Twitter, Facebook, Linkedin].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  className="focus-ring flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-white/50 transition hover:border-rush-cyan/40 hover:text-rush-cyan"
                  aria-label="Social link"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-white/40">{col.title}</h3>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="focus-ring text-sm text-white/65 transition hover:text-white">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-white/[0.06] pt-6 text-xs text-white/40 md:flex-row md:items-center md:justify-between">
          <p>© 2026 TECHRUSH. All rights reserved.</p>
          <p className="max-w-2xl md:text-right">
            TECHRUSH connects customers with independent retail partners, authorized dealers and distributors. TECHRUSH
            is not affiliated with or endorsed by any electronics manufacturer or brand named on this site.
          </p>
        </div>
      </div>
    </footer>
  );
}
