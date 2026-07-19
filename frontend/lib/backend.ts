// Shared server-side helpers for talking to the FastAPI backend.
// Keep this the single place that knows the backend origin + session cookie name.

export const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

export const SESSION_COOKIE_NAME = "session";

export interface ProductSearchItem {
  id: string;
  title: string;
  canonical_key: string;
}

export interface ProductSearchResponse {
  items: ProductSearchItem[];
}

export interface Offer {
  offer_id: string;
  store: string;
  url: string;
  price: number;
  currency: string;
  stock_status: string | null;
  is_real_data: boolean;
  observed_at: string | null;
}

export interface PriceHistoryOk {
  status: "OK";
  latest_price: string;
  min_price: string;
  average_price: string;
  max_price: string;
  trend: "UP" | "DOWN" | "FLAT";
  points: { price: string }[];
}

export interface PriceHistoryInsufficient {
  status: "INSUFFICIENT_DATA";
  reason: string;
}

export type PriceHistory = PriceHistoryOk | PriceHistoryInsufficient;

export interface DealScore {
  score: number;
  decision: "WATCH" | "BUY" | "SKIP" | string;
  reasons: string[];
}

export interface DealSignal {
  offer_id: string;
  has_price_data: boolean;
  lowest_prices: Record<string, unknown>;
  deal_score: DealScore;
  recommendation: string;
  message: string;
}

export interface ProductDetail {
  product: ProductSearchItem;
  offers: Offer[];
  price_history: PriceHistory;
  deal_signal: DealSignal | null;
}

export interface IdentityUser {
  id: string;
  email: string;
  display_name: string | null;
  preferred_language?: string;
  preferred_currency?: string;
  preferred_country?: string;
}

export interface WatchlistItem {
  id: string;
  user_id: string;
  product_key: string;
  query: string;
  target_price: number | null;
  marketplaces: string[] | null;
  channels: string[] | null;
  status: "ACTIVE" | "INACTIVE" | string;
  last_evaluation: unknown;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DealFeedItem {
  canonical_product_key: string;
  product_id: string;
  product_name: string;
  offer_id: string;
  source_id: string;
  marketplace: string;
  price: number;
  effective_price: number;
  currency: string;
  confidence_score: number;
  opportunity_score: number;
  observed_discount_pct: number;
  deal_decision: "BUY" | "WATCH" | "SKIP" | string | null;
  deal_message: string;
  is_real_data: boolean;
  personalized_score: number;
  personalization_reasons: string[];
}

export interface DealFeedResponse {
  feed_count: number;
  total_eligible_count: number;
  items: DealFeedItem[];
  metadata: Record<string, unknown>;
}
