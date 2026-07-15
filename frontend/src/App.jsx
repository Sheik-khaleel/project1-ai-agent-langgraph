import { useState } from "react";
import { sendQuery } from "./api.js";

const DEFAULT_MESSAGE = "please ingest todos";

export default function App() {
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const [limit, setLimit] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = await sendQuery(message, limit);
      setResult(payload);
      setHistory((prev) => [payload, ...prev].slice(0, 5));
    } catch (err) {
      setError(err?.response?.data?.detail ?? err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Agentic Orchestrator Console</h1>
        <p>Trigger the Fetch→Transform→Sink pipeline and monitor responses.</p>
      </header>

      <main className="main">
        <section className="panel form-panel">
          <h2>Send Request</h2>
          <form onSubmit={handleSubmit} className="query-form">
            <label htmlFor="message">Message</label>
            <textarea
              id="message"
              className="input textarea"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={3}
            />

            <label htmlFor="limit">Limit</label>
            <input
              id="limit"
              className="input"
              type="number"
              min="1"
              max="20"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            />

            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Submitting..." : "Submit"}
            </button>
          </form>

          {error && <p className="error">{Array.isArray(error) ? error.join(", ") : error}</p>}
        </section>

        <section className="panel result-panel">
          <h2>Latest Response</h2>

          {!loading && !result && !error && (
            <div className="placeholder-card">
              <p>Submit a request to view orchestration results.</p>
            </div>
          )}

          {loading && (
            <div className="placeholder-card">
              <div className="spinner" aria-hidden />
              <p>Orchestrating agents&hellip;</p>
            </div>
          )}

          {result && (
            <div className="result-card">
              <header>
                <span className={`status-pill status-${result.status}`}>{result.status}</span>
                <span className="limit-pill">limit {result.limit ?? "?"}</span>
              </header>

              <section>
                <h3>Records</h3>
                {result.records?.length ? (
                  <ul className="record-list">
                    {result.records.map((record) => (
                      <li key={record.source_id ?? record.title} className="record-item">
                        <div className="record-title">{record.title}</div>
                        <div className="record-meta">
                          <span>ID: {record.source_id ?? "n/a"}</span>
                          <span className={`badge badge-${record.status}`}>{record.status}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No records returned.</p>
                )}
              </section>

              {result.sink_result && (
                <section className="sink-summary">
                  <h3>Sink Response</h3>
                  <pre>{JSON.stringify(result.sink_result, null, 2)}</pre>
                </section>
              )}
            </div>
          )}
        </section>

        <section className="panel history-panel">
          <h2>Recent Runs</h2>
          {history.length === 0 ? (
            <p className="muted">No history yet.</p>
          ) : (
            <ul className="history-list">
              {history.map((entry, index) => (
                <li key={`${entry.status}-${index}`} className="history-item">
                  <div>
                    <span className={`status-pill status-${entry.status}`}>{entry.status}</span>
                    <span className="muted"> limit {entry.limit}</span>
                  </div>
                  <small>{entry.records?.length ?? 0} records</small>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>Agentic Demo UI • React + Vite</span>
      </footer>
    </div>
  );
}
