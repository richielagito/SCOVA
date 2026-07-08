const supabaseUrl = window.SUPABASE_URL || "https://example.supabase.co";
const supabaseKey = window.SUPABASE_PUBLISHABLE_KEY || "pubkey-placeholder";
export const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);
