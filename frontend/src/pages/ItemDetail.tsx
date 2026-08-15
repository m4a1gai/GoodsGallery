import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchCatalogItem, fetchCharacters } from "../api/catalog";
import { fetchCollection, updateCollection } from "../api/collection";
import type { CatalogItemDetail, Character, CollectionStatus, UserCollection } from "../types";

export default function ItemDetail() {
  const { id } = useParams<{ id: string }>();
  const itemId = Number(id);
  const [item, setItem] = useState<CatalogItemDetail | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [collection, setCollection] = useState<UserCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalogItem(itemId).then(setItem).catch((e) => setError(String(e)));
    fetchCharacters().then(setCharacters).catch(() => {});
    fetchCollection()
      .then((rows) => setCollection(rows.find((r) => r.catalog_item_id === itemId) ?? null))
      .catch(() => {});
  }, [itemId]);

  async function setStatus(status: CollectionStatus) {
    const updated = await updateCollection(itemId, {
      status,
      quantity: status === "owned" ? Math.max(1, collection?.quantity ?? 1) : collection?.quantity ?? 0,
    });
    setCollection(updated);
  }

  if (error) return <p style={{ color: "#e07a7a" }}>{error}</p>;
  if (!item) return <p className="empty-state">Loading...</p>;

  const characterById = Object.fromEntries(characters.map((c) => [c.id, c]));

  return (
    <div>
      <Link to="/" style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
        ← Back to Catalog
      </Link>

      <div style={{ display: "flex", gap: "2rem", marginTop: "1rem", flexWrap: "wrap" }}>
        <div style={{ flex: "0 0 320px" }}>
          {item.images.length > 0 ? (
            <img
              src={item.images.find((i) => i.is_primary)?.image_url ?? item.images[0].image_url}
              alt={item.canonical_name}
              style={{ width: "100%", borderRadius: 10, background: "#000" }}
            />
          ) : (
            <div className="empty-state">No image</div>
          )}
          {item.images.length > 1 && (
            <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.5rem" }}>
              {item.images.map((img) => (
                <img key={img.id} src={img.image_url} alt="" style={{ width: 56, height: 56, borderRadius: 6, objectFit: "cover" }} />
              ))}
            </div>
          )}
        </div>

        <div style={{ flex: "1 1 320px" }}>
          <h1 style={{ marginTop: 0, marginBottom: 4 }}>{item.japanese_name ?? item.canonical_name}</h1>
          {item.japanese_name && <p style={{ color: "var(--text-muted)", marginTop: 0 }}>{item.canonical_name}</p>}

          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "1rem" }}>
            {item.character_ids.map((cid) => (
              <span key={cid} className="chip active">
                {characterById[cid]?.japanese_name ?? characterById[cid]?.name ?? cid}
              </span>
            ))}
          </div>

          <table style={{ width: "100%", fontSize: "0.9rem", borderCollapse: "collapse" }}>
            <tbody>
              <Row label="Series" value={item.series} />
              <Row label="Manufacturer" value={item.manufacturer} />
              <Row label="Release date" value={item.release_date} />
              <Row label="Official price" value={item.official_price ? `¥${item.official_price}` : null} />
              <Row label="Product number" value={item.product_number} />
            </tbody>
          </table>

          <div style={{ margin: "1rem 0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: 4 }}>
              <span>Data completeness</span>
              <span>{Math.round(item.data_completeness * 100)}%</span>
            </div>
            <div className="completeness-bar">
              <div style={{ width: `${Math.round(item.data_completeness * 100)}%` }} />
            </div>
            {item.missing_fields.length > 0 && (
              <p style={{ fontSize: "0.8rem", color: "var(--warn)", marginTop: 6 }}>
                Missing: {item.missing_fields.join(", ")}
              </p>
            )}
          </div>

          <div className="status-btn-group" style={{ marginBottom: "1.5rem" }}>
            <button
              className={`status-btn ${collection?.status === "owned" ? "active-owned" : ""}`}
              onClick={() => setStatus("owned")}
            >
              ✓ Owned{collection?.status === "owned" && collection.quantity > 1 ? ` ×${collection.quantity}` : ""}
            </button>
            <button
              className={`status-btn ${collection?.status === "wishlist" ? "active-wishlist" : ""}`}
              onClick={() => setStatus("wishlist")}
            >
              ♡ Wishlist
            </button>
            <button className="status-btn" onClick={() => setStatus("not_owned")}>
              ○ Not owned
            </button>
          </div>

          <h3 style={{ marginBottom: "0.5rem" }}>Sources</h3>
          {item.item_sources.length === 0 ? (
            <p className="empty-state">No linked sources yet.</p>
          ) : (
            <ul style={{ paddingLeft: "1.1rem", fontSize: "0.88rem" }}>
              {item.item_sources.map((s) => (
                <li key={s.id}>
                  <a href={s.source_url} target="_blank" rel="noreferrer">
                    {s.source_url}
                  </a>
                  {s.source_price && <span style={{ color: "var(--text-muted)" }}> — ¥{s.source_price}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
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
