import LegalPage from "@/components/legal/LegalPage";

export const metadata = { title: "Refund Policy | TECHRUSH" };

export default function RefundsPage() {
  return (
    <LegalPage title="Refund Policy" updated="September 2026">
      <p>
        Most products purchased through TECHRUSH are eligible for a 7-day easy replacement if received damaged,
        defective, or materially different from the listing. Some large appliances may carry a manufacturer-led
        replacement process instead of a direct swap.
      </p>
      <p>
        Refunds for cancelled orders (before dispatch) are processed back to the original payment method. Orders
        paid via Cash on Delivery are refunded via bank transfer or store credit.
      </p>
      <p>Refund timelines vary by payment method and retail partner, typically 3–7 business days once approved.</p>
    </LegalPage>
  );
}
