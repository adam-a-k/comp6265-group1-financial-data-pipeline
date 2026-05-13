import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts"

export function CryptoPanel({ data }) {
  const updated = new Date().toLocaleTimeString()
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>CRYPTO</h2>
        <span className="updated">Updated {updated}</span>
      </div>
      {!data || data.length === 0 ? (
        <div className="loading">Loading crypto...</div>
      ) : (
        data.map(c => (
          <div key={c.symbol} className="forex-row">
            <div>
              <div className="forex-pair">{c.symbol.toUpperCase()}</div>
              <div className={c.change >= 0 ? "change-pos" : "change-neg"}>
                {c.change >= 0 ? "+" : ""}{c.change}%
              </div>
            </div>
            <div className="forex-chart">
              <ResponsiveContainer width="100%" height={40}>
                <LineChart data={c.history.map(v => ({ value: v }))}>
                  <Line type="monotone" dataKey="value" stroke="#00ff88" dot={false} strokeWidth={1.5} />
                  <Tooltip formatter={(v) => [`$${Number(v).toLocaleString()}`, c.symbol.toUpperCase()]} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="forex-rate">${Number(c.price).toLocaleString()}</div>
          </div>
        ))
      )}
    </section>
  )
}
