import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import multiMonthPlugin from "@fullcalendar/multimonth";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventInput, EventClickArg } from "@fullcalendar/core";
import type { EventRow } from "../lib/types";

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
  const fcEvents: EventInput[] = events.map((e) => ({
    id: String(e.id),
    title: `${e.headliner ?? e.title} · ${e.venue_name}`,
    start: e.starts_at ?? e.date_local,
    allDay: !e.starts_at,
    borderColor: CATEGORY_COLOR[e.category] ?? "#7E8C82",
    extendedProps: { row: e }
  }));

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
