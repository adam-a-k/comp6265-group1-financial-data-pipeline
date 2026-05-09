import StockPanel from './components/StockPanel'
import ForexPanel from './components/ForexPanel'
import NewsPanel  from './components/NewsPanel'
import './App.css'

export default function App() {
  const now = new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="logo">◈ FINPULSE</div>
          <span className="header-date">{now}</span>
        </div>
        <div className="header-right">
          <span className="live-badge">● LIVE</span>
        </div>
      </header>

      <main className="dashboard">
        <div className="col-left">
          <StockPanel />
          <ForexPanel />
        </div>
        <div className="col-right">
          <NewsPanel />
        </div>
      </main>
    </div>
  )
}
