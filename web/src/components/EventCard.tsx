import { Ticket, MapPin, Clock } from "lucide-react";
import type { EventRow } from "../lib/types";
import { showDate, showTime, showTimeLabel, priceLabel, posterFor } from "../lib/format";
import { StatusBadge, TicketKindBadge } from "./StatusBadge";

interface Props {
  event: EventRow;
  isNew: boolean;
  onOpen: (e: EventRow) => void;
}

export function EventCard({ event, isNew, onOpen }: Props) {
  const doors = showTime(event.doors_at);
  const show = showTimeLabel(event.starts_at);

  return (
    <article
      className={`group relative flex overflow-hidden rounded-lg bg-ink-800 shadow-flyer ring-1 transition
        ${isNew ? "ring-coral/60" : "ring-ink-600 hover:ring-moss/50"}`}
    >
      {isNew && (
        <span className="absolute left-0 top-3 z-10 rounded-r-sm bg-coral px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-widest text-ink-900">
          New
        </span>
      )}

      {/* Poster — the hero of each flyer. */}
      <button
        onClick={() => onOpen(event)}
        aria-label={`Open ${event.headliner ?? event.title}`}
        className="grain relative hidden w-28 shrink-0 sm:block md:w-36"
      >
        <img
          src={posterFor(event)}
          alt=""
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover opacity-90 transition duration-500 group-hover:scale-[1.04]"
        />
      </button>

      {/* Body */}
      <div className="flex min-w-0 flex-1 flex-col justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-coral">
            <span>{showDate(event)}</span>
            <span className="text-ink-600">/</span>
            <span className="text-moss">{event.category}</span>
          </div>
          <button onClick={() => onOpen(event)} className="block text-left">
            <h3 className="font-display text-2xl leading-[0.95] tracking-wide text-bone md:text-3xl">
              {event.headliner ?? event.title}
            </h3>
          </button>
          {event.lineup && event.lineup.length > 0 && (
            <p className="mt-1 truncate text-sm text-moss">
              with {event.lineup.join(", ")}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-moss">
            <span className="inline-flex items-center gap-1">
              <MapPin size={12} /> {event.venue_name}
            </span>
            {(doors || show) && (
              <span className="inline-flex items-center gap-1 font-mono">
                <Clock size={12} />
                {doors && <>doors {doors}</>}
                {doors && show && <span className="text-ink-600">·</span>}
                {show && <>{show === "Time TBA" ? show : <>show {show}</>}</>}
              </span>
            )}
            {event.is_all_ages === true && (
              <span className="rounded-sm bg-ink-600 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider">
                All ages
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Ticket stub */}
      <div className="stub-edge flex w-28 shrink-0 flex-col items-center justify-center gap-2 bg-ink-700 p-3 text-center md:w-32">
        <StatusBadge status={event.status} />
        <div className="font-mono text-lg font-bold text-bone">{priceLabel(event)}</div>
        {event.ticket_url ? (
          <a
            href={event.ticket_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex w-full items-center justify-center gap-1 rounded-sm bg-coral px-2 py-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-ink-900 transition hover:brightness-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-bone"
          >
            <Ticket size={12} /> Tickets
          </a>
        ) : (
          <span className="font-mono text-[10px] uppercase tracking-wider text-moss">
            No link
          </span>
        )}
        <TicketKindBadge kind={event.ticket_url_type} />
      </div>
    </article>
  );
}
