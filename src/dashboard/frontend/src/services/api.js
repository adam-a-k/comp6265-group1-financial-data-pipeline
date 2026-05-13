import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
})

export const fetchStocks = () => api.get('/stocks').then(r => {
  const raw = r.data
  const grouped = {}
  raw.forEach(row => {
    const sym = row.symbol
    if (!grouped[sym]) grouped[sym] = []
    grouped[sym].push(row)
  })
  return Object.entries(grouped).map(([symbol, rows]) => {
    const latest = rows[rows.length - 1]
    return {
      symbol,
      price: latest.price,
      change: latest.price_change_pct ?? 0,
      volume: latest.volume ?? 0,
      history: rows.map(r => ({ value: r.price }))
    }
  })
})

export const fetchForex = () => api.get('/forex').then(r => {
  const raw = r.data
  const grouped = {}
  raw.forEach(row => {
    const sym = row.symbol
    if (!grouped[sym]) grouped[sym] = []
    grouped[sym].push(row)
  })
  return Object.entries(grouped).map(([pair, rows]) => {
    const latest = rows[rows.length - 1]
    return {
      pair,
      rate: latest.price,
      change_pct: latest.price_change_pct ?? 0,
      history: rows.map(r => ({ value: r.price }))
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
