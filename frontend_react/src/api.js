import axios from 'axios';

export const API = 'https://cod-trakr-sor4.onrender.com';

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;
