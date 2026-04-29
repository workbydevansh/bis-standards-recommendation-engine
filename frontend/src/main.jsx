import React from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  Clock3,
  Copy,
  FileSearch,
  Gauge,
  Layers3,
  Loader2,
  Play,
  RotateCcw,
  Search,
  ShieldCheck
} from "lucide-react";
import "./styles.css";

const examples = [
  "33 Grade Ordinary Portland Cement for chemical and physical compliance",
  "Coarse and fine aggregates from natural sources for structural concrete",
  "Precast concrete pipes with and without reinforcement for water mains",
  "Hollow and solid lightweight concrete masonry blocks",
  "White Portland cement for architectural and decorative purposes"
];

const initialResults = [
  {
    standard_id: "IS 269: 1989",
    title: "Ordinary Portland Cement, 33 Grade",
    score: 84.6623,
    rationale:
      "IS 269: 1989 - Ordinary Portland Cement, 33 Grade: strong title term coverage, cement type matched, 33 grade matched.",
    pages: [22, 23]
  },
  {
    standard_id: "IS 12269: 1987",
    title: "53 Grade Ordinary Portland Cement",
    score: 80.1299,
    rationale:
      "IS 12269: 1987 - 53 Grade Ordinary Portland Cement: title terms overlap, cement type matched.",
    pages: [34]
  },
  {
    standard_id: "IS 8112: 1989",
    title: "43 Grade Ordinary Portland Cement",
    score: 79.8898,
    rationale:
      "IS 8112: 1989 - 43 Grade Ordinary Portland Cement: title terms overlap, cement type matched.",
    pages: [33]
  }
];

function App() {
  const [query, setQuery] = React.useState(examples[0]);
  const [results, setResults] = React.useState(initialResults);
  const [latency, setLatency] = React.useState(0.05);
  const [status, setStatus] = React.useState("ready");
  const [error, setError] = React.useState("");
  const [copied, setCopied] = React.useState("");

  async function runSearch(nextQuery = query) {
    if (!nextQuery.trim()) return;
    setStatus("loading");
    setError("");
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(nextQuery)}`);
      if (!response.ok) {
        throw new Error(`Search failed with HTTP ${response.status}`);
      }
      const payload = await response.json();
      setResults(payload.results || []);
      setLatency(payload.latency_seconds ?? 0);
      setStatus("ready");
    } catch (err) {
      setStatus("error");
      setError(err.message || "Unable to reach the search API");
    }
  }

  function useExample(value) {
    setQuery(value);
    runSearch(value);
  }

  async function copyJson() {
    const payload = results.map((item) => item.standard_id);
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied("standards");
    window.setTimeout(() => setCopied(""), 1400);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={22} />
          </div>
          <div>
            <p className="eyebrow">BIS SP 21 retrieval</p>
            <h1>BIS Standards Recommendation Engine</h1>
          </div>
        </div>
        <div className="status-strip" aria-label="System status">
          <span><ShieldCheck size={16} /> Official PDF index</span>
          <span><Gauge size={16} /> Offline scorer</span>
          <span><Clock3 size={16} /> {Number(latency).toFixed(4)}s</span>
        </div>
      </header>

      <section className="workspace">
        <aside className="query-panel" aria-label="Product query">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Product input</p>
              <h2>Describe the material</h2>
            </div>
            <button
              className="icon-button"
              type="button"
              title="Reset query"
              aria-label="Reset query"
              onClick={() => setQuery("")}
            >
              <RotateCcw size={18} />
            </button>
          </div>

          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: Portland slag cement for chemical and physical requirements"
            spellCheck="true"
          />

          <div className="action-row">
            <button className="primary-button" type="button" onClick={() => runSearch()} disabled={status === "loading"}>
              {status === "loading" ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
              Recommend standards
            </button>
            <button className="secondary-button" type="button" onClick={copyJson} disabled={!results.length}>
              <Copy size={18} />
              {copied ? "Copied" : "Copy IDs"}
            </button>
          </div>

          <div className="examples">
            <p className="section-label">Sample queries</p>
            {examples.map((example) => (
              <button key={example} type="button" onClick={() => useExample(example)}>
                <Play size={14} />
                <span>{example}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="results-panel" aria-label="Recommendation results">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Top matches</p>
              <h2>{results.length ? `${results.length} standards recommended` : "No standards yet"}</h2>
            </div>
            <div className={`run-state ${status}`}>
              {status === "loading" ? <Loader2 className="spin" size={16} /> : <CheckCircle2 size={16} />}
              {status === "loading" ? "Running" : status === "error" ? "Check API" : "Ready"}
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="metric-grid">
            <Metric icon={<Layers3 size={18} />} label="Indexed records" value="574" />
            <Metric icon={<FileSearch size={18} />} label="Public Hit@3" value="100%" />
            <Metric icon={<Clock3 size={18} />} label="Last latency" value={`${Number(latency).toFixed(3)}s`} />
          </div>

          <div className="results-list">
            {results.map((result, index) => (
              <article className="result-card" key={`${result.standard_id}-${index}`}>
                <div className="rank-badge">{index + 1}</div>
                <div className="result-content">
                  <div className="result-title-row">
                    <h3>{result.standard_id}</h3>
                    <span>Score {Number(result.score).toFixed(2)}</span>
                  </div>
                  <p className="standard-title">{result.title}</p>
                  <p className="rationale">{result.rationale}</p>
                  <div className="meta-row">
                    <span>SP 21 pages {(result.pages || []).join(", ") || "n/a"}</span>
                    <ArrowRight size={15} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);

