import axios from 'axios';

// Use the VITE_API_URL environment variable if deployed over Render/Vercel
// Fallback to '/api' for local proxy development
const baseURL = import.meta.env.VITE_API_URL || '/api';
console.log("[StoXeye] API URL:", baseURL);

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// JWT interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // In demo mode, we don't automatically redirect to login for 401s
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(err);
  }
);

// Auth
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

// Stocks
export const stocksAPI = {
  list: (params) => api.get('/stocks', { params }),
  detail: (ticker) => api.get(`/company/${ticker}`),
  trend: () => api.get('/trend'),
};

// Watchlist
export const watchlistAPI = {
  get: () => api.get('/watchlist'),
  add: (ticker) => api.post('/watchlist', { ticker }),
  remove: (ticker) => api.delete(`/watchlist/${ticker}`),
};

// Alerts
export const alertsAPI = {
  get: (params) => api.get('/alerts', { params }),
  markRead: (id) => api.put(`/alerts/${id}/read`),
  markAllRead: () => api.put('/alerts/read-all'),
  setupTelegram: (chatId) => api.post('/alerts/telegram-setup', { chat_id: chatId }),
};

// Scanner
export const scannerAPI = {
  run: () => api.post('/scanner/run'),
  status: () => api.get('/scanner/status'),
};

export default api;
