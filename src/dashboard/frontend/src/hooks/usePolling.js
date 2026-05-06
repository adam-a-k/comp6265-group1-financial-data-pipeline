import { useState, useEffect, useCallback } from 'react'

export function usePolling(fetchFn, intervalMs = 30000) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const load = useCallback(async () => {
    try {
      const result = await fetchFn()
      setData(result)
      setError(null)
      setLastUpdated(new Date())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [fetchFn])

  useEffect(() => {
    load()
    const timer = setInterval(load, intervalMs)
    return () => clearInterval(timer)
  }, [load, intervalMs])

  return { data, loading, error, lastUpdated, refetch: load }
}
