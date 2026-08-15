/* Supabase project connection — the anon key below is meant to be public (it sits in a public
   GitHub repo on purpose); Row Level Security in supabase/schema.sql is the real security
   boundary, not this key's secrecy. See supabase/schema.sql for the RLS policies, and make sure
   self-signup is disabled in the Supabase dashboard (Authentication -> Providers -> Email) —
   without that, anyone could register an account and satisfy the "authenticated" write policies.

   TODO: replace both placeholders once the Supabase project exists (Project Settings -> API). */
const SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co";
const SUPABASE_ANON_KEY = "YOUR-ANON-PUBLIC-KEY";
