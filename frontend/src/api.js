import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API endpoints
export const scraperAPI = {
  // Scraper operations
  runScraping: () => api.post('/scraper/run'),
  getSessions: (limit = 10) => api.get(`/scraper/sessions?limit=${limit}`),
  getSession: (sessionId) => api.get(`/scraper/session/${sessionId}`),
  
  // Tweet operations
  getTweets: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/tweets?${queryParams.toString()}`);
  },
  
  searchTweets: (searchParams) => api.post('/tweets/search', searchParams),
  getTweet: (tweetId) => api.get(`/tweets/${tweetId}`),
  
  // Analytics
  getAnalytics: () => api.get('/analytics'),
  
  // Configuration
  getConfig: () => api.get('/config'),
  updateConfig: (config) => api.post('/config', config),
  
  // Scheduler
  startScheduler: () => api.post('/scheduler/start'),
  stopScheduler: () => api.post('/scheduler/stop'),
  getSchedulerStatus: () => api.get('/scheduler/status'),
  
  // Health check
  healthCheck: () => api.get('/'),
};

export default api;