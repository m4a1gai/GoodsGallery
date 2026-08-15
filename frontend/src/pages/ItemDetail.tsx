import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ImageCropper from "../components/ImageCropper";
import Lightbox from "../components/Lightbox";
import {
  addCatalogItemImage,
  deleteCatalogItemImage,
  fetchCatalogItem,
  fetchCharacters,
  setPrimaryCatalogItemImage,
} from "../api/catalog";
import { fetchCollection, updateCollection } from "../api/collection";
import type { CatalogItemDetail, Character, CollectionStatus, UserCollection } from "../types";

export default function ItemDetail() {
  const { id } = useParams<{ id: string }>();
  const itemId = Number(id);
  const [item, setItem] = useState<CatalogItemDetail | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [collection, setCollection] = useState<UserCollection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cropperSrc, setCropperSrc] = useState<string | null>(null);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  function reloadItem() {
    fetchCatalogItem(itemId).then(setItem).catch((e) => setError(String(e)));
  }

  useEffect(() => {
    reloadItem();
    fetchCharacters().then(setCharacters).catch(() => {});
    fetchCollection()
      .then((rows) => setCollection(rows.find((r) => r.catalog_item_id === itemId) ?? null))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId]);

  async function setStatus(status: CollectionStatus) {
    const updated = await updateCollection(itemId, {
      status,
      quantity: status === "owned" ? Math.max(1, collection?.quantity ?? 1) : collection?.quantity ?? 0,
    });
    setCollection(updated);
  }

  async function makePrimary(imageId: number) {
    await setPrimaryCatalogItemImage(itemId, imageId);
    reloadItem();
  }

  async function removeImage(imageId: number) {
    await deleteCatalogItemImage(itemId, imageId);
    reloadItem();
  }

  async function handleCropConfirm(dataUrl: string) {
    await addCatalogItemImage(itemId, { image_url: dataUrl, is_primary: true });
    setCropperSrc(null);
    reloadItem();
  }

  if (error) return <p style={{ color: "#e07a7a" }}>{error}</p>;
  if (!item) return <p className="empty-state">Loading...</p>;

  const characterById = Object.fromEntries(characters.map((c) => [c.id, c]));
  const primaryImage = item.images.find((i) => i.is_primary) ?? item.images[0];

  return (
    <div>
      <Link to="/" style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
        ← Back to Catalog
      </Link>

      <div style={{ display: "flex", gap: "2rem", marginTop: "1rem", flexWrap: "wrap" }}>
        <div style={{ flex: "0 0 320px" }}>
          {primaryImage ? (
            <img
              src={primaryImage.image_url}
              alt={item.canonical_name}
              onClick={() => setLightboxSrc(primaryImage.image_url)}
              className="image-zoomable"
              style={{ width: "100%", borderRadius: 10, background: "#000" }}
            />
          ) : (
            <div className="empty-state">No image</div>
          )}

          {item.images.length > 0 && (
            <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
              {item.images.map((img) => (
                <div key={img.id} style={{ position: "relative" }}>
                  <img
                    src={img.image_url}
                    alt=""
                    onClick={() => makePrimary(img.id)}
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 6,
                      objectFit: "cover",
                      cursor: "pointer",
                      border: img.is_primary ? "2px solid var(--accent)" : "2px solid transparent",
                    }}
                  />
                  <button
                    onClick={() => removeImage(img.id)}
                    title="Remove image"
                    style={{
                      position: "absolute",
                      top: -6,
                      right: -6,
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      border: "none",
                      background: "var(--surface-hover)",
                      color: "var(--text-muted)",
                      fontSize: "0.7rem",
                      lineHeight: "18px",
                      padding: 0,
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {primaryImage && (
            <button className="btn" style={{ marginTop: "0.6rem" }} onClick={() => setCropperSrc(primaryImage.image_url)}>
              Crop new image from this
            </button>
          )}
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
            点缩略图设为头图；整盒/多人商品照可以用 Crop 截出这个角色的部分再设为头图。
          </p>
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

      {cropperSrc && (
        <ImageCropper src={cropperSrc} onClose={() => setCropperSrc(null)} onConfirm={handleCropConfirm} />
      )}
      {lightboxSrc && <Lightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />}
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
