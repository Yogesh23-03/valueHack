import "./globals.css";
import { Inter, JetBrains_Mono } from "next/font/google";
import TopNav from "@/components/nav/TopNav";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "BizSim",
  description: "See the chain before it happens.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans antialiased min-h-screen relative`}>
        <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-drift"></div>
          <div className="absolute top-40 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-drift delay-1000"></div>
          <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl animate-drift delay-2000"></div>
        </div>
        <TopNav />
        <main className="max-w-7xl mx-auto px-4 py-8 relative">
          {children}
        </main>
      </body>
    </html>
  );
}
