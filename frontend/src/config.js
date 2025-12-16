import axios from "axios";

// In production (Vercel), we use relative paths like "/api/..." which get rewritten.
// In development, we fallback to localhost:8000.
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "development" ? "http://127.0.0.1:8000" : "");

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export default api;
export { API_BASE_URL };
