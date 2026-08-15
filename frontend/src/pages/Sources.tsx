import { useEffect, useState } from "react";
import { fetchSources } from "../api/sources";
import type { Source } from "../types";

const POLICY_LABEL: Record<Source["crawl_policy"], string> = {
  auto: "Auto crawl",
  search_discovery_only: "Search discovery only",
  manual_import_only: "Manual import only",
  disabled: "Disabled",
};

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    fetchSources().then(setSources);
  }, []);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Data Sources</h1>
      <p style={{ color: "var(--text-muted)", marginTop: -8, maxWidth: 640 }}>
        每个来源的 crawl policy 决定 pipeline 能否自动抓取它。第一阶段没有任何来源被验证为可以自动爬取，全部是{" "}
        <code>manual_import_only</code> 或 <code>search_discovery_only</code>——需要逐个确认 robots.txt / ToS 之后才会打开
        Auto crawl。
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
                <button className="btn" disabled title="仅在该来源的 crawl_policy = auto 时可用，目前尚未开放任何来源">
                  Run Crawl
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
