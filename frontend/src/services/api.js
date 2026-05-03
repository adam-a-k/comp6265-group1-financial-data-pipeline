import axios from 'axios'

const api = axios.create({
  baseURL: '/api',   // Vite proxy forwards this to http://localhost:8000
  timeout: 8000,
})

export const fetchStocks = () => api.get('/stocks').then(r => r.data)
export const fetchForex  = () => api.get('/forex').then(r => r.data)
export const fetchNews   = () => api.get('/news').then(r => r.data)
