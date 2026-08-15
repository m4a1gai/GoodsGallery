import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCatalogItems } from "../api/catalog";
import { fetchCollection, fetchCollectionStats } from "../api/collection";
import type { CatalogItemListItem, CollectionStats, CollectionStatus, UserCollection } from "../types";

export default function MyCollection() {
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [collectionRows, setCollectionRows] = useState<UserCollection[]>([]);
  const [items, setItems] = useState<CatalogItemListItem[]>([]);
  const [filter, setFilter] = useState<CollectionStatus | "all">("owned");

  useEffect(() => {
    fetchCollectionStats().then(setStats);
    fetchCollection().then(setCollectionRows);
    fetchCatalogItems({}).then(setItems);
  }, []);

  const byItemId = Object.fromEntries(collectionRows.map((r) => [r.catalog_item_id, r]));
  const visible = items.filter((item) => {
    const row = byItemId[item.id];
    if (filter === "all") return true;
    if (filter === "owned") return row?.status === "owned";
    if (filter === "wishlist") return row?.status === "wishlist";
    return !row || row.status === "not_owned";
  });

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>My Collection</h1>

      {stats && (
        <div className="stats-row">
          <StatTile label="Catalog" value={stats.catalog_total} />
          <StatTile label="Owned" value={stats.owned_total} />
          <StatTile label="Wishlist" value={stats.wishlist_total} />
          <StatTile label="Completion" value={`${stats.completion_pct}%`} />
          <StatTile label="Total spent" value={`¥${stats.total_spent.toLocaleString()}`} />
        </div>
      )}

      {stats && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "0.5rem" }}>By character</h3>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            {Object.entries(stats.by_character).map(([name, v]) => (
              <span key={name} className="chip">
                {name}: {v.owned} / {v.total}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="filters-bar">
        {(["owned", "wishlist", "not_owned", "all"] as const).map((f) => (
          <button key={f} className={`chip ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
            {f === "owned" ? "Owned" : f === "wishlist" ? "Wishlist" : f === "not_owned" ? "Not owned" : "All"}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="empty-state">Nothing here yet.</p>
      ) : (
        <div className="grid">
          {visible.map((item) => (
            <Link key={item.id} to={`/items/${item.id}`} className="card">
              {item.primary_image_url && <img src={item.primary_image_url} alt={item.canonical_name} />}
              <div className="card-body">
                <div className="card-title">{item.japanese_name ?? item.canonical_name}</div>
                <div className="card-meta">
                  <span>{byItemId[item.id]?.status ?? "not_owned"}</span>
                  <span>{item.official_price ? `¥${item.official_price}` : "—"}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-tile">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
