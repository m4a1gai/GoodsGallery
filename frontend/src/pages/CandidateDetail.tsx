import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Lightbox from "../components/Lightbox";
import { fetchCharacters, fetchItemTypes } from "../api/catalog";
import { acceptCandidate, editCandidateImages, fetchCandidate, rejectCandidate } from "../api/review";
import type { Candidate, Character, ItemType } from "../types";

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const candidateId = Number(id);
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [itemTypes, setItemTypes] = useState<ItemType[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  function reload() {
    fetchCandidate(candidateId).then(setCandidate).catch((e) => setError(String(e)));
  }

  useEffect(() => {
    reload();
    fetchCharacters().then(setCharacters).catch(() => {});
    fetchItemTypes().then(setItemTypes).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateId]);

  async function handleAccept() {
    if (!candidate) return;
    setBusy(true);
    try {
      await acceptCandidate(candidate.id);
      navigate("/review");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!candidate) return;
    setBusy(true);
    try {
      await rejectCandidate(candidate.id, "Rejected from Candidate Detail UI");
      navigate("/review");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleCropConfirm(dataUrl: string) {
    if (!candidate) return;
    const newImages = [{ url: dataUrl }, ...candidate.images];
    try {
      const updated = await editCandidateImages(candidate.id, newImages);
      setCandidate(updated);
    } catch (e) {
      setError(String(e));
    }
  }

  if (error) return <p style={{ color: "#e07a7a" }}>{error}</p>;
  if (!candidate) return <p className="empty-state">Loading...</p>;

  const characterById = Object.fromEntries(characters.map((c) => [c.id, c]));
  const itemType = itemTypes.find((t) => t.id === candidate.item_type_id);
  const primaryImage = candidate.images[0];

  return (
    <div>
      <Link to="/review" style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
        ← Back to Review Queue
      </Link>

      <div style={{ display: "flex", gap: "2rem", marginTop: "1rem", flexWrap: "wrap" }}>
        <div style={{ flex: "0 0 320px" }}>
          {primaryImage ? (
            <img
              src={primaryImage.url}
              alt={candidate.canonical_name}
              onClick={() => setLightboxSrc(primaryImage.url)}
              className="image-zoomable"
              style={{ width: "100%", borderRadius: 10, background: "#000" }}
            />
          ) : (
            <div className="empty-state">No image</div>
          )}

          {candidate.images.length > 1 && (
            <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
              {candidate.images.map((img, i) => (
                <img
                  key={i}
                  src={img.url}
                  alt=""
                  onClick={() => setLightboxSrc(img.url)}
                  className="image-zoomable"
                  style={{ width: 56, height: 56, borderRadius: 6, objectFit: "cover" }}
                />
              ))}
            </div>
          )}
        </div>

        <div style={{ flex: "1 1 320px" }}>
          <h1 style={{ marginTop: 0, marginBottom: 4 }}>{candidate.japanese_name ?? candidate.canonical_name}</h1>
          {candidate.japanese_name && (
            <p style={{ color: "var(--text-muted)", marginTop: 0 }}>{candidate.canonical_name}</p>
          )}

          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "1rem", alignItems: "center" }}>
            {candidate.character_ids.map((cid) => (
              <span key={cid} className="chip active">
                {characterById[cid]?.japanese_name ?? characterById[cid]?.name ?? cid}
              </span>
            ))}
            <span className="confidence-tag">confidence {candidate.confidence.toFixed(2)}</span>
          </div>

          <table style={{ width: "100%", fontSize: "0.9rem", borderCollapse: "collapse" }}>
            <tbody>
              <Row label="Series" value={candidate.series} />
              <Row label="Item type" value={itemType?.label_ja ?? itemType?.label_en ?? null} />
              <Row label="Manufacturer" value={candidate.manufacturer} />
              <Row label="Price" value={candidate.price ? `¥${candidate.price}` : null} />
              <Row label="Product number" value={candidate.product_number} />
              <Row label="Status" value={candidate.status} />
            </tbody>
          </table>

          <div className="review-actions" style={{ margin: "1.2rem 0" }}>
            <button className="btn primary" disabled={busy} onClick={handleAccept}>
              Accept
            </button>
            <button className="btn danger" disabled={busy} onClick={handleReject}>
              Reject
            </button>
          </div>

          <h3 style={{ marginBottom: "0.5rem" }}>Source</h3>
          {candidate.source_url ? (
            <a href={candidate.source_url} target="_blank" rel="noreferrer" style={{ fontSize: "0.88rem" }}>
              {candidate.source_url}
            </a>
          ) : (
            <p className="empty-state">No source URL.</p>
          )}
        </div>
      </div>

      {lightboxSrc && (
        <Lightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} onCrop={handleCropConfirm} />
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number | null }) {
  return (
    <tr>
      <td style={{ padding: "0.3rem 0", color: "var(--text-muted)", width: 140 }}>{label}</td>
      <td style={{ padding: "0.3rem 0" }}>{value ?? "—"}</td>
    </tr>
  );
}
