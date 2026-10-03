"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  UploadCloud,
  FileText,
  ArrowRight,
  Play,
  Zap,
  ShieldCheck,
  LineChart,
} from "lucide-react";
import { uploadCsv, ApiError } from "@/lib/api";
import { GlassCard } from "@/components/ui/GlassCard";

const Hero3D = dynamic(() => import("@/components/hero/Hero3D"), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] sm:h-[480px] w-full flex items-center justify-center text-muted-foreground text-sm animate-pulse rounded-3xl border border-card-border bg-card/40">
      Loading 3D Supply Chain Visualizer...
    </div>
  ),
});

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [tableType, setTableType] = useState<string>("auto");
  const [loading, setLoading] = useState(false);
  const [showIntro, setShowIntro] = useState(false);

  useEffect(() => {
    const seen = sessionStorage.getItem("bizsim_intro_seen");
    if (!seen) {
      setShowIntro(true);
      sessionStorage.setItem("bizsim_intro_seen", "true");
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const toastId = toast.loading("Validating and parsing CSV file...");

    try {
      const res = await uploadCsv(file, tableType === "auto" ? undefined : tableType);
      toast.success("CSV Validation Passed!", {
        id: toastId,
        description: res.message,
      });
      setTimeout(() => router.push("/dashboard"), 1200);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        toast.error(`CSV Validation Error [${err.code}]`, {
          id: toastId,
          description: err.friendly,
        });
      } else {
        toast.error("CSV Validation Failed", {
          id: toastId,
          description: "Could not parse or validate the CSV file.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const scrollToUploader = () => {
    document.getElementById("csv-uploader-section")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="space-y-16 py-4">
      {/* Optional Session Intro Overlay */}
      <AnimatePresence>
        {showIntro && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-2xl p-6"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-center space-y-6 max-w-lg"
            >
              <div className="inline-flex p-4 rounded-3xl bg-primary/15 border border-primary/30 text-primary shadow-xl">
                <Zap className="w-10 h-10" />
              </div>
              <h2 className="text-3xl font-extrabold text-foreground tracking-tight">
                Welcome to <span className="text-gradient">BizSim</span>
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                A cash-flow fire-drill simulator built for small Indian businesses. Model supply delays and cash gaps before they happen.
              </p>
              <button
                onClick={() => setShowIntro(false)}
                className="px-8 py-3 rounded-2xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/30 hover:scale-105 active:scale-95 transition-all"
              >
                Launch Simulator
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero Section with 3D Cover */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-7 space-y-6 text-center lg:text-left"
        >
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-primary shadow-xs">
              <Play className="h-3.5 w-3.5 fill-primary" /> SMVIT ValueHack 2026 Demo
            </span>
            <button
              onClick={() => setShowIntro(true)}
              className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-4"
            >
              Replay intro
            </button>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-foreground leading-[1.1]">
            See the cash-flow chain <br />
            <span className="text-gradient">before it breaks.</span>
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto lg:mx-0">
            Simulate 14-day supply delays, customer payment holds, and cost spikes for <strong>Sharma Hardware and Electricals</strong> before they trigger a cash-flow failure.
          </p>

          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2">
            <Link
              href="/dashboard"
              onClick={() => toast.success("Sharma Hardware Demo loaded!")}
              className="px-8 py-3.5 rounded-2xl bg-primary font-bold text-white shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2 text-sm"
            >
              Load Sharma Hardware Demo <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={scrollToUploader}
              className="px-8 py-3.5 rounded-2xl border border-card-border bg-card/60 hover:bg-muted/60 font-semibold text-foreground text-sm transition-all"
            >
              Upload your CSVs
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="lg:col-span-5 relative"
        >
          <Hero3D />
        </motion.div>
      </div>

      {/* Below the Fold Section 1: How It Works */}
      <div className="space-y-8 max-w-5xl mx-auto">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-extrabold text-foreground">How BizSim Works</h2>
          <p className="text-xs text-muted-foreground">Four steps to stress-test your business resilience</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { step: "01", title: "Load Data", desc: "Use Sharma Hardware demo or upload your own CSV files." },
            { step: "02", title: "Set Shock", desc: "Select 14-day supplier delay, customer hold, or cost spike." },
            { step: "03", title: "View Cascade", desc: "Trace stock-out days, cash drops, and payment failures." },
            { step: "04", title: "Compare Actions", desc: "Evaluate engine-suggested supplier switches and advances." },
          ].map((s, i) => (
            <GlassCard key={i} className="p-5 flex flex-col justify-between space-y-4">
              <span className="font-mono text-2xl font-black text-primary/40">{s.step}</span>
              <div>
                <h3 className="font-bold text-sm text-foreground mb-1">{s.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{s.desc}</p>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>

      {/* Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        <Link href="/dashboard">
          <GlassCard className="h-full hover:border-primary/40 transition-all cursor-pointer p-6 space-y-3">
            <div className="p-3 rounded-2xl bg-primary/10 text-primary border border-primary/20 w-fit">
              <LineChart className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-foreground">Executive Dashboard</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Track cash balance, catalog SKUs, stock cover remaining days, and supplier dependency shares.
            </p>
          </GlassCard>
        </Link>

        <Link href="/fire-drill">
          <GlassCard className="h-full hover:border-primary/40 transition-all cursor-pointer p-6 space-y-3">
            <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/20 w-fit">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-foreground">Fire Drill Simulator</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Interactive cascade timeline, deterministic 'Why?' panel, demand ranges, and action choices.
            </p>
          </GlassCard>
        </Link>

        <Link href="/vendor-check">
          <GlassCard className="h-full hover:border-primary/40 transition-all cursor-pointer p-6 space-y-3">
            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-500 border border-blue-500/20 w-fit">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-foreground">Signals & Reports</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Audit 8 vendor trust signals, scan PDF invoices for overcharges, and export executive PDF reports.
            </p>
          </GlassCard>
        </Link>
      </div>

      {/* CSV Uploader Section */}
      <div id="csv-uploader-section" className="max-w-3xl mx-auto pt-4">
        <GlassCard className="p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-card-border pb-4">
            <h2 className="text-xl font-bold flex items-center gap-2.5 text-foreground">
              <FileText className="h-5 w-5 text-primary" />
              CSV Payload Validator & Loader
            </h2>
            <span className="text-xs font-semibold text-muted-foreground">POST /api/business/load</span>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="csv-table-type" className="block text-xs font-semibold text-muted-foreground mb-1">
                  Target Entity Table
                </label>
                <select
                  id="csv-table-type"
                  value={tableType}
                  onChange={(e) => setTableType(e.target.value)}
                  className="w-full bg-card border border-card-border rounded-xl px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  <option value="auto">Auto-detect from headers</option>
                  <option value="products">Products (products.csv)</option>
                  <option value="suppliers">Suppliers (suppliers.csv)</option>
                  <option value="customers">Customers (customers.csv)</option>
                  <option value="orders">Orders (orders.csv)</option>
                </select>
              </div>
              <div>
                <label htmlFor="csv-file-input" className="block text-xs font-semibold text-muted-foreground mb-1">
                  Select CSV File
                </label>
                <input
                  id="csv-file-input"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="w-full bg-card border border-card-border rounded-xl px-3 py-1.5 text-xs text-foreground file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-primary/15 file:text-primary file:text-xs file:font-bold"
                />
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="w-full py-3.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <UploadCloud className="h-4 w-4" />
              {loading ? "Validating & Inserting..." : "Upload & Validate Payload"}
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
