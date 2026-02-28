import Icon from '@/components/Icon';

export default function Footer() {
  return (
    <footer className="footer relative z-10 border-t border-white/5 pt-24 pb-12 bg-background overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,rgba(139,92,246,0.05)_0%,transparent_60%)] pointer-events-none mix-blend-screen" />

      <div className="container max-w-7xl mx-auto px-6 relative z-10">
        <div className="flex flex-col items-center gap-10">

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-neon flex items-center justify-center font-black text-white text-sm">
              P
            </div>
            <div>
              <div className="font-display font-black text-xl text-white tracking-tight leading-none mb-1">
                PPSC Crack
              </div>
              <div className="text-xs text-primary-light font-medium tracking-wide uppercase">
                AI-Powered Exam Intelligence
              </div>
            </div>
          </div>

          <div className="flex items-center gap-8 flex-wrap justify-center text-sm font-medium text-white/50">
            {['Features', 'How It Works', 'Pricing', 'Privacy', 'Terms', 'Contact'].map((item) => (
              <a 
                key={item} 
                href={`#${item.toLowerCase().replace(/ /g, '-')}`} 
                className="hover:text-primary transition-colors"
              >
                {item}
              </a>
            ))}
          </div>

          <div className="w-24 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-4" />

          <p className="text-xs text-white/30 text-center font-medium">
            © {new Date().getFullYear()} PPSC Crack. All rights reserved. <br/>
            Engineered for precision.
          </p>

        </div>
      </div>
    </footer>
  );
}
