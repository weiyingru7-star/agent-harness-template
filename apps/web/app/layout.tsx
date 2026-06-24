import "./globals.css";

export const metadata = {
  title: "Agent Harness Template",
  description: "Business-agnostic starter template for agent applications",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
