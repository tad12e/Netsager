import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const setAuthToken = (token) => {
  if (token) {
    API.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete API.defaults.headers.common.Authorization;
  }
};

export const fetchProducts = () => API.get('products/');
export const fetchListings = () => API.get('listings/');
export const fetchSellers = () => API.get('sellers/');
export const registerUser = (payload) => API.post('auth/register/', payload);
export const loginUser = (payload) => API.post('auth/login/', payload);
export const loginWithGoogle = (payload) => API.post('auth/google/', payload, { timeout: 25000 });
export const fetchCurrentUser = () => API.get('auth/me/');
export const logoutUser = () => API.post('auth/logout/');

export default API;
