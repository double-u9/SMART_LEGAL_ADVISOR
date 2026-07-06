import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'المستشار القانوني الذكي — Smart Legal Advisor',
  description: 'مستشار قانوني ذكي يعمل بالذكاء الاصطناعي للقانون العراقي. يوفر إجابات دقيقة مع استشهادات من الكتب القانونية الرسمية.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl" className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0A0F1C" />
      </head>
      <body className="bg-gradient-navy min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
