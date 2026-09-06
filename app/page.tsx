import Hero from "@/components/home/Hero";
import CategoryScroll from "@/components/home/CategoryScroll";
import FeaturedProducts from "@/components/home/FeaturedProducts";
import DeliveredFast from "@/components/home/DeliveredFast";
import WhyTechrush from "@/components/home/WhyTechrush";
import PartnerSection from "@/components/home/PartnerSection";

export default function HomePage() {
  return (
    <>
      <Hero />
      <CategoryScroll />
      <FeaturedProducts />
      <DeliveredFast />
      <WhyTechrush />
      <PartnerSection />
    </>
  );
}
