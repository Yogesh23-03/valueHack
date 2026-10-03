/**
 * TypeScript types matching the real backend responses.
 * Source of truth: docs/api_contract_engine.md and the captured samples in
 * docs/samples/ (all shapes below were verified against live output).
 */

export type ScenarioType =
  | "supplier_delay"
  | "customer_delay"
  | "cost_spike"
  | "demand_shock";

export interface ScenarioShock {
  type: string;
  target: string;
  magnitude: number;
  duration_days?: number | null;
}

export interface CascadeRequest {
  delay?: number;
  horizon?: number;
  ext_a?: number;
  ext_c?: number;
  early_discount?: number;
  alt_supplier?: boolean;
  alt_fails?: boolean;
  cost_spike_pct?: number;
  customer_late_days?: number;
  demand_band_pct?: number;
  scenario?: ScenarioShock | null;
}

export interface FailedPayment {
  name: string;
  day: number;
}

export type StockPoint = Record<string, number>;

export interface ScenarioInfo {
  type: string;
  target: string;
  target_name?: string;
  magnitude: number;
  label?: string;
  switch_vendor?: boolean;
  vendor_fails?: boolean;
  early_discount_pct?: number;
  invoice_extension_days?: number;
  payable_extension_days?: number;
  demand_multiplier?: number;
}

export interface CascadeSummary {
  stockout_day: number | null;
  lost_sales_inr: number;
  lost_sales_all_products_inr: number;
  first_negative_day: number | null;
  lowest_cash_inr: number;
  lowest_cash_day: number | null;
  end_cash_inr: number;
  failed_payments_count: number;
  order_delay_days: number;
  customer_payment_day: number | null;
}

export type ChainStatus = "triggered" | "avoided" | "not_reached";

export interface CascadeStep {
  step: string;
  status: ChainStatus;
  day: number | null;
  title: string;
  detail: string;
}

export type EventSeverity = "info" | "warning" | "critical";

export interface SimEvent {
  id: string;
  day: number;
  type: string;
  entity: string;
  values: Record<string, number | string | null>;
  cause_ids: string[];
  severity: EventSeverity;
}

export interface Explanation {
  metric_id: string;
  label: string;
  value: number | null;
  unit: string; // "inr" | "day" | "count"
  sentence: string;
  event_ids: string[];
}

export type AssumptionSource = "demo_data" | "assumed" | "user";

export interface Assumption {
  id: string;
  text: string;
  value: number | null;
  unit: string | null;
  editable: boolean;
  source: AssumptionSource;
}

export interface RangeMetric {
  min: number;
  base: number;
  max: number;
  min_case: string;
  max_case: string;
}

export interface RangeRun {
  case: string;
  demand_multiplier: number;
  metrics: Record<string, number>;
}

export interface Ranges {
  runs: RangeRun[];
  metrics: Record<string, RangeMetric>;
  range_note: string;
}

export interface CascadeMeta {
  engine_version: string;
  horizon_days: number;
  deterministic: boolean;
  shock_type: string;
}

export interface CascadeResult {
  // Legacy fields (frozen by the golden tests)
  stockout: number | null;
  lost_rev: number;
  first_negative_day: number | null;
  min_cash: number;
  min_day: number;
  failed: FailedPayment[];
  delivered: boolean;
  end_cash: number;
  cash_timeline: number[];
  stock_timeline: StockPoint[];
  // New engine fields
  scenario?: ScenarioInfo;
  summary?: CascadeSummary;
  cascade_chain?: CascadeStep[];
  events?: SimEvent[];
  timeline?: { cash: number[]; stock: StockPoint[] };
  explanations?: Explanation[];
  assumptions?: Assumption[];
  ranges?: Ranges;
  meta?: CascadeMeta;
}

export interface RiskFactor {
  points: number;
  reason: string;
}

export interface ActionRisk {
  level: string; // "Low" | "Medium" | "High"
  score: number;
  factors: RiskFactor[];
}

export interface VendorRisk {
  score: number;
  band: string; // "green" | "amber" | "red" | "unknown"
  reasons: string[];
}

export interface DeltaEntry {
  base: number;
  action: number;
  delta: number;
}

export interface ActionCompareResult extends CascadeResult {
  id: string;
  label: string;
  delta_vs_do_nothing: Record<string, DeltaEntry>;
  tradeoff: string;
  affordable: boolean;
  shortfall_inr: number | null;
  requires_counterparty_agreement: boolean;
  risk: ActionRisk;
  suggested: boolean;
  suggested_reason: string;
  vendor_risk?: VendorRisk | null;
  exposure_inr?: number | null;
  vendor_fails_result?: CascadeResult | null;
}

export type ActionsCompareResponse = Record<string, ActionCompareResult>;

export interface ProductShare {
  name: string;
  share_pct: number;
}

export interface ProductDependency {
  product: string;
  product_id: string;
  suppliers: ProductShare[];
}

export interface SupplierDependency {
  supplier: string;
  supplier_id: string;
  stock_value_share_pct: number;
  purchase_value_share_pct: number;
  concentration: string; // "high" | "medium" | "low"
}

export interface StockCoverRow {
  product: string;
  product_id: string;
  stock_units: number;
  daily_demand: number;
  cover_days: number;
  next_restock_day: number;
  days_to_stockout: number;
  status: string; // "safe" | "watch" | "critical"
}

export interface AttentionInput {
  kind: string;
  entity: string;
  severity: string;
  day: number | null;
  evidence: string;
}

export interface AnalyticsBlock {
  dependency_shares: {
    products: ProductDependency[];
    supplier_dependency: SupplierDependency[];
  };
  stock_cover: StockCoverRow[];
  attention_inputs: AttentionInput[];
}

export interface BusinessResponse {
  name: string;
  cash: number;
  analytics: AnalyticsBlock;
}

export interface ElasticityBand {
  low: number;
  base: number;
  high: number;
}

export interface PricingCurvePoint {
  price_change_pct: number;
  profit_inr: ElasticityBand;
  demand_multiplier: ElasticityBand;
}

export interface PricingWhatIf {
  product: string;
  product_id: string;
  current_price_inr: number;
  new_price_inr: number;
  price_change_pct: number;
  elasticity: ElasticityBand;
  demand_multiplier: ElasticityBand;
  unit_margin_inr: number;
  new_unit_margin_inr: number;
  profit_inr: ElasticityBand;
  profit_change_inr: ElasticityBand;
  breakeven_demand_drop_pct: number;
  horizon_days: number;
  curve: PricingCurvePoint[];
  sentence: string;
  assumptions: Assumption[];
}

export interface ScenarioParseResult {
  type: string;
  target: string;
  days: number;
}

export interface VendorCheckResult {
  score: number;
  badge: string; // "green" | "amber" | "red"
  reasons: string[];
}

export interface AttentionItem {
  id: number;
  text: string;
  icon: string;
}

export interface ForecastResponse {
  forecast: unknown[];
  mape: number;
}

export interface BillScanResult {
  supplier: string;
  items: Array<{ name: string; qty: number; unit_price: number; tax_rate: number }>;
  due_date: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}
