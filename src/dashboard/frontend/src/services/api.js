import axios from 'axios'
import Keycloak from 'keycloak-js'
import keycloak from '../keycloak'

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
})

const groupBySymbol = (raw) => {
  const grouped = {}
  raw.forEach(row => {
    const sym = row.symbol
    if (!grouped[sym]) grouped[sym] = []
    grouped[sym].push(row)
  })
  return grouped
}

const calcChange = (rows) => {
  const latest = rows[rows.length - 1]
  const first = rows[0]
  if (latest.price && first.price && latest.price !== first.price) {
    return parseFloat(((latest.price - first.price) / first.price * 100).toFixed(2))
  }
  return parseFloat((latest.price_change_pct ?? 0).toFixed(2))
}

export const fetchStocks = () => api.get('/stocks').then(r => {
  const grouped = groupBySymbol(r.data)
  return Object.entries(grouped).map(([symbol, rows]) => {
    const latest = rows[rows.length - 1]
    return {
      symbol,
      price: latest.price,
      change: calcChange(rows),
      volume: latest.volume ?? 0,
      history: rows.map(r => r.price).filter(Boolean)
    }
  })
})

export const fetchForex = () => api.get('/forex').then(r => {
  const grouped = groupBySymbol(r.data)
  return Object.entries(grouped).map(([pair, rows]) => {
    const latest = rows[rows.length - 1]
    return {
      pair,
      rate: latest.price,
      change_pct: calcChange(rows),
      history: rows.map(r => r.price).filter(Boolean)
    }
  })
})

export const fetchCrypto = () => api.get('/crypto').then(r => {
  const grouped = groupBySymbol(r.data)
  return Object.entries(grouped).map(([symbol, rows]) => {
    const latest = rows[rows.length - 1]
    return {
      symbol,
      price: latest.price,
      change: calcChange(rows),
      history: rows.map(r => r.price).filter(Boolean)
    }
  })
})

export const fetchNews = () => api.get('/news').then(r => {
  return r.data.map(item => ({
    title: item.title,
    source: item.source ?? item.publisher ?? 'Unknown',
    sentiment: item.sentiment ?? 'neutral',
    category: item.symbol ?? 'General',
    ago: item.timestamp ?? item.fetched_at ?? ''
  }))
})

api.interceptors.request.use(config => {
  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`
  }
  return config
})