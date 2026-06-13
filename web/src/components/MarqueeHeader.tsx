import { SlidersHorizontal } from "lucide-react";

export type Tab = "feed" | "calendar" | "venues";

const TABS: { id: Tab; label: string }[] = [
  { id: "feed", label: "Feed" },
  { id: "calendar", label: "Calendar" },
  { id: "venues", label: "Venues" }
];

interface Props {
  tab: Tab;
  onTab: (t: Tab) => void;
  onOpenFilters: () => void;
  activeFilterCount: number;
}

export function MarqueeHeader({ tab, onTab, onOpenFilters, activeFilterCount }: Props) {
  return (
    <header className="sticky top-0 z-40 border-b border-ink-600 bg-ink-900/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          {/* Bulb-lit marquee wordmark — the signature header. */}
          <div className="flex items-center gap-3">
            <div className="bulbs animate-flicker h-1.5 w-10 rounded-full opacity-80" aria-hidden />
            <h1 className="font-display text-2xl leading-none tracking-[0.08em] text-bone sm:text-3xl">
              PNW <span className="text-coral">STAGE</span>
            </h1>
          </div>

          <button
            onClick={onOpenFilters}
            className="relative inline-flex items-center gap-2 rounded-md border border-ink-600 bg-ink-800 px-3 py-2 font-mono text-xs uppercase tracking-wider text-bone hover:border-coral focus:outline-none focus-visible:ring-2 focus-visible:ring-coral"
          >
            <SlidersHorizontal size={14} /> Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 rounded-full bg-coral px-1.5 text-[10px] font-bold text-ink-900">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>

        <nav className="flex gap-1" aria-label="Views">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => onTab(t.id)}
              aria-current={tab === t.id ? "page" : undefined}
              className={`rounded-md px-3 py-1.5 font-mono text-xs uppercase tracking-widest transition
                ${tab === t.id ? "bg-coral text-ink-900" : "text-moss hover:text-bone"}`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
