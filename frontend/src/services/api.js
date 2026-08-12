import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export const checkHealth = () => api.get("/health");
export const prescribeShipment = (data) => api.post("/prescribe", data);
export const createShipment = (data) => api.post("/shipments", data);
export const createDecision = (data) => api.post("/decisions", data);
export const getDecisions = () => api.get("/decisions");
export const createOutcome = (data) => api.post("/outcomes", data);
export const evaluateDecision = (decisionId) => api.post(`/evaluate/${decisionId}`);
export const getAnalytics = () => api.get("/analytics");
export const getRetrainingStatus = () => api.get("/retraining/status");
export const runRetraining = () => api.post("/retraining/run");

export function apiErrorMessage(error, fallback = "The request could not be completed.") {
  if (!error.response) return "Cannot reach the backend. Confirm that FastAPI is running on port 8000.";
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
  return fallback;
}
