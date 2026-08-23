// Client-side persistence for PWA features (favorites, recently viewed, saved plans).
"use client";

const TOKEN = "jtr:token";
const FAV = "jtr:favorites";
const RECENT = "jtr:recent";
const PLANS = "jtr:plans";
const MAX_RECENT = 20;

export interface SavedSpot { id: string; name: string; }
export interface SavedPlan { id: string; origin: string; summary?: string; at: number; }

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function write<T>(key: string, value: T) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota / private mode */
  }
}

// ---- auth token (JWT) ----
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN);
  } catch {
    return null;
  }
}
export function setToken(token: string) {
  try {
    localStorage.setItem(TOKEN, token);
  } catch {
    /* ignore */
  }
}
export function clearToken() {
  try {
    localStorage.removeItem(TOKEN);
  } catch {
    /* ignore */
  }
}

// ---- favorites ----
export const getFavorites = () => read<SavedSpot[]>(FAV, []);
export const isFavorite = (id: string) => getFavorites().some((s) => s.id === id);
export function toggleFavorite(spot: SavedSpot): boolean {
  const list = getFavorites();
  const exists = list.some((s) => s.id === spot.id);
  const next = exists ? list.filter((s) => s.id !== spot.id) : [spot, ...list];
  write(FAV, next);
  return !exists;
}

// ---- recently viewed ----
export const getRecent = () => read<SavedSpot[]>(RECENT, []);
export function pushRecent(spot: SavedSpot) {
  const list = getRecent().filter((s) => s.id !== spot.id);
  write(RECENT, [spot, ...list].slice(0, MAX_RECENT));
}

// ---- saved plans ----
export const getPlans = () => read<SavedPlan[]>(PLANS, []);
export function savePlan(plan: SavedPlan) {
  const list = getPlans().filter((p) => p.id !== plan.id);
  write(PLANS, [plan, ...list].slice(0, 50));
}
export function removePlan(id: string) {
  write(PLANS, getPlans().filter((p) => p.id !== id));
}
