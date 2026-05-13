import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
})

export const fetchStocks = () => api.get('/stocks').then(r => r.data)
export const fetchForex  = () => api.get('/forex').then(r => r.data)
export const fetchNews   = () => api.get('/news').then(r => r.data)