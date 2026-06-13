import { Plus, Check, Sparkles } from "lucide-react";
import type { EventRow } from "../lib/types";
import { EventCard } from "./EventCard";

interface Props {
  events: EventRow[];
  isNew: (e: EventRow) => boolean;
  onOpen: (e: EventRow) => void;
  showExpandable: boolean;
  onToggleExpandable: () => void;
  onMarkSeen: () => void;
}

export function FeedView({ events, isNew, onOpen, showExpandable, onToggleExpandable, onMarkSeen }: Props) {
  const fresh = events.filter(isNew);
  const rest = events.filter((e) => !isNew(e));

  return (
    <div className="flex flex-col gap-8">
      {!showExpandable && (
        <button
          onClick={onToggleExpandable}
          className="flex items-center justify-center gap-2 rounded-lg border border-dashed border-ink-600 bg-ink-800/50 px-4 py-3 font-mono text-xs uppercase tracking-widest text-moss transition hover:border-coral hover:text-bone"
        >
          <Plus size={14} /> Show Portland / Vancouver WA / Vancouver BC
        </button>
      )}

      {fresh.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-display text-xl tracking-wide text-bone">
              <Sparkles size={18} className="text-coral" />
              New since your last visit
              <span className="font-mono text-base text-coral">({fresh.length})</span>
            </h2>
            <button
              onClick={onMarkSeen}
              className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-moss hover:text-bone"
            >
              <Check size={12} /> Mark all seen
            </button>
          </div>
          <div className="grid gap-3" data-testid="new-section">
            {fresh.map((e) => (
              <EventCard key={e.id} event={e} isNew onOpen={onOpen} />
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-widest text-moss">
          {fresh.length > 0 ? "Everything else" : "Upcoming shows"} · {rest.length}
        </h2>
        <div className="grid gap-3">
          {rest.map((e) => (
            <EventCard key={e.id} event={e} isNew={false} onOpen={onOpen} />
          ))}
        </div>
        {events.length === 0 && (
          <p className="rounded-lg border border-ink-600 bg-ink-800 p-8 text-center text-moss">
            No shows match these filters. Try widening the date range or clearing a filter.
          </p>
        )}
      </section>
    </div>
  );
}
