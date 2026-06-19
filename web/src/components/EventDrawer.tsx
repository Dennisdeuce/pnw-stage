import { X, Ticket, ExternalLink, MapPin, Clock, Calendar } from "lucide-react";
import { useEffect } from "react";
import type { EventRow } from "../lib/types";
import { showDate, showTime, showTimeLabel, priceLabel, posterFor } from "../lib/format";
import { StatusBadge, TicketKindBadge } from "./StatusBadge";

export function EventDrawer({ event, onClose }: { event: EventRow | null; onClose: () => void }) {
  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => ev.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!event) return null;
  const doors = showTime(event.doors_at);
  const show = showTimeLabel(event.starts_at);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-ink-900/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-md flex-col overflow-y-auto bg-ink-800 shadow-2xl ring-1 ring-ink-600">
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-3 top-3 z-10 rounded-full bg-ink-900/70 p-2 text-bone hover:bg-coral hover:text-ink-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-bone"
        >
          <X size={18} />
        </button>

        <div className="grain relative aspect-[4/3] w-full shrink-0">
          <img src={posterFor(event)} alt="" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-ink-800 via-ink-800/30 to-transparent" />
        </div>

        <div className="flex flex-1 flex-col gap-4 p-5">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-coral">
            {event.category} <span className="text-ink-600">/</span>
            <StatusBadge status={event.status} />
          </div>
          <h2 className="font-display text-4xl leading-[0.9] tracking-wide text-bone">
            {event.headliner ?? event.title}
          </h2>
          {event.lineup && event.lineup.length > 0 && (
            <p className="text-moss">with {event.lineup.join(", ")}</p>
          )}

          <dl className="grid gap-2 border-y border-ink-600 py-4 text-sm">
            <Row icon={<Calendar size={14} />} label={showDate(event)} />
            <Row icon={<MapPin size={14} />} label={`${event.venue_name}${event.city ? `, ${event.city}` : ""}`} />
            {(doors || show) && (
              <Row
                icon={<Clock size={14} />}
                label={[doors && `Doors ${doors}`, show && (show === "Time TBA" ? show : `Show ${show}`)]
                  .filter(Boolean)
                  .join(" · ")}
              />
            )}
            <Row icon={<Ticket size={14} />} label={priceLabel(event)} />
          </dl>

          {event.description && (
            <p className="text-sm leading-relaxed text-bone/80">{event.description}</p>
          )}

          <div className="mt-auto flex flex-col gap-2 pt-2">
            {event.ticket_url ? (
              <a
                href={event.ticket_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-coral px-4 py-3 font-mono text-sm font-bold uppercase tracking-wider text-ink-900 transition hover:brightness-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-bone"
              >
                <Ticket size={16} /> Get tickets
              </a>
            ) : (
              <span className="text-center font-mono text-xs uppercase tracking-wider text-moss">
                No ticket link yet
              </span>
            )}
            <div className="flex items-center justify-between">
              <TicketKindBadge kind={event.ticket_url_type} />
              {event.source_url && (
                <a
                  href={event.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-moss hover:text-bone"
                >
                  Event page <ExternalLink size={11} />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2 text-bone/90">
      <span className="text-coral">{icon}</span>
      <dd className="font-mono">{label}</dd>
    </div>
  );
}
