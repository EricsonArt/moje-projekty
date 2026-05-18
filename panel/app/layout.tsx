import "./globals.css";

export const metadata = {
  title: "Skala Viral Panel",
  description: "Sterowanie generatorem skryptów",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}
