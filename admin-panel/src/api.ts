export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080/api';
export const API_ORIGIN = API_URL.replace(/\/api\/?$/, '');
export const WS_ORIGIN = API_ORIGIN.replace(/^http/, 'ws');
let token = localStorage.getItem('admin_token');
export function setAdminToken(t: string) { token = t; localStorage.setItem('admin_token', t); }
export function clearAdminToken() { token = null; localStorage.removeItem('admin_token'); }
export function mediaUrl(path?: string) { if (!path) return ''; if (path.startsWith('http')) return path; if (path.startsWith('/media') && /\/api\/?$/.test(API_URL)) return `${API_URL}${path}`; return `${API_ORIGIN}${path}`; }
async function req(path: string, options: RequestInit = {}) {
  const headers: Record<string,string> = { ...(options.headers as any) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) { const text = await res.text(); let message = text || `HTTP ${res.status}`; try { const parsed = JSON.parse(text); message = parsed.error || parsed.detail || message; } catch {} throw new Error(message); }
  return res.json();
}
export const api = {
  login: (phone: string, password: string) => req('/auth/login', { method: 'POST', body: JSON.stringify({ phone, password }) }),
  me: () => req('/auth/me'),
  dashboard: () => req('/admin/dashboard'),
  users: () => req('/admin/users'),
  user: (id: string) => req(`/admin/users/${id}`),
  farmers: () => req('/admin/farmers'),
  createUser: (payload: any) => req('/admin/users', { method:'POST', body: JSON.stringify(payload) }),
  updateUser: (id: string, payload: any) => req(`/admin/users/${id}`, { method:'PATCH', body: JSON.stringify(payload) }),
  toggleUser: (id: string) => req(`/admin/users/${id}/toggle`, { method:'POST' }),
  deleteUser: (id: string) => req(`/admin/users/${id}`, { method:'DELETE' }),
  resetPassword: (id: string, new_password: string) => req(`/admin/users/${id}/reset-password`, { method:'POST', body: JSON.stringify({ new_password }) }),
  changePassword: (payload: any) => req('/auth/change-password', { method:'POST', body: JSON.stringify(payload) }),
  pests: () => req('/pests'),
  savePest: (payload: any) => req('/admin/pests', { method: 'POST', body: JSON.stringify(payload) }),
  togglePest: (id: string) => req(`/admin/pests/${id}/toggle`, { method:'POST' }),
  deletePest: (id: string) => req(`/admin/pests/${id}`, { method:'DELETE' }),
  adminInsecticides: () => req('/insecticides/admin'),
  getInsecticide: (id: string) => req(`/insecticides/admin/${id}`),
  saveInsecticide: (payload: any, id?: string) => req(id ? `/insecticides/admin/${id}` : '/insecticides/admin', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload) }),
  toggleInsecticide: (id: string) => req(`/insecticides/admin/${id}/toggle`, { method:'POST' }),
  uploadAsset: (file: File) => { const fd = new FormData(); fd.append('file', file); return req('/admin/assets', { method:'POST', body: fd }); },
  uploadTrainingImage: (file: File, pest_id: string, stage: string, verified = true) => { const fd = new FormData(); fd.append('image', file); fd.append('pest_id', pest_id); fd.append('stage', stage); fd.append('verified', String(verified)); return req('/admin/training-images', { method: 'POST', body: fd }); },
  pendingTrainingImages: () => req('/admin/training-images/pending'),
  verifyTrainingImage: (id: string, pestId: string, stage: string) => { const fd = new FormData(); fd.append('pest_id', pestId); fd.append('stage', stage); return req(`/admin/training-images/${id}/verify`, { method: 'POST', body: fd }); },
  detectionsToReview: () => req('/admin/detections/review'),
  updateDetection: (id: string, payload: any) => req(`/admin/detections/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  approveDetection: (id: string, pestId: string, stage: string) => { const fd = new FormData(); fd.append('pest_id', pestId); fd.append('stage', stage); return req(`/admin/detections/${id}/approve-training`, { method: 'POST', body: fd }); },
  blogs: () => req('/admin/blogs'),
  publishBlog: (payload: any) => req('/admin/blogs', { method: 'POST', body: JSON.stringify(payload) }),
  updateBlog: (id: string, payload: any) => req(`/admin/blogs/${id}`, { method:'PATCH', body: JSON.stringify(payload) }),
  deleteBlog: (id: string) => req(`/admin/blogs/${id}`, { method:'DELETE' }),
  events: () => req('/admin/events'),
  saveEvent: (payload: any, id?: string) => req(id ? `/admin/events/${id}` : '/admin/events', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload) }),
  deleteEvent: (id: string) => req(`/admin/events/${id}`, { method:'DELETE' }),
  calendar: () => req('/admin/calendar'),
  getCalendar: (id: string) => req(`/admin/calendar/${id}`),
  saveCalendar: (payload: any, id?: string) => req(id ? `/admin/calendar/${id}` : '/admin/calendar', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload) }),
  deleteCalendar: (id: string) => req(`/admin/calendar/${id}`, { method:'DELETE' }),
  chats: () => req('/admin/chats'),
  chatMessages: (id: string) => req(`/admin/chats/${id}/messages`),
  sendChat: (id: string, message: string) => req(`/admin/chats/${id}/messages`, { method:'POST', body: JSON.stringify({ message }) }),
  sendChatAttachment: (id: string, file: File, message = '') => { const fd = new FormData(); fd.append('message', message); fd.append('file', file); return req(`/admin/chats/${id}/attachments`, { method:'POST', body: fd }); },
  adminNotifications: () => req('/notifications/admin'),
  adminNotificationCount: () => req('/notifications/admin/unread-count'),
  readAdminNotification: (id: string) => req(`/notifications/admin/${id}/read`, { method:'POST' }),
  deleteAdminNotification: (id: string) => req(`/notifications/admin/${id}`, { method:'DELETE' }),
  clearAdminNotifications: () => req('/notifications/admin/clear', { method:'POST' }),
  sendNotification: (payload: any) => req('/notifications/admin/send', { method:'POST', body: JSON.stringify(payload) }),
  pushCampaigns: () => req('/notifications/admin/push-campaigns'),
  firebaseStatus: () => req('/notifications/admin/firebase-status'),
  firebaseLogs: () => req('/notifications/admin/firebase-logs'),
  classCoverage: () => req('/admin/ai/class-coverage'),
  freeModels: () => req('/admin/ai/free-models'),
  feedData: (payload: any) => req('/admin/ai/feed-data', { method: 'POST', body: JSON.stringify(payload) }),
  train: (dataset_version: string, base_model: string) => req('/admin/ai/train', { method: 'POST', body: JSON.stringify({ dataset_version, base_model, epochs: 3, batch_size: 8 }) }),
  jobs: () => req('/admin/ai/jobs'),
  aiModels: () => req('/admin/ai/models'),
};
