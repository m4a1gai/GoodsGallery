import { useEffect, useState } from "react";
import { fetchSources, triggerCrawl, type CrawlResult } from "../api/sources";
import type { Source } from "../types";

const POLICY_LABEL: Record<Source["crawl_policy"], string> = {
  auto: "Auto crawl",
  search_discovery_only: "Search discovery only",
  manual_import_only: "Manual import only",
  disabled: "Disabled",
};

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [openCrawlFor, setOpenCrawlFor] = useState<string | null>(null);
  const [startUrl, setStartUrl] = useState("");
  const [maxPages, setMaxPages] = useState(3);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CrawlResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    fetchSources().then(setSources);
  }

  useEffect(load, []);

  function openCrawlForm(key: string, defaultUrl: string) {
    setOpenCrawlFor(key);
    setStartUrl(defaultUrl);
    setResult(null);
    setError(null);
  }

  async function runCrawl(key: string) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await triggerCrawl(key, { start_url: startUrl, max_pages: maxPages });
      setResult(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Data Sources</h1>
      <p style={{ color: "var(--text-muted)", marginTop: -8, maxWidth: 640 }}>
        每个来源的 crawl policy 决定 pipeline 能否自动抓取它。只有明确检查过 robots.txt / ToS 的来源才会被设为{" "}
        <code>auto</code>——其余都是 <code>manual_import_only</code> 或 <code>search_discovery_only</code>。Run Crawl
        只会抓你指定的这一个 collection 页面（走它的分页），不是后台定时任务。
      </p>

      <table className="source-table">
        <thead>
          <tr>
            <th>Source</th>
            <th>Kind</th>
            <th>Policy</th>
            <th>Trust priority</th>
            <th>Notes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.id}>
              <td>
                {s.base_url ? (
                  <a href={s.base_url} target="_blank" rel="noreferrer">
                    {s.name}
                  </a>
                ) : (
                  s.name
                )}
              </td>
              <td>{s.kind}</td>
              <td>
                <span className={`policy-tag policy-${s.crawl_policy}`}>{POLICY_LABEL[s.crawl_policy]}</span>
              </td>
              <td>{s.trust_priority}</td>
              <td style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: 360 }}>{s.notes}</td>
              <td>
                {s.crawl_policy === "auto" ? (
                  <button className="btn primary" onClick={() => openCrawlForm(s.key, s.base_url ?? "")}>
                    Run Crawl
                  </button>
                ) : (
                  <button className="btn" disabled title="仅在该来源的 crawl_policy = auto 时可用">
                    Run Crawl
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {openCrawlFor && (
        <div className="review-card" style={{ marginTop: "1.5rem", flexDirection: "column", gap: "0.6rem" }}>
          <strong>Run crawl: {openCrawlFor}</strong>
          <label style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Collection / category URL
            <input
              type="text"
              style={{ display: "block", width: "100%", marginTop: 4 }}
              value={startUrl}
              onChange={(e) => setStartUrl(e.target.value)}
            />
          </label>
          <label style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Max pages
            <input
              type="text"
              inputMode="numeric"
              style={{ display: "block", width: 80, marginTop: 4 }}
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value) || 1)}
            />
          </label>
          <div className="review-actions">
            <button className="btn primary" disabled={busy || !startUrl} onClick={() => runCrawl(openCrawlFor)}>
              {busy ? "Crawling..." : "Start"}
            </button>
            <button className="btn" onClick={() => setOpenCrawlFor(null)}>
              Close
            </button>
          </div>
          {error && <p style={{ color: "#e07a7a", fontSize: "0.85rem" }}>{error}</p>}
          {result && (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              Discovered {result.discovered} · created {result.created} · already seen {result.skipped_already_seen} ·
              errors {result.errors}. 新 candidate 已经进入 <a href="/review">Review Queue</a>。
            </p>
          )}
        </div>
      )}
    </div>
  );
}
