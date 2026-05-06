import { usePolling } from '../hooks/usePolling'
import { fetchNews } from '../services/api'

const sentimentColor = { positive: '#22c55e', negative: '#ef4444', neutral: '#94a3b8' }
const sentimentLabel = { positive: '▲', negative: '▼', neutral: '–' }

export default function NewsPanel() {
  const { data: news, loading, error, lastUpdated } = usePolling(fetchNews, 60000)

  if (loading) return <div className="panel-loading">Loading news…</div>
  if (error)   return <div className="panel-error">⚠ {error}</div>

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Market News</h2>
        <span className="updated">Updated {lastUpdated?.toLocaleTimeString()}</span>
      </div>
      <div className="news-list">
        {news.map(item => (
          <div key={item.id} className="news-item">
            <div className="news-meta">
              <span
                className="news-sentiment"
                style={{ color: sentimentColor[item.sentiment] }}
              >
                {sentimentLabel[item.sentiment]}
              </span>
              <span className="news-source">{item.source}</span>
              <span className="news-category">{item.category}</span>
              <span className="news-time">{item.ago}</span>
            </div>
            <p className="news-title">{item.title}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
