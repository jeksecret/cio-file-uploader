import { API_BASE } from "../config";

export async function fetchWithAuth(path, options = {}, getAccessToken) {
  const token = await getAccessToken();
  const isFormData = options.body instanceof FormData;

  const headers = {
    ...(options.headers || {}),
    Authorization: token ? `Bearer ${token}` : "",
  };
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const error = new Error(body.detail || `Request failed (${res.status})`);
    error.status = res.status;
    throw error;
  }

  return res.json();
}