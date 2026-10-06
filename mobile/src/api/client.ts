export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8080/api';
const API_ORIGIN = API_URL.replace(/\/api\/?$/, '');
export const WS_ORIGIN = API_ORIGIN.replace(/^http/, 'ws');

let token: string | null = null;
export function setToken(next: string | null) { token = next; }
export function getToken() { return token; }
export function mediaUrl(path?: string | null) {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  if (path.startsWith('/media') && /\/api\/?$/.test(API_URL)) return `${API_URL}${path}`;
  return `${API_ORIGIN}${path}`;
}

async function request(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> | undefined) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    let message = text || `HTTP ${res.status}`;
    try { const parsed = JSON.parse(text); message = parsed.error || parsed.detail || message; } catch {}
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  login: (phone: string, password: string) => request('/auth/login', { method: 'POST', body: JSON.stringify({ phone, password }) }),
  register: (payload: { name: string; phone: string; password: string; district?: string }) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request('/auth/me'),
  registerFcmToken: (token: string, platform: string) => request('/notifications/register-token', { method: 'POST', body: JSON.stringify({ token, platform }) }),
  updateProfile: (payload: any) => request('/auth/me', { method: 'PATCH', body: JSON.stringify(payload) }),
  pests: () => request('/pests'),
  history: () => request('/detections/history'),
  detection: (id: string) => request(`/detections/${id}`),
  feedback: (id: string, payload: any) => request(`/detections/${id}/feedback`, { method: 'POST', body: JSON.stringify(payload) }),
  blogs: (language = 'en') => request(`/blogs?language=${language}`),
  blog: (id: string, language: string = 'en') => request(`/blogs/${id}?language=${language}`),
  likeBlog: (id: string) => request(`/blogs/${id}/like`, { method: 'POST' }),
  commentBlog: (id: string, comment: string) => request(`/blogs/${id}/comments`, { method: 'POST', body: JSON.stringify({ comment }) }),
  calendar: (language: string = 'en') => request(`/pests/calendar/year?language=${language}`),
  events: (language: string = 'en') => request(`/events?language=${language}`),
  insecticides: () => request('/insecticides'),
  notifications: () => request('/notifications'),
  unreadNotifications: () => request('/notifications/unread-count'),
  readNotification: (id: string) => request(`/notifications/${id}/read`, { method: 'POST' }),
  deleteNotification: (id: string) => request(`/notifications/${id}`, { method: 'DELETE' }),
  clearNotifications: () => request('/notifications/clear', { method: 'POST' }),
  chats: () => request('/chat/conversations'),
  createChat: (message: string) => request('/chat/conversations', { method: 'POST', body: JSON.stringify({ message }) }),
  chatMessages: (id: string) => request(`/chat/conversations/${id}/messages`),
  sendChat: (id: string, message: string) => request(`/chat/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify({ message }) }),
  sendChatAttachment: (id: string, uri: string, name: string, type: string, message = '') => { const fd = new FormData(); fd.append('message', message); fd.append('file', { uri, name, type } as any); return request(`/chat/conversations/${id}/attachments`, { method: 'POST', body: fd }); },
  detect: async (uri: string, source: 'camera' | 'gallery') => {
    const data = new FormData();
    data.append('source', source);
    data.append('image', { uri, name: 'citri-photo.jpg', type: 'image/jpeg' } as any);
    return request('/detections', { method: 'POST', body: data });
  },
  sendDetectionForTraining: (detectionId: string) => request(`/detections/${detectionId}/send-for-training`, { method: 'POST' }),
};
