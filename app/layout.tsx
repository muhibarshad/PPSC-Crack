import './globals.css';
import AuthProvider from '@/components/auth/AuthProvider';
import ClientProviders from '@/components/ClientProviders';

// Register GSAP plugins globally
import '@/lib/gsap-init';

export const metadata = {
  title: 'PPSC Crack — AI-Powered Exam Domination System',
  description:
    'Stop guessing. Start dominating. Pakistan\'s first AI system that analyzes 500+ past PPSC papers, detects hidden patterns, and tells you exactly what to study.',
  keywords: 'PPSC, exam preparation, AI, Pakistan, competitive exams, past papers, prediction',
  openGraph: {
    title: 'PPSC Crack — AI-Powered Exam Domination System',
    description: 'Pakistan\'s first AI system that analyzes 500+ past PPSC papers and tells you exactly what to study.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="bg-atmosphere" />
        <AuthProvider>
          <ClientProviders>{children}</ClientProviders>
        </AuthProvider>
      </body>
    </html>
  );
}
