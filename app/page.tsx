import './landing.css';
import Navbar from '@/components/landing/Navbar';
import HeroSection from '@/components/landing/HeroSection';
import ProblemSolution from '@/components/landing/ProblemSolution';
import FeaturesSection from '@/components/landing/FeaturesSection';
import StepsSection from '@/components/landing/StepsSection';
import PricingSection from '@/components/landing/PricingSection';
import TestimonialsSection from '@/components/landing/TestimonialsSection';
import CTASection from '@/components/landing/CTASection';
import Footer from '@/components/landing/Footer';

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <HeroSection />
      <ProblemSolution />
      <FeaturesSection />
      <StepsSection />
      <PricingSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </>
  );
}
