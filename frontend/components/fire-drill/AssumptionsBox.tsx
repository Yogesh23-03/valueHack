import type { Assumption } from "@/lib/types";
import { SourceTag } from "@/components/ui/badges";

/**
 * Always-visible assumptions box (not hidden in a tooltip). Each assumption
 * shows its source (demo data / assumption / you set) and whether it can be
 * edited in the current UI.
 */
export default function AssumptionsBox({ assumptions }: { assumptions: Assumption[] }) {
  return (
    <section aria-label="Assumptions">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
        Assumptions this run makes
      </h3>
      <ul className="grid gap-2 md:grid-cols-2">
        {assumptions.map((a) => (
          <li key={a.id} className="rounded-xl border border-white/5 bg-white/5 p-3">
            <div className="mb-1 flex flex-wrap items-center gap-1.5">
              <SourceTag source={a.source} />
              {a.editable && (
                <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                  editable
                </span>
              )}
            </div>
            <p className="text-sm leading-snug text-zinc-300">{a.text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
