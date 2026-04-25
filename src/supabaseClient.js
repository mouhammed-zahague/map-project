import { createClient } from "@supabase/supabase-js";

// ──────────────────────────────────────────────────────────────
// 🔧 STEP 1 – Paste your Supabase Project URL here
//    Find it in: Supabase Dashboard → Settings → API → Project URL
// ──────────────────────────────────────────────────────────────
const SUPABASE_URL = "https://jxzldmnzlnbzvamxwuhy.supabase.co/rest/v1/";

// ──────────────────────────────────────────────────────────────
// 🔑 STEP 2 – Paste your Supabase Public (anon) Key here
//    Find it in: Supabase Dashboard → Settings → API → anon / public
// ──────────────────────────────────────────────────────────────
const SUPABASE_PUBLIC_KEY = "sb_publishable_9Vgd83AKyo_xKjvAJ4_gvg_HZkx51fY";

// ──────────────────────────────────────────────────────────────
// Supabase client – import this wherever you need database access
// Usage: import { supabase } from "../src/supabaseClient.js";
// ──────────────────────────────────────────────────────────────
export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLIC_KEY);
