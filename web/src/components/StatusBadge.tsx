import type { Status, TicketType } from "../lib/types";

const STATUS_STYLE: Record<Status, string> = {
  on_sale: "text-ink-900 bg-coral",
  presale: "text-sky bg-sky/15 ring-1 ring-sky/40",
  sold_out: "text-moss bg-ink-600 line-through-none",
  announced: "text-amber bg-amber/15 ring-1 ring-amber/40",
  cancelled: "text-moss bg-ink-600",
  postponed: "text-amber bg-amber/15 ring-1 ring-amber/40"
};

const STATUS_LABEL: Record<Status, string> = {
  on_sale: "On sale",
  presale: "Presale",
  sold_out: "Sold out",
  announced: "Announced",
  cancelled: "Cancelled",
  postponed: "Postponed"
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-block rounded-sm px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${STATUS_STYLE[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}

// "primary, not resale" guarantee made visible (BUILD_SPEC §3.4).
export function TicketKindBadge({ kind }: { kind: TicketType | null }) {
  if (!kind) return null;
  const label =
    kind === "venue_primary" || kind === "api_primary"
      ? "Primary on-sale"
      : kind === "artist"
      ? "Artist listing"
      : "Venue page";
  return (
    <span className="font-mono text-[10px] uppercase tracking-widest text-moss">
      {label}
    </span>
  );
}
