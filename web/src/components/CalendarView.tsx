import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import multiMonthPlugin from "@fullcalendar/multimonth";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventInput, EventClickArg } from "@fullcalendar/core";
import type { EventRow } from "../lib/types";
import { pacificNaiveISO, isPacificMidnight } from "../lib/format";

const CATEGORY_COLOR: Record<string, string> = {
  music: "#FF5A3C",
  comedy: "#F5B544",
  arts: "#4DA8FF",
  other: "#7E8C82"
};

export function CalendarView({
  events,
  onOpen
}: {
  events: EventRow[];
  onOpen: (e: EventRow) => void;
}) {
  // Date-only listings (no start_at, or exactly midnight Pacific) are all-day.
  // Timed events are passed as an offset-less Pacific wall-clock ISO so
  // FullCalendar's default 'local' zone renders the Pacific time verbatim and
  // never shifts an event onto the wrong day for a non-Pacific viewer.
  const fcEvents: EventInput[] = events.map((e) => {
    const allDay = !e.starts_at || isPacificMidnight(e.starts_at);
    return {
      id: String(e.id),
      title: `${e.headliner ?? e.title} · ${e.venue_name}`,
      start: allDay ? e.date_local : pacificNaiveISO(e.starts_at as string),
      allDay,
      borderColor: CATEGORY_COLOR[e.category] ?? "#7E8C82",
      extendedProps: { row: e }
    };
  });

  return (
    <div className="rounded-lg border border-ink-600 bg-ink-800 p-3 md:p-4">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, multiMonthPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "timeGridWeek,dayGridMonth,multiMonthYear"
        }}
        buttonText={{ today: "Today", week: "Week", month: "Month", year: "Year" }}
        views={{ multiMonthYear: { type: "multiMonth", duration: { months: 12 } } }}
        height="auto"
        eventTimeFormat={{ hour: "numeric", minute: "2-digit", meridiem: "short" }}
        events={fcEvents}
        eventClick={(arg: EventClickArg) => {
          arg.jsEvent.preventDefault();
          onOpen(arg.event.extendedProps.row as EventRow);
        }}
        eventDisplay="block"
        dayMaxEvents={3}
        firstDay={0}
      />
    </div>
  );
}
