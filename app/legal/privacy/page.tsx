import LegalPage from "@/components/legal/LegalPage";

export const metadata = { title: "Privacy Policy | TECHRUSH" };

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="September 2026">
      <p>
        This prototype stores your cart, wishlist, saved addresses, login state and order history locally in your
        browser (using localStorage) so the experience persists across visits. No account data is transmitted to or
        stored on a TECHRUSH server in this demo build.
      </p>
      <p>
        In a production version, TECHRUSH would collect delivery location, contact details and order history to
        match you with nearby retail partners and delivery partners, process payments securely, and provide order
        support — governed by a full privacy policy compliant with applicable data protection law.
      </p>
      <p>You can clear all locally stored data at any time by clearing your browser&apos;s site data for this app.</p>
    </LegalPage>
  );
}
