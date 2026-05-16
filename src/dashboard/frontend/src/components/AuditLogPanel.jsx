import { useEffect, useState } from "react"
import keycloak from "../keycloak"

const ACTION_COLOURS = {
  CREATE: "#4ade80",
  UPDATE: "#60a5fa",
  DELETE: "#f87171",
}

export default function AuditLogPanel() {
  const [logs, setLogs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [filter, setFilter]   = useState("")

  const load = () => {
    setLoading(true)
    fetch("/api/audit-logs", {
      headers: { "Authorization": `Bearer ${keycloak.token}` }
    })
      .then(r => r.json())
      .then(data => {
        if (!Array.isArray(data)) { setError(JSON.stringify(data)); setLoading(false); return }
        setLogs(data)
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const visible = logs.filter(l =>
    !filter || l.action === filter || l.resource.includes(filter)
  )

  return (
    <div className="panel" style={{ margin: "1.5rem" }}>
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Audit Log</h2>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <select value={filter} onChange={e => setFilter(e.target.value)} className="filter-select">
            <option value="">All</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
          </select>
          <button onClick={load} className="refresh-btn">↻ Refresh</button>
        </div>
      </div>

      {loading && <p className="muted">Loading…</p>}
      {error   && <p style={{ color: "#f87171" }}>Error: {error}</p>}

      {!loading && !error && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #333" }}>
              <th style={{ padding: "0.5rem" }}>Time</th>
              <th style={{ padding: "0.5rem" }}>Action</th>
              <th style={{ padding: "0.5rem" }}>Resource</th>
              <th style={{ padding: "0.5rem" }}>ID</th>
              <th style={{ padding: "0.5rem" }}>User</th>
              <th style={{ padding: "0.5rem" }}>IP</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 && (
              <tr><td colSpan={6} style={{ padding: "1rem", color: "#888" }}>No entries</td></tr>
            )}
            {visible.map(log => (
              <tr key={log.id} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ padding: "0.5rem", color: "#888" }}>
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <span style={{
                    color: ACTION_COLOURS[log.action] ?? "#ccc",
                    fontWeight: 600,
                    fontSize: "0.75rem",
                    letterSpacing: "0.05em"
                  }}>
                    {log.action}
                  </span>
                </td>
                <td style={{ padding: "0.5rem" }}>{log.resource}</td>
                <td style={{ padding: "0.5rem", color: "#888" }}>{log.resource_id ?? "—"}</td>
                <td style={{ padding: "0.5rem" }}>{log.user_id ?? "—"}</td>
                <td style={{ padding: "0.5rem", color: "#888" }}>{log.ip_address ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}