// TARGET PATH IN REPO: frontend/src/app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: {
    default: 'NyayaSetu — IPC ↔ BNS Transition Platform',
    template: '%s · NyayaSetu',
  },
  description:
    'AI-assisted legal migration platform for translating Indian Penal Code (IPC) references to the Bharatiya Nyaya Sanhita (BNS) with traceable, engineering-grade validation.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col font-sans">
        <div className="flex-1">{children}</div>
        <footer className="border-t border-slate-200 bg-white">
          <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <span>NyayaSetu AI — IPC ↔ BNS Legal Intelligence Platform</span>
            <span>
              For research assistance only — not legal advice. Mappings require
              human review.
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
