import { usePolling } from '../hooks/usePolling'
import { fetchCrypto } from '../services/api'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export function CryptoPanel() {
  const { data, loading, error, lastUpdated } = usePolling(fetchCrypto, 30000)
  if (loading) return <div className="panel-loading">Loading crypto...</div>
  if (error) return <div className="panel-error">? {error}</div>
  if (!data || data.length === 0) return <div className="panel-loading">Waiting for crypto...</div>
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>CRYPTO</h2>
        <span className="updated">Updated {lastUpdated?.toLocaleTimeString()}</span>
      </div>
      <div className="forex-list">
        {data.map(c => {
          const positive = c.change >= 0
          const chartData = Array.isArray(c.history) ? c.history.map((v, i) => ({ i, v: Number(v) })) : []
          return (
            <div key={c.symbol} className="forex-row">
              <div className="forex-left">
                <span className="forex-pair">{c.symbol.toUpperCase()}</span>
                <span className={`forex-change ${positive ? 'up' : 'down'}`}>
                  {positive ? '+' : ''}{c.change}%
                </span>
              </div>
              <ResponsiveContainer width={120} height={36}>
                <LineChart data={chartData}>
                  <Line type="monotone" dataKey="v" stroke={positive ? '#22c55e' : '#ef4444'} strokeWidth={1.5} dot={false} />
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: 'none', fontSize: 10 }} formatter={v => [`$${Number(v).toLocaleString()}`, '']} labelFormatter={() => ''} />
                </LineChart>
              </ResponsiveContainer>
              <div className="forex-rate">${Number(c.price).toLocaleString()}</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
