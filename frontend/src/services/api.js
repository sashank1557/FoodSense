/**
 * FoodSense - Frontend API Client
 * Connects directly to Express Relay Gateway (http://127.0.0.1:3001/api).
 * Handles Auth (JWT), Meal History, Daily Aggregation, Manual Corrections, and Inference Proxy.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds to accommodate cold starts
});

// In-memory token storage with sessionStorage fallback
let authToken = sessionStorage.getItem('foodsense_jwt_token') || null;

export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    sessionStorage.setItem('foodsense_jwt_token', token);
  } else {
    sessionStorage.removeItem('foodsense_jwt_token');
  }
};

export const getAuthToken = () => authToken;

// Axios Request Interceptor: Attach JWT token if available
apiClient.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

/**
 * Check backend health status (Express + Upstream Flask)
 */
export const checkBackendHealth = async () => {
  try {
    const res = await apiClient.get('/health', { timeout: 5000 });
    return {
      success: res.data?.status === 'healthy',
      data: res.data
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Backend unreachable'
    };
  }
};

/**
 * Analyze meal photo through Express relay to Flask inference
 * Automatically saves to history if user is logged in
 */
export const analyzeMealImage = async (
  imageFile,
  options = { onUploadProgress: null, signal: null }
) => {
  const formData = new FormData();
  formData.append('image', imageFile);

  try {
    const response = await apiClient.post('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal: options.signal,
      onUploadProgress: (progressEvent) => {
        if (options.onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onUploadProgress(percentCompleted);
        }
      }
    });

    return response.data;

  } catch (error) {
    if (axios.isCancel(error) || error.name === 'CanceledError') {
      throw { isCanceled: true, message: 'Analysis canceled by user.' };
    }

    if (error.response?.status === 503 || error.response?.data?.error === 'INFERENCE_BACKEND_COLD_START') {
      const err = new Error(error.response?.data?.message || 'Inference engine is waking up. Please retry in a few seconds.');
      err.isColdStart = true;
      throw err;
    }

    if (error.response?.status === 400) {
      const err = new Error(error.response?.data?.message || 'Invalid image uploaded. Please choose a clear JPEG or PNG photo.');
      err.isValidationError = true;
      throw err;
    }

    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      const err = new Error('Request timed out while waiting for AI models to respond. The server may be waking up.');
      err.isColdStart = true;
      throw err;
    }

    const message = error.response?.data?.message || error.message || 'Failed to analyze meal photo.';
    throw new Error(message);
  }
};

/**
 * Manual Food Classification Correction
 */
export const submitMealCorrection = async ({
  meal_id,
  original_label = 'unrecognized',
  corrected_label,
  correction_type = 'misclassified',
  bbox,
  all_items
}) => {
  const res = await apiClient.post('/correct', {
    meal_id,
    original_label,
    corrected_label,
    correction_type,
    bbox,
    all_items
  });
  return res.data;
};

export const fetchCorrectionsExport = async () => {
  const res = await apiClient.get('/corrections/export');
  return res.data;
};

/**
 * Authentication Endpoints
 */
export const signupUser = async ({ email, password, name }) => {
  const res = await apiClient.post('/auth/signup', { email, password, name });
  if (res.data?.token) {
    setAuthToken(res.data.token);
  }
  return res.data;
};

export const loginUser = async ({ email, password }) => {
  const res = await apiClient.post('/auth/login', { email, password });
  if (res.data?.token) {
    setAuthToken(res.data.token);
  }
  return res.data;
};

export const fetchCurrentUser = async () => {
  if (!authToken) return null;
  try {
    const res = await apiClient.get('/auth/me');
    return res.data?.user || null;
  } catch (err) {
    setAuthToken(null);
    return null;
  }
};

/**
 * Meal History & Daily Totals Endpoints
 */
export const fetchMealHistory = async ({ limit = 50, offset = 0 } = {}) => {
  const res = await apiClient.get('/history', { params: { limit, offset } });
  return res.data;
};

export const fetchDailyTotals = async (dateString) => {
  const params = dateString ? { date: dateString } : {};
  const res = await apiClient.get('/history/daily-totals', { params });
  return res.data;
};

export const deleteMealHistoryEntry = async (id) => {
  const res = await apiClient.delete(`/history/${id}`);
  return res.data;
};

export const fetchSupportedClasses = async () => {
  try {
    const res = await apiClient.get('/analyze/classes', { timeout: 8000 });
    return res.data;
  } catch (err) {
    console.warn('Could not load class metadata:', err);
    return null;
  }
};

/**
 * 1500+ Indian Dishes Catalog & Search API
 */
export const searchDishes = async (query = '', { category = null, region = null, limit = 25, offset = 0 } = {}) => {
  const params = { q: query, limit, offset };
  if (category && category !== 'All') params.category = category;
  if (region && region !== 'All') params.region = region;

  const res = await apiClient.get('/dishes/search', { params });
  return res.data;
};

export const fetchDishCategories = async () => {
  try {
    const res = await apiClient.get('/dishes/categories');
    return res.data;
  } catch (err) {
    console.warn('Could not load dish categories:', err);
    return { categories: [], regions: [], total_dishes: 0 };
  }
};

export const fetchDishById = async (id) => {
  const res = await apiClient.get(`/dishes/${id}`);
  return res.data;
};

export const saveCustomDish = async (dishData) => {
  const res = await apiClient.post('/dishes/custom', dishData);
  return res.data;
};
