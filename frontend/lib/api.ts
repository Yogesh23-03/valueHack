const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 1): Promise<unknown> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const text = await res.text();
    return text ? JSON.parse(text) : {};
  } catch (error) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, 800));
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}

export const getBusiness = () => fetchWithRetry(`${API}/api/business`);
export const getAttention = () => fetchWithRetry(`${API}/api/attention`);
export const simulateCascade = (params: Record<string, unknown>) => fetchWithRetry(`${API}/api/simulate/cascade`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(params),
});
export const compareActions = (delay: number) => fetchWithRetry(`${API}/api/actions/compare`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ delay }),
});
export const parseScenario = (text: string) => fetchWithRetry(`${API}/api/scenario/parse`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text }),
});
export const checkVendor = (input: Record<string, string>) => fetchWithRetry(`${API}/api/vendor/check`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(input),
});
export const scanBill = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return fetchWithRetry(`${API}/api/bill/scan`, {
    method: "POST",
    body: formData,
  });
};
export const getForecast = () => fetchWithRetry(`${API}/api/forecast`);
export const getAnomalies = () => fetchWithRetry(`${API}/api/anomalies`);

export const getReport = async () => {
  const res = await fetch(`${API}/api/report`);
  if (!res.ok) throw new Error("Failed to generate report");
  return await res.blob();
};
