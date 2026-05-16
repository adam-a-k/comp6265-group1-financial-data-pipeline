import { useEffect, useState } from "react"
import keycloak from "../keycloak"

const STATUS_COLOUR = { active: "#4ade80", inactive: "#888", error: "#f87171" }
const EMPTY_FORM = { name: "", source_type: "REST_API", url: "", owner: "", status: "active" }

const authHeader = () => ({ "Authorization": `Bearer ${keycloak.token}` })

export default function SourceRegistryPanel({ canRegister }) {
  const [sources, setSources]       = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [form, setForm]             = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError]   = useState(null)

  const load = () => {
    setLoading(true)
    fetch("/api/registry/", { headers: authHeader() })
      .then(r => r.json())
      .then(data => {
        if (!Array.isArray(data)) { setError(JSON.stringify(data)); setLoading(false); return }
        setSources(data)
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async e => {
    e.preventDefault()
    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch("/api/registry/", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify(form)
      })
      if (!res.ok) throw new Error(await res.text())
      setForm(EMPTY_FORM)
      load()
    } catch (e) {
      setFormError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async id => {
    if (!confirm("Delete this source?")) return
    await fetch(`/api/registry/${id}`, { method: "DELETE", headers: authHeader() })
    load()
  }

  const handleStatusToggle = async (id, current) => {
    const next = current === "active" ? "inactive" : "active"
    await fetch(`/api/registry/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ status: next })
    })
    load()
  }

  return (
    <div style={{ margin: "1.5rem" }}>

      {canRegister && (
        <div className="panel" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ marginBottom: "1rem" }}>Register Source</h2>
          <form onSubmit={handleSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <input required placeholder="Name"  value={form.name}   onChange={e => setForm({ ...form, name: e.target.value })}  className="input" />
            <select value={form.source_type} onChange={e => setForm({ ...form, source_type: e.target.value })} className="input">
              <option>REST_API</option>
              <option>CSV</option>
              <option>DB</option>
              <option>STREAM</option>
            </select>
            <input placeholder="URL"   value={form.url}   onChange={e => setForm({ ...form, url: e.target.value })}   className="input" />
            <input placeholder="Owner" value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} className="input" />
            <button type="submit" disabled={submitting} className="refresh-btn" style={{ gridColumn: "span 2" }}>
              {submitting ? "Registering…" : "+ Register"}
            </button>
            {formError && <p style={{ color: "#f87171", gridColumn: "span 2" }}>{formError}</p>}
          </form>
        </div>
      )}

      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2>Registered Sources</h2>
          <button onClick={load} className="refresh-btn">↻ Refresh</button>
        </div>

        {loading && <p className="muted">Loading…</p>}
        {error   && <p style={{ color: "#f87171" }}>Error: {error}</p>}

        {!loading && !error && (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #333" }}>
                {["Name","Type","URL","Owner","Status",""].map(h => (
                  <th key={h} style={{ padding: "0.5rem" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.length === 0 && (
                <tr><td colSpan={6} style={{ padding: "1rem", color: "#888" }}>No sources registered</td></tr>
              )}
              {sources.map(s => (
                <tr key={s.id} style={{ borderBottom: "1px solid #222" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 600 }}>{s.name}</td>
                  <td style={{ padding: "0.5rem", color: "#888" }}>{s.source_type}</td>
                  <td style={{ padding: "0.5rem", color: "#888", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.url || "—"}</td>
                  <td style={{ padding: "0.5rem" }}>{s.owner || "—"}</td>
                  <td style={{ padding: "0.5rem" }}>
                    <span
                      style={{ color: STATUS_COLOUR[s.status] ?? "#ccc", cursor: "pointer", fontWeight: 600, fontSize: "0.75rem" }}
                      onClick={() => canRegister && handleStatusToggle(s.id, s.status)}
                      title={canRegister ? "Click to toggle" : ""}
                    >
                      {s.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: "0.5rem" }}>
                    {canRegister && (
                      <button onClick={() => handleDelete(s.id)} style={{ color: "#f87171", background: "none", border: "none", cursor: "pointer" }}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}