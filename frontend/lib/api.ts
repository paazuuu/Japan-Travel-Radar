// Central API helpers + types shared across pages.
// Server components use BACKEND_URL (docker-internal, e.g. http://backend:8000).
// Client components use NEXT_PUBLIC_BACKEND_URL (browser-reachable, e.g. localhost:8000).

export const serverBase = () => process.env.BACKEND_URL || "http://localhost:8000";
export const browserBase = () =>
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface Spot {
  id: string;
  name: string;
  name_en?: string | null;
  description?: string | null;
  category?: string | null;
  subcategory?: string | null;
  best_season?: string | null;
  recommended_stay_minutes?: number | null;
  estimated_budget_min?: number | null;
  estimated_budget_max?: number | null;
  access_text?: string | null;
  official_url?: string | null;
  source_url?: string | null;
  status: string;
  lat?: number | null;
  lng?: number | null;
  distance_m?: number | null;
  ai_summary?: string | null;
  tags: string[];
  travel_types: string[];
  ai_confidence?: number | null;
  trend_score?: number | null;
}

export interface RankingItem {
  id: string;
  name: string;
  category?: string | null;
  lat?: number | null;
  lng?: number | null;
  ai_summary?: string | null;
  ai_confidence?: number | null;
  trend_score: number;
  growth_score: number;
  engagement_score: number;
  recency_score: number;
  seasonality_score: number;
  source_diversity_score: number;
  novelty_score: number;
  data_confidence_score: number;
  is_reference: boolean;
  score_date: string;
}

export interface Restaurant {
  id: string;
  name: string;
  category?: string | null;
  price_min?: number | null;
  price_max?: number | null;
  fish: boolean;
  meat: boolean;
  vegetarian: boolean;
  vegan: boolean;
  local_specialty: boolean;
  official_url?: string | null;
  source_url?: string | null;
  lat?: number | null;
  lng?: number | null;
  distance_m?: number | null;
}

async function getJSON<T>(url: string, headers?: Record<string, string>): Promise<T | null> {
  try {
    const res = await fetch(url, { cache: "no-store", headers });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// Admin key is server-side only (never exposed to the browser).
const adminHeaders = () => {
  const key = process.env.ADMIN_API_KEY;
  return key ? { "X-Admin-Key": key } : undefined;
};

// ---- server-side fetchers ----
export const api = {
  rankings: (kind: string, params = "") =>
    getJSON<RankingItem[]>(`${serverBase()}/api/v1/rankings/${kind}?limit=12${params}`),
  spots: (params = "") => getJSON<Spot[]>(`${serverBase()}/api/v1/spots?${params}`),
  spot: (id: string) => getJSON<Spot>(`${serverBase()}/api/v1/spots/${id}`),
  nearbySpots: (lat: number, lng: number, radius = 8000) =>
    getJSON<Spot[]>(`${serverBase()}/api/v1/spots/nearby?lat=${lat}&lng=${lng}&radius=${radius}`),
  nearbyRestaurants: (lat: number, lng: number, extra = "") =>
    getJSON<Restaurant[]>(`${serverBase()}/api/v1/restaurants/nearby?lat=${lat}&lng=${lng}${extra}`),
  restaurants: (params = "") => getJSON<Restaurant[]>(`${serverBase()}/api/v1/restaurants?${params}`),
  admin: <T>(path: string) => getJSON<T>(`${serverBase()}/api/v1/admin/${path}`, adminHeaders()),
};

export const yen = (n?: number | null) => (n == null ? "—" : `¥${n.toLocaleString()}`);
