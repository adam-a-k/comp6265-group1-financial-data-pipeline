import { usePolling } from '../hooks/usePolling'
import { fetchStocks } from '../services/api'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function StockPanel() {
  const { data: stocks, loading, error, lastUpdated } = usePolling(fetchStocks, 30000)

  if (loading) return <div className="panel-loading">Loading stocks…</div>
  if (error)   return <div className="panel-error">⚠ {error}</div>
  if (!stocks || stocks.length === 0) return <div className="panel-loading">Waiting for data...</div>

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Stocks</h2>
        <span className="updated">Updated {lastUpdated?.toLocaleTimeString()}</span>
      </div>
      <div className="stock-grid">
        {stocks.map(s => {
          const positive = s.change >= 0
          const chartData = (s.history ?? []).map((v, i) => ({ i, v }))
          return (
            <div key={s.symbol} className={`stock-card ${positive ? 'up' : 'down'}`}>
              <div className="stock-top">
                <span className="symbol">{s.symbol}</span>
                {positive ? <TrendingUp size={16}/> : <TrendingDown size={16}/>}
              </div>
              <div className="price">${s.price.toLocaleString()}</div>
              <div className="change">{positive ? '+' : ''}{s.change}%</div>
              <ResponsiveContainer width="100%" height={50}>
                <LineChart data={chartData}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke={positive ? '#22c55e' : '#ef4444'}
                    strokeWidth={1.5}
                    dot={false}
                  />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: 'none', fontSize: 11 }}
                    formatter={v => [`$${v}`, '']}
                    labelFormatter={() => ''}
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="volume">Vol {(s.volume / 1e6).toFixed(1)}M</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}