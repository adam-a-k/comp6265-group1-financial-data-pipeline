import "./App.css"
import { useCallback } from "react"
import { fetchStocks, fetchForex, fetchCrypto, fetchNews } from "./services/api"
import StockPanel from "./components/StockPanel"
import ForexPanel from "./components/ForexPanel"
import { CryptoPanel } from "./components/CryptoPanel"
import NewsPanel from "./components/NewsPanel"
import { usePolling } from "./hooks/usePolling"

export default function App() {
  const stocks = usePolling(fetchStocks, 30000)
  const forex = usePolling(fetchForex, 30000)
  const crypto = usePolling(fetchCrypto, 30000)
  const news = usePolling(fetchNews, 60000)

  const handleRefresh = useCallback(() => {
    window.location.reload()
  }, [])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="logo">? FINPULSE</span>
          <span className="date">{new Date().toLocaleDateString("en-US", { weekday:"long", year:"numeric", month:"long", day:"numeric" })}</span>
        </div>
        <div className="header-right">
          <button onClick={handleRefresh} className="refresh-btn">? Refresh</button>
          <span className="live-indicator">? LIVE</span>
        </div>
      </header>
      <main className="main">
        <div className="left-col">
          <StockPanel data={stocks} />
          <ForexPanel data={forex} />
          <CryptoPanel data={crypto} />
        </div>
        <div className="right-col">
          <NewsPanel data={news} />
        </div>
      </main>
    </div>
  )
}
