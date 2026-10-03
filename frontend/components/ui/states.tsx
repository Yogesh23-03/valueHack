"use client";

import { AlertTriangle, RefreshCw, WifiOff } from "lucide-react";
import { ApiError } from "@/lib/api";

/** Simple shimmer block used by loading skeletons. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-white/5 ${className}`} />;
}

/** Generic card-shaped loading skeleton. */
export function LoadingSkeleton({ rows = 3, className = "h-6" }: { rows?: number; className?: string }) {
  return (
    <div className="space-y-3" role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className={className} />
      ))}
    </div>
  );
}

/** Empty state: placeholder text is allowed here only. */
export function EmptyState({
  title,
  hint,
  icon,
}: {
  title: string;
  hint?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      {icon && <div className="text-zinc-500">{icon}</div>}
      <p className="font-medium text-zinc-300">{title}</p>
      {hint && <p className="max-w-md text-sm text-zinc-500">{hint}</p>}
    </div>
  );
}

/**
 * Failed state with a Retry button. Renders the backend's {code, message}
 * as a friendly sentence — never a stack trace. Shows an offline hint when
 * the engine can't be reached.
 */
export function ErrorState({
  error,
  onRetry,
  title = "Something went wrong",
}: {
  error: unknown;
  onRetry?: () => void;
  title?: string;
}) {
  const offline = error instanceof ApiError && error.offline;
  const detail = error instanceof ApiError ? error.friendly : "Unexpected error. Try again.";
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center"
    >
      {offline ? (
        <WifiOff className="h-6 w-6 text-red-400" aria-hidden />
      ) : (
        <AlertTriangle className="h-6 w-6 text-red-400" aria-hidden />
      )}
      <div>
        <p className="font-medium text-red-300">{title}</p>
        <p className="mt-1 max-w-md text-sm text-zinc-400">{detail}</p>
        {error instanceof ApiError && !offline && error.code !== "HTTP_ERROR" && (
          <p className="mt-1 text-xs text-zinc-600">Error code: {error.code}</p>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
        >
          <RefreshCw className="h-4 w-4" aria-hidden /> Retry
        </button>
      )}
    </div>
  );
}
