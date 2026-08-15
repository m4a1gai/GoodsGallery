import { useEffect, useState } from "react";
import { acceptCandidate, fetchCandidates, rejectCandidate } from "../api/review";
import type { Candidate } from "../types";

export default function ReviewQueue() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    fetchCandidates("pending").then(setCandidates).catch((e) => setError(String(e)));
  }

  useEffect(load, []);

  async function handle(id: number, action: "accept" | "reject") {
    setBusyId(id);
    try {
      if (action === "accept") await acceptCandidate(id);
      else await rejectCandidate(id, "Rejected from Review Queue UI");
      setCandidates((prev) => prev.filter((c) => c.id !== id));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Review Queue</h1>
      <p style={{ color: "var(--text-muted)", marginTop: -8 }}>
        New candidates: {candidates.length}. 这些数据来自 pipeline（目前为 seed mock 数据 / 手动导入），确认后才会进入
        Global Catalog。
      </p>

      {error && <p style={{ color: "#e07a7a" }}>{error}</p>}

      {candidates.length === 0 ? (
        <p className="empty-state">No pending candidates.</p>
      ) : (
        candidates.map((c) => (
          <div key={c.id} className="review-card">
            {c.images[0] && <img src={c.images[0].url} alt="" />}
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div>
                  <strong>{c.japanese_name ?? c.canonical_name}</strong>
                  {c.japanese_name && (
                    <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{c.canonical_name}</div>
                  )}
                </div>
                <span className="confidence-tag">confidence {c.confidence.toFixed(2)}</span>
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                {c.price ? `¥${c.price}` : "price unknown"} · raw_product #{c.raw_product_id}
                {c.product_number ? ` · ${c.product_number}` : ""}
              </div>
              <div className="review-actions">
                <button className="btn primary" disabled={busyId === c.id} onClick={() => handle(c.id, "accept")}>
                  Accept
                </button>
                <button className="btn danger" disabled={busyId === c.id} onClick={() => handle(c.id, "reject")}>
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
