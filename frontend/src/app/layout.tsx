import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'GARDA-JKN | SIMRS V-Claim',
  description: 'AI Adjudicator for BPJS Claims',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
