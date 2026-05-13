import { usePolling } from '../hooks/usePolling'
import { fetchNews } from '../services/api'

const sentimentColor = { positive: '#22c55e', negative: '#ef4444', neutral: '#94a3b8' }
const sentimentLabel = { positive: '?', negative: '?', neutral: '-' }

export default function NewsPanel() {
  const { data: news, loading, error, lastUpdated } = usePolling(fetchNews, 60000)
  if (loading) return <div className="panel-loading">Loading news...</div>
  if (error) return <div className="panel-error">? {error}</div>
  if (!news || news.length === 0) return <div className="panel-loading">Waiting for news...</div>
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>MARKET NEWS</h2>
        <span className="updated">Updated {lastUpdated?.toLocaleTimeString()}</span>
      </div>
      <div className="news-list">
        {news.map((item, idx) => (
          <div key={idx} className="news-item">
            <div className="news-meta">
              <span className="news-sentiment" style={{ color: sentimentColor[item.sentiment] ?? '#94a3b8' }}>
                {sentimentLabel[item.sentiment] ?? '-'}
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
