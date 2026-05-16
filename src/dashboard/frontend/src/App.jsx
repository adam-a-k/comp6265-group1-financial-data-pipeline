import "./App.css"
import { useCallback } from "react"
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom"
import { fetchStocks, fetchForex, fetchCrypto, fetchNews } from "./services/api"
import StockPanel from "./components/StockPanel"
import ForexPanel from "./components/ForexPanel"
import { CryptoPanel } from "./components/CryptoPanel"
import NewsPanel from "./components/NewsPanel"
import AuditLogPanel from "./components/AuditLogPanel"
import SourceRegistryPanel from "./components/SourceRegistryPanel"
import { usePolling } from "./hooks/usePolling"

function Dashboard({ stocks, forex, crypto, news }) {
  return (
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
  )
}

export default function App() {
  const stocks = usePolling(fetchStocks, 30000)
  const forex  = usePolling(fetchForex, 30000)
  const crypto = usePolling(fetchCrypto, 30000)
  const news   = usePolling(fetchNews, 60000)

  const handleRefresh = useCallback(() => window.location.reload(), [])

  return (
    <BrowserRouter>
      <div className="app">
        <header className="header">
          <div className="header-left">
            <span className="logo">⚡ FINPULSE</span>
            <nav className="nav">
              <NavLink to="/"         end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Dashboard</NavLink>
              <NavLink to="/registry"     className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Sources</NavLink>
              <NavLink to="/audit"        className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Audit Log</NavLink>
            </nav>
          </div>
          <div className="header-right">
            <button onClick={handleRefresh} className="refresh-btn">↻ Refresh</button>
            <span className="live-indicator">● LIVE</span>
          </div>
        </header>
        <Routes>
          <Route path="/"         element={<Dashboard stocks={stocks} forex={forex} crypto={crypto} news={news} />} />
          <Route path="/registry" element={<SourceRegistryPanel />} />
          <Route path="/audit"    element={<AuditLogPanel />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}