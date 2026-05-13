import { usePolling } from '../hooks/usePolling'
import { fetchForex } from '../services/api'
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts'

export default function ForexPanel() {
  const { data: pairs, loading, error, lastUpdated } = usePolling(fetchForex, 30000)

  if (loading) return <div className="panel-loading">Loading forex…</div>
  if (error)   return <div className="panel-error">⚠ {error}</div>
  if (!pairs || pairs.length === 0) return <div className="panel-loading">Waiting for data...</div>

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Forex</h2>
        <span className="updated">Updated {lastUpdated?.toLocaleTimeString()}</span>
      </div>
      <div className="forex-list">
        {pairs.map(p => {
          const positive = p.change_pct >= 0
          const chartData = p.history.map((v, i) => ({ i, v }))
          return (
            <div key={p.pair} className="forex-row">
              <div className="forex-left">
                <span className="forex-pair">{p.pair}</span>
                <span className={`forex-change ${positive ? 'up' : 'down'}`}>
                  {positive ? '+' : ''}{p.change_pct}%
                </span>
              </div>
              <ResponsiveContainer width={120} height={36}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id={`fg-${p.pair.replace('/','')}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={positive ? '#22c55e' : '#ef4444'} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={positive ? '#22c55e' : '#ef4444'} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke={positive ? '#22c55e' : '#ef4444'}
                    fill={`url(#fg-${p.pair.replace('/','')}`}
                    strokeWidth={1.5}
                    dot={false}
                  />
                  <Tooltip
                    contentStyle={{ background: '#1a1a2e', border: 'none', fontSize: 10 }}
                    formatter={v => [v, '']}
                    labelFormatter={() => ''}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <div className="forex-rate">{p.rate}</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}