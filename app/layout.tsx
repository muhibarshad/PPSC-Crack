import './globals.css';
import AuthProvider from '@/components/auth/AuthProvider';

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
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
