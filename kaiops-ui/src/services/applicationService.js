import axios from 'axios';
import { API_BASE_URL } from '../constants/apiConstants';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('📤 API Request:', config.method.toUpperCase(), config.url, token ? '✅ Token attached' : '❌ No token');
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 API Response:', response.config.method.toUpperCase(), response.config.url, response.status);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('❌ API Error:', error.response.status, error.response.data);
      if (error.response.status === 401) {
        console.error('🔒 Unauthorized - redirecting to login');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
      }
    } else {
      console.error('❌ Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Application Service
export const applicationService = {
  /**
   * Get all applications with optional filters and pagination
   */
  async getApplications(params = {}) {
    try {
      const response = await apiClient.get('/applications/', { params });
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Get single application by ID
   */
  async getApplication(id) {
    try {
      const response = await apiClient.get(`/applications/${id}`);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Create new application
   */
  async createApplication(data) {
    try {
      const response = await apiClient.post('/applications/', data);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Update existing application
   */
  async updateApplication(id, data) {
    try {
      const response = await apiClient.put(`/applications/${id}`, data);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Delete application (Admin only)
   */
  async deleteApplication(id) {
    try {
      await apiClient.delete(`/applications/${id}`);
      return { success: true };
    } catch (error) {

      throw error;
    }
  },

  /**
   * Toggle application status (Active/Inactive)
   */
  async toggleStatus(id) {
    try {
      const response = await apiClient.post(`/applications/${id}/toggle`);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Search applications
   */
  async searchApplications(query, limit = 20) {
    try {
      const response = await apiClient.get('/applications/search/query', {
        params: { q: query, limit }
      });
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Get application statistics
   */
  async getStatistics() {
    try {
      const response = await apiClient.get('/applications/stats/summary');
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Get applications by owner
   */
  async getByOwner(owner) {
    try {
      const response = await apiClient.get(`/applications/owner/${owner}`);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Get applications by cluster
   */
  async getByCluster(cluster) {
    try {
      const response = await apiClient.get(`/applications/cluster/${cluster}`);
      return response.data;
    } catch (error) {

      throw error;
    }
  },

  /**
   * Get applications by status
   */
  async getByStatus(status) {
    try {
      const response = await apiClient.get(`/applications/status/${status}`);
      return response.data;
    } catch (error) {

      throw error;
    }
  },
};

export default applicationService;
