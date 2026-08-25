const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "solsight_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let payload = body;
  if (form) {
    payload = form; // FormData sets its own content-type boundary
  } else if (body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch (_) {
      /* no-op */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

// ---------- auth ----------
export const login = (email, password) =>
  request("/auth/login", { method: "POST", body: { email, password }, auth: false });

export const register = (name, email, password) =>
  request("/auth/register", { method: "POST", body: { name, email, password }, auth: false });

export const me = () => request("/auth/me");

// ---------- panels ----------
export const listPanels = () => request("/panels");

export const createPanel = (panel) => request("/panels", { method: "POST", body: panel });

export const getPanel = (panelId) => request(`/panels/${panelId}`);

export const getPanelHistory = (panelId) => request(`/panels/${panelId}/history`);

export const getPanelPrediction = (panelId) => request(`/panels/${panelId}/prediction`);

// ---------- inspections ----------
export function uploadInspection({ panelId, voltage, current, temperature, image }) {
  const form = new FormData();
  form.append("panel_id", panelId);
  form.append("voltage", voltage);
  form.append("current", current);
  form.append("temperature", temperature);
  if (image) form.append("image", image);
  return request("/upload-inspection", { method: "POST", form });
}

export function predictDefect({ panelId, voltage, current, temperature, image }) {
  const form = new FormData();
  form.append("panel_id", panelId);
  form.append("voltage", voltage);
  form.append("current", current);
  form.append("temperature", temperature);
  if (image) form.append("image", image);
  return request("/predict-defect", { method: "POST", form });
}
