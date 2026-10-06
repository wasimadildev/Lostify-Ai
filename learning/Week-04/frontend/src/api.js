// Same-origin by default (the production build is served by FastAPI itself).
// Dev mode (Vite) overrides this via frontend/.env.local -> http://localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || '';

export const apiBase = API_BASE;

/** Turn a stored image_path (e.g. "data/pets/PETS-01.jpg") into a browser URL. */
export function assetUrl(imagePath) {
  if (!imagePath) return null;
  return `${API_BASE}/static/${imagePath.replace(/^data\//, '')}`;
}

/** POST /search — upload a report (image + text + filters) and get ranked matches. */
export async function searchReport(payload) {
  const form = new FormData();
  if (payload.image) form.append('image', payload.image);
  if (payload.text) form.append('text', payload.text);
  if (payload.queryType) form.append('query_type', payload.queryType);
  if (payload.category) form.append('category', payload.category);
  if (payload.location) form.append('location', payload.location);
  form.append('top_k', String(payload.topK ?? 5));

  const res = await fetch(`${API_BASE}/search`, { method: 'POST', body: form });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.detail || `Server error (${res.status})`;
    throw new Error(message);
  }
  return data;
}

/** POST /analyze — extract YOLO, OCR, and face features without searching. */
export async function analyzeImage(image) {
  const form = new FormData();
  form.append('image', image);
  const res = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: form });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail || `Server error (${res.status})`);
  return data;
}

/** GET /cases — all stored dataset reports for the gallery. */
export async function fetchCases(limit = 200) {
  const res = await fetch(`${API_BASE}/cases?limit=${limit}`);
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Server error (${res.status})`);
  }
  return data;
}

/** GET /health — service + index status. */
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`health check failed (${res.status})`);
  return res.json();
}

/** POST /reports — save a brand-new lost report (photo + details) to the database. */
export async function createReport(payload) {
  const form = new FormData();
  if (payload.image) form.append('image', payload.image);
  if (payload.title) form.append('title', payload.title);
  if (payload.description) form.append('description', payload.description);
  form.append('case_type', payload.caseType);
  if (payload.category) form.append('category', payload.category);
  if (payload.location) form.append('location', payload.location);
  if (payload.latitude) form.append('latitude', String(payload.latitude));
  if (payload.longitude) form.append('longitude', String(payload.longitude));
  if (payload.dateLost) form.append('date_lost', payload.dateLost);

  const res = await fetch(`${API_BASE}/reports`, { method: 'POST', body: form });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.detail || `Server error (${res.status})`;
    throw new Error(message);
  }
  return data; // { message, case }
}

/** GET /reports — every report in the database (dataset seed + user submissions). */
export async function fetchReports(limit = 500) {
  const res = await fetch(`${API_BASE}/reports?limit=${limit}`);
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Server error (${res.status})`);
  }
  return data;
}