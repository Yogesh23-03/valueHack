import {
  ActionsCompareResponse,
  ApiErrorBody,
  BillScanResult,
  BusinessResponse,
  CascadeRequest,
  CascadeResult,
  ForecastResponse,
  AttentionItem,
  PricingWhatIf,
  ScenarioParseResult,
  VendorCheckResult,
} from "./types";

/**
 * Base URL: NEXT_PUBLIC_API_BASE_URL is the documented setting;
 * NEXT_PUBLIC_API_URL is kept as a legacy fallback.
 */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export const API_BASE_URL = BASE_URL;

/** Friendly copy for each backend error code (docs/api_contract_engine.md). */
const FRIENDLY_MESSAGES: Record<string, string> = {
  INVALID_SHOCK: "That scenario type isn't supported. Pick a supplier delay, customer delay or cost spike.",
  UNKNOWN_SUPPLIER: "That supplier isn't in this business. Check the name and try again.",
  UNKNOWN_CUSTOMER: "That customer isn't in this business. Check the name and try again.",
  UNKNOWN_PRODUCT: "That product isn't in this business. Check the name and try again.",
  MAGNITUDE_OUT_OF_RANGE: "That amount is outside the allowed range for this scenario.",
  ELASTICITY_OUT_OF_RANGE: "Elasticity must be between -3 and 0 (it is negative by definition).",
  INVALID_INPUT: "The engine rejected one of the inputs.",
};

/** One error type for the whole app: parses the backend {code, message} body. */
export class ApiError extends Error {
  code: string;
  status: number;
  offline: boolean;

  constructor(message: string, opts: { code?: string; status?: number; offline?: boolean } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = opts.code ?? "UNKNOWN";
    this.status = opts.status ?? 0;
    this.offline = opts.offline ?? false;
  }

  get friendly(): string {
    if (this.offline) {
      return `Can't reach the engine at ${BASE_URL}. Start the backend: cd backend && uvicorn app.main:app --port 8000`;
    }
    return FRIENDLY_MESSAGES[this.code] ?? this.message;
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let body: ApiErrorBody | null = null;
  try {
    body = (await res.json()) as ApiErrorBody;
  } catch {
    body = null;
  }
  if (body && typeof body.code === "string") {
    return new ApiError(body.message || FRIENDLY_MESSAGES[body.code] || "Request failed", {
      code: body.code,
      status: res.status,
    });
  }
  return new ApiError(`Request failed (HTTP ${res.status})`, { code: "HTTP_ERROR", status: res.status });
}

async function request<T>(path: string, init: RequestInit = {}, retries = 1): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    // Network failure (backend down) — one quick retry, then surface offline.
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 600));
      return request<T>(path, init, retries - 1);
    }
    throw new ApiError("Network error", { code: "OFFLINE", offline: true });
  }
  if (!res.ok) {
    throw await parseError(res);
  }
  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}

function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const getBusiness = (signal?: AbortSignal) =>
  request<BusinessResponse>("/api/business", { signal });

export const getAttention = (signal?: AbortSignal) =>
  request<AttentionItem[]>("/api/attention", { signal });

export const simulateCascade = (params: CascadeRequest, signal?: AbortSignal) =>
  postJson<CascadeResult>("/api/simulate/cascade", params, signal);

export const compareActions = (delay: number, signal?: AbortSignal) =>
  postJson<ActionsCompareResponse>("/api/actions/compare", { delay }, signal);

export const parseScenario = (text: string, signal?: AbortSignal) =>
  postJson<ScenarioParseResult>("/api/scenario/parse", { text }, signal);

export const checkVendor = (input: { name?: string; gstin?: string; pan?: string }, signal?: AbortSignal) =>
  postJson<VendorCheckResult>("/api/vendor/check", input, signal);

export const scanBill = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return request<BillScanResult>("/api/bill/scan", { method: "POST", body: formData });
};

export const getPricingWhatIf = (
  params: { product_id: string; price_change_pct: number; elasticity?: number; horizon_days?: number },
  signal?: AbortSignal,
) => postJson<PricingWhatIf>("/api/pricing/whatif", params, signal);

export const getForecast = (signal?: AbortSignal) =>
  request<ForecastResponse>("/api/forecast", { signal });

export const getAnomalies = (signal?: AbortSignal) =>
  request<unknown[]>("/api/anomalies", { signal });

export const getReportPdf = async (): Promise<Blob> => {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/api/report`);
  } catch {
    throw new ApiError("Network error", { code: "OFFLINE", offline: true });
  }
  if (!res.ok) throw await parseError(res);
  return res.blob();
};
