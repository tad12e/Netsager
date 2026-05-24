import axios from 'axios';

const API = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const fetchProducts = () => API.get('products/');
export const fetchListings = () => API.get('listings/');
export const fetchSellers = () => API.get('sellers/');

export default API;
