import LegalPage from "@/components/legal/LegalPage";

export const metadata = { title: "Shipping Policy | TECHRUSH" };

export default function ShippingPage() {
  return (
    <LegalPage title="Shipping Policy" updated="September 2026">
      <p>
        TECHRUSH fulfills orders from the nearest participating retail partner with available stock, rather than a
        centralized warehouse. Delivery estimates (30 minutes – 2 hours) depend on partner distance, product size,
        order preparation time and delivery partner availability.
      </p>
      <p>
        Small accessories typically arrive fastest; large appliances such as TVs, refrigerators and washing machines
        take longer and may be scheduled with an installation slot.
      </p>
      <p>
        Serviceability is limited to areas with participating retail partners. If your location isn&apos;t
        serviceable yet, the app will let you know at checkout.
      </p>
    </LegalPage>
  );
}
