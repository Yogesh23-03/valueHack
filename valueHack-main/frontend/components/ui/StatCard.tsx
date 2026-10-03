"use client";

import React, { useEffect, useState } from "react";
import { formatInr } from "@/lib/format";
import { GlassCard } from "./GlassCard";

interface StatCardProps {
  title: string;
  value: number;
  isCurrency?: boolean;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: { value: string; positive?: boolean };
}

export function StatCard({ title, value, isCurrency = false, subtitle, icon, trend }: StatCardProps) {
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 1000;
    const steps = 30;
    const increment = (value - start) / steps;
    const stepTime = duration / steps;

    const timer = setInterval(() => {
      start += increment;
      if ((increment >= 0 && start >= value) || (increment < 0 && start <= value)) {
        setDisplayVal(value);
        clearInterval(timer);
      } else {
        setDisplayVal(Math.round(start));
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <GlassCard className="flex flex-col justify-between">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</span>
        {icon && <div className="p-2 rounded-xl bg-primary/10 text-primary border border-primary/20">{icon}</div>}
      </div>

      <div className="mt-3">
        <p className="font-mono font-bold text-2xl sm:text-3xl text-foreground font-tabular">
          {isCurrency ? formatInr(displayVal) : displayVal.toLocaleString("en-IN")}
        </p>

        <div className="mt-1 flex items-center gap-2">
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          {trend && (
            <span
              className={`inline-flex items-center text-xs font-semibold ${
                trend.positive ? "text-green-500" : "text-amber-500"
              }`}
            >
              {trend.value}
            </span>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
