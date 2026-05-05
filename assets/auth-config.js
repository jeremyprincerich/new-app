// Supabase project credentials — see db/SETUP.md for how to fill these in.
// The `anon` key is safe to commit publicly; security comes from the RLS
// policies in db/schema.sql, not from the key being secret.
//
// After creating the Supabase project (one-time), paste the values from
// Supabase Studio → Settings → API into the placeholders below.

export const SUPABASE_URL      = "https://niakazcqiftvgkiazwwr.supabase.co";
export const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5pYWthemNxaWZ0dmdraWF6d3dyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5NjE0MDQsImV4cCI6MjA5MzUzNzQwNH0.7fO5uDJWVv-bc5o19tKJUH3DwZaYKPjLz7TFLnd5yO4";

// Returns true once the placeholders have been replaced with real values.
export function isAuthConfigured() {
  return !SUPABASE_URL.includes("YOUR_PROJECT_ID")
      && !SUPABASE_ANON_KEY.includes("YOUR_ANON_PUBLIC_KEY")
      && SUPABASE_URL.startsWith("https://")
      && SUPABASE_ANON_KEY.length > 40;
}
