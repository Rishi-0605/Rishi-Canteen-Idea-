import LegalPage from "@/components/legal/LegalPage";

export const metadata = { title: "Terms of Service | TECHRUSH" };

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" updated="September 2026">
      <p>
        These Terms govern your use of the TECHRUSH platform, a prototype marketplace connecting customers with
        independent retail partners, authorized dealers, distributors and brand warehouses for electronics and
        appliances.
      </p>
      <p>
        TECHRUSH acts as a technology intermediary. Products are sold and fulfilled by participating retail
        partners; TECHRUSH does not manufacture or directly warehouse the majority of inventory shown on the
        platform.
      </p>
      <p>
        Delivery estimates shown throughout the app (including &quot;30 minutes&quot;, &quot;42 min&quot; and similar
        figures) are estimates only, based on partner distance, product size and availability. They are not
        guaranteed delivery windows.
      </p>
      <p>
        This build is a product prototype. Payments, OTP verification and account creation are simulated for
        demonstration purposes and no real financial transactions are processed.
      </p>
      <p>By using TECHRUSH, you agree to these terms and our Privacy Policy, Refund Policy and Shipping Policy.</p>
    </LegalPage>
  );
}
