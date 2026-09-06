import Logo from "@/components/ui/Logo";

export const metadata = { title: "About | TECHRUSH" };

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 md:px-6">
      <Logo size="lg" className="mb-6" />
      <h1 className="text-3xl font-extrabold tracking-tight text-white">Quick commerce for electronics.</h1>
      <div className="mt-6 space-y-5 text-sm leading-relaxed text-white/60">
        <p>
          TECHRUSH connects customers with existing electronics retailers, distributors, warehouses and authorized
          sellers — instead of operating expensive dark stores for large and expensive electronics.
        </p>
        <p>
          Our platform matches every order with the fastest eligible nearby source, so customers get genuine
          products with estimated delivery in as little as 30 minutes, and retail partners reach more customers
          without giving up their existing storefront.
        </p>
        <p>
          TECHRUSH is a technology marketplace, not a manufacturer or a single retailer. We are not affiliated with
          or endorsed by any electronics brand named on this site — products listed are sourced from independent,
          participating retail partners.
        </p>
        <h2 className="pt-4 text-lg font-bold text-white" id="careers">Careers</h2>
        <p>
          We&apos;re a small team building the future of local electronics delivery in India. This prototype
          doesn&apos;t have live openings yet — check back soon.
        </p>
      </div>
    </div>
  );
}
