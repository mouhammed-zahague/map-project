/* ============================================================
   Supabase Client – Green Campus Alert
   Loaded after the Supabase UMD CDN script, which exposes the
   global `supabase` namespace (supabase.createClient).
   ============================================================ */

// ──────────────────────────────────────────────────────────────
// 🔧 STEP 1 – Paste your Supabase Project URL here
//    Supabase Dashboard → Settings → API → Project URL
//    (base URL only, no /rest/v1 suffix)
// ──────────────────────────────────────────────────────────────
const SUPABASE_URL = "https://jxzldmnzlnbzvamxwuhy.supabase.co";

// ──────────────────────────────────────────────────────────────
// 🔑 STEP 2 – Paste your anon / public key here
//    Supabase Dashboard → Settings → API → anon / public
// ──────────────────────────────────────────────────────────────
const SUPABASE_PUBLIC_KEY = "sb_publishable_9Vgd83AKyo_xKjvAJ4_gvg_HZkx51fY";

// ──────────────────────────────────────────────────────────────
// Expose the client as a global so auth.js (and other scripts)
// can use it without a bundler / ES-module setup.
// Access it anywhere with:  supabaseClient.auth.signIn(...)
// ──────────────────────────────────────────────────────────────
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_PUBLIC_KEY);
