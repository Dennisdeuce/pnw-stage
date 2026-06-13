import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!url || !anonKey) {
  // Surfaced in the UI as a config error rather than a blank screen.
  console.error(
    "Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY. See web/.env.example."
  );
}

export const supabase = createClient(url ?? "", anonKey ?? "", {
  auth: { persistSession: false }
});

export const isConfigured = Boolean(url && anonKey);
