import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCatalogItems, fetchCharacters, fetchItemTypes } from "../api/catalog";
import type { CatalogItemListItem, Character, ItemType } from "../types";

export default function CatalogHome() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [itemTypes, setItemTypes] = useState<ItemType[]>([]);
  const [items, setItems] = useState<CatalogItemListItem[]>([]);
  const [characterId, setCharacterId] = useState<number | undefined>(undefined);
  const [characterMode, setCharacterMode] = useState<"includes" | "exact">("includes");
  const [itemTypeId, setItemTypeId] = useState<number | undefined>(undefined);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchCharacters(), fetchItemTypes()])
      .then(([chars, types]) => {
        setCharacters(chars);
        setItemTypes(types);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchCatalogItems({ characterId, characterMode, itemTypeId, search: search || undefined })
      .then(setItems)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [characterId, characterMode, itemTypeId, search]);

  const characterById = Object.fromEntries(characters.map((c) => [c.id, c]));

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Poppin'Party Collection</h1>
      <p style={{ color: "var(--text-muted)", marginTop: -8 }}>
        戸山香澄 × 市ヶ谷有咲 — Global Catalog. 拥有状态在「My Collection」单独维护。
      </p>

      {error && <p style={{ color: "#e07a7a" }}>{error}</p>}

      <div className="filters-bar">
        <button
          className={`chip ${characterId === undefined ? "active" : ""}`}
          onClick={() => setCharacterId(undefined)}
        >
          All
        </button>
        {characters.map((c) => (
          <button
            key={c.id}
            className={`chip ${characterId === c.id ? "active" : ""}`}
            onClick={() => setCharacterId(c.id)}
          >
            {c.japanese_name ?? c.name}
          </button>
        ))}

        {characterId !== undefined && (
          <select value={characterMode} onChange={(e) => setCharacterMode(e.target.value as "includes" | "exact")}>
            <option value="includes">Includes (含多人商品)</option>
            <option value="exact">Exact (仅单人商品)</option>
          </select>
        )}

        <select
          value={itemTypeId ?? ""}
          onChange={(e) => setItemTypeId(e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">All types</option>
          {itemTypes.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label_ja ?? t.label_en}
            </option>
          ))}
        </select>

        <input
          type="search"
          placeholder="Search name / series..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="empty-state">Loading...</p>
      ) : items.length === 0 ? (
        <p className="empty-state">No items match these filters.</p>
      ) : (
        <div className="grid">
          {items.map((item) => (
            <Link key={item.id} to={`/items/${item.id}`} className="card">
              {item.primary_image_url && <img src={item.primary_image_url} alt={item.canonical_name} />}
              <div className="card-body">
                <div className="card-title">{item.japanese_name ?? item.canonical_name}</div>
                <div className="card-meta">
                  <span>{item.character_ids.map((id) => characterById[id]?.name?.split(" ")[0]).join(" / ")}</span>
                  <span>{item.official_price ? `¥${item.official_price}` : "—"}</span>
                </div>
                <div className="completeness-bar">
                  <div style={{ width: `${Math.round(item.data_completeness * 100)}%` }} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
