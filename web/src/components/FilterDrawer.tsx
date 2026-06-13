import { X } from "lucide-react";
import type { Category, Region } from "../lib/types";
import { ALL_REGIONS, type Filters, type SaleState } from "../lib/filters";
import { CATEGORY_LABEL, REGION_LABEL } from "../lib/format";

const CATEGORIES: Category[] = ["music", "comedy", "arts"];
const SALE_OPTIONS: { value: SaleState; label: string }[] = [
  { value: "any", label: "Any" },
  { value: "on_sale", label: "On sale" },
  { value: "presale", label: "Presale" }
];

interface Props {
  open: boolean;
  filters: Filters;
  onChange: (f: Filters) => void;
  onClose: () => void;
}

export function FilterDrawer({ open, filters, onChange, onClose }: Props) {
  if (!open) return null;

  const toggle = <T,>(list: T[], value: T): T[] =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label="Filters">
      <div className="absolute inset-0 bg-ink-900/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative ml-auto flex h-full w-full max-w-sm flex-col gap-6 overflow-y-auto bg-ink-800 p-5 ring-1 ring-ink-600">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl tracking-wide">Filters</h2>
          <button onClick={onClose} aria-label="Close filters" className="rounded-full p-2 hover:bg-ink-700">
            <X size={18} />
          </button>
        </div>

        <Group label="Search">
          <input
            type="search"
            value={filters.query}
            onChange={(e) => onChange({ ...filters, query: e.target.value })}
            placeholder="Artist, venue…"
            className="w-full rounded-md border border-ink-600 bg-ink-900 px-3 py-2 text-sm text-bone placeholder:text-moss focus:border-coral focus:outline-none"
          />
        </Group>

        <Group label="Category">
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((c) => (
              <Chip
                key={c}
                active={filters.categories.includes(c)}
                onClick={() => onChange({ ...filters, categories: toggle(filters.categories, c) })}
              >
                {CATEGORY_LABEL[c]}
              </Chip>
            ))}
          </div>
        </Group>

        <Group label="Region">
          <div className="flex flex-wrap gap-2">
            {ALL_REGIONS.map((r: Region) => (
              <Chip
                key={r}
                active={filters.regions.includes(r)}
                onClick={() => onChange({ ...filters, regions: toggle(filters.regions, r) })}
              >
                {REGION_LABEL[r]}
              </Chip>
            ))}
          </div>
          <label className="mt-3 flex items-center gap-2 text-sm text-moss">
            <input
              type="checkbox"
              checked={filters.showExpandable}
              onChange={(e) => onChange({ ...filters, showExpandable: e.target.checked })}
              className="accent-coral"
            />
            Include Portland / Vancouver
          </label>
        </Group>

        <Group label="On-sale status">
          <div className="flex gap-2">
            {SALE_OPTIONS.map((o) => (
              <Chip key={o.value} active={filters.sale === o.value} onClick={() => onChange({ ...filters, sale: o.value })}>
                {o.label}
              </Chip>
            ))}
          </div>
        </Group>

        <Group label={`Max price${filters.priceCeiling != null ? `: $${filters.priceCeiling}` : ""}`}>
          <input
            type="range"
            min={0}
            max={200}
            step={5}
            value={filters.priceCeiling ?? 200}
            onChange={(e) =>
              onChange({ ...filters, priceCeiling: Number(e.target.value) >= 200 ? null : Number(e.target.value) })
            }
            className="w-full accent-coral"
          />
        </Group>

        <Group label="Only show">
          <div className="flex flex-col gap-2 text-sm">
            <Toggle label="All ages" checked={filters.allAges} onChange={(v) => onChange({ ...filters, allAges: v })} />
            <Toggle label="Free events" checked={filters.freeOnly} onChange={(v) => onChange({ ...filters, freeOnly: v })} />
            <Toggle label="Has ticket link" checked={filters.hasTickets} onChange={(v) => onChange({ ...filters, hasTickets: v })} />
          </div>
        </Group>
      </div>
    </div>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 font-mono text-[11px] uppercase tracking-widest text-moss">{label}</h3>
      {children}
    </div>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1 font-mono text-xs uppercase tracking-wider transition
        ${active ? "bg-coral text-ink-900" : "bg-ink-700 text-moss hover:text-bone"}`}
    >
      {children}
    </button>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 text-bone/90">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="accent-coral" />
      {label}
    </label>
  );
}
