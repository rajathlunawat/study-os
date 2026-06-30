import './globals.css';

export const metadata = {
  title: 'StudyOS — Notebook',
  description: 'AI-Powered Study Operating System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#121212" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
