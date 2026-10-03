import "./globals.css";
import { Inter, JetBrains_Mono } from "next/font/google";
import TopNav from "@/components/nav/TopNav";
import { ThemeProvider } from "@/components/providers/ThemeProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "BizSim | Fire-drill Simulator",
  description: "See the chain before it happens. Cash-flow fire-drill simulator for small Indian businesses.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${mono.variable} font-sans antialiased min-h-screen relative`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <div className="aurora-bg">
            <div className="aurora-blob-1" />
            <div className="aurora-blob-2" />
          </div>
          <div className="grid-pattern" />
          <TopNav />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
