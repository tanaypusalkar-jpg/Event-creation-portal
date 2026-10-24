const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { credentials: "include", ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map(x => x.msg).join(", ") : data.detail || "Request failed");
  return data;
}
export const api = {
  events: (params={}) => { const q = new URLSearchParams(Object.entries(params).filter(([,v])=>v)); return request(`/api/events${q.size?`?${q}`:""}`); },
  event: id => request(`/api/events/${id}`),
  register: (id,body) => request(`/api/events/${id}/registrations`,{method:"POST",body:JSON.stringify(body)}),
  login: body => request("/api/auth/login",{method:"POST",body:JSON.stringify(body)}),
  logout: () => request("/api/auth/logout",{method:"POST"}),
  me: () => request("/api/auth/me"),
  dashboard: () => request("/api/admin/dashboard"),
  adminEvents: () => request("/api/admin/events"),
  createEvent: body => request("/api/admin/events",{method:"POST",body:JSON.stringify(body)}),
  updateEvent: (id,body) => request(`/api/admin/events/${id}`,{method:"PATCH",body:JSON.stringify(body)}),
  deleteEvent: id => request(`/api/admin/events/${id}`,{method:"DELETE"}),
  registrations: id => request(`/api/admin/events/${id}/registrations`)
};
