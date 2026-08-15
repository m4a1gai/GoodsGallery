import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ImageCropper from "../components/ImageCropper";
import { acceptCandidate, editCandidateImages, fetchCandidates, rejectCandidate } from "../api/review";
import type { Candidate } from "../types";

export default function ReviewQueue() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cropCandidateId, setCropCandidateId] = useState<number | null>(null);

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

  async function handleCropConfirm(candidateId: number, dataUrl: string) {
    const candidate = candidates.find((c) => c.id === candidateId);
    if (!candidate) return;
    const newImages = [{ url: dataUrl }, ...candidate.images];
    try {
      const updated = await editCandidateImages(candidateId, newImages);
      setCandidates((prev) => prev.map((c) => (c.id === candidateId ? updated : c)));
    } catch (e) {
      setError(String(e));
    } finally {
      setCropCandidateId(null);
    }
  }

  const cropCandidate = candidates.find((c) => c.id === cropCandidateId);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Review Queue</h1>
      <p style={{ color: "var(--text-muted)", marginTop: -8 }}>
        New candidates: {candidates.length}. 这些数据来自 pipeline（目前为 seed mock 数据 / 手动导入 / bushiroad_store
        自动爬取），确认后才会进入 Global Catalog。图片是整盒/多人商品照的话，先用 Crop 截出你要的那一张再 Accept。
      </p>

      {error && <p style={{ color: "#e07a7a" }}>{error}</p>}

      {candidates.length === 0 ? (
        <p className="empty-state">No pending candidates.</p>
      ) : (
        candidates.map((c) => (
          <div key={c.id} className="review-card">
            <Link to={`/review/${c.id}`} style={{ display: "contents" }}>
              {c.images[0] && <img src={c.images[0].url} alt="" />}
            </Link>
            <div style={{ flex: 1 }}>
              <Link to={`/review/${c.id}`} style={{ color: "inherit", textDecoration: "none" }}>
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
              </Link>
              <div className="review-actions">
                <button className="btn primary" disabled={busyId === c.id} onClick={() => handle(c.id, "accept")}>
                  Accept
                </button>
                <button className="btn danger" disabled={busyId === c.id} onClick={() => handle(c.id, "reject")}>
                  Reject
                </button>
                {c.images[0] && (
                  <button className="btn" disabled={busyId === c.id} onClick={() => setCropCandidateId(c.id)}>
                    Crop image
                  </button>
                )}
              </div>
            </div>
          </div>
        ))
      )}

      {cropCandidate && cropCandidate.images[0] && (
        <ImageCropper
          src={cropCandidate.images[0].url}
          onClose={() => setCropCandidateId(null)}
          onConfirm={(dataUrl) => handleCropConfirm(cropCandidate.id, dataUrl)}
        />
      )}
    </div>
  );
}
