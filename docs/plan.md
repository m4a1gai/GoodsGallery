# Poppin'Party 谷子数据库 (GoodsGallery) — 架构与第一阶段实现计划

## Context

仓库目前完全为空（只有 IntelliJ 的 `.idea` 元数据，无代码、无 commit、无技术栈）。用户希望的不是一个"收藏相册"，而是一个可长期维护的两层系统：

1. **Global Catalog**（客观存在的商品图鉴，不含个人状态）
2. **Personal Collection**（用户是否拥有/心愿单/购买记录，与 Catalog 分离）

并且 Catalog 的数据来源不能完全靠手动录入，而要通过一个 **Source → Raw → Normalize → Dedup → Confidence → Review Queue → Catalog** 的流水线来发现和整理商品，人工只做最后确认。第一阶段角色范围：户山香澄、市谷有咲（Poppin'Party），但数据模型要能扩展到任意角色/乐队。

技术栈已与用户确认：**前后端分离，PostgreSQL**。后端语言选 **Python**，理由：爬虫/清洗/去重管线是本项目最核心也最难的部分，需要 `httpx`/`selectolax`/`BeautifulSoup`（解析）、`Pillow` + `imagehash`（图片感知哈希去重）、`rapidfuzz`（名称相似度）、可选 `sentence-transformers`（未来图像/文本 embedding）——Python 生态在这些方面明显强于 Node，且能避免爬虫服务和 API 服务分成两种语言的维护成本。前端用 React + TypeScript + Vite。

对候选数据源做了初步 robots.txt 抽查（非最终结论，实现时每个 Source Adapter 仍需单独复核 ToS）：
- **suruga-ya.jp**：对通用 UA 是 `Allow: /`，仅针对具名 AI 爬虫（ClaudeBot/GPTBot/CCBot 等）加了 `Content-Signal: ai-train=no, use=reference`。用自己的 UA、低频率抓取，且仅做"参考编目"用途，与该站点声明的 `use=reference` 是一致的，但仍需在实现时人工确认一次 ToS。
- **jp.mercari.com**：robots.txt 对通用 UA 只 disallow 账户/交易/内部 API 路径，商品页本身没被 disallow；但二手交易平台的 ToS 通常明确禁止自动化抓取，建议先按"仅手动 URL 导入"处理，不做自动爬取。
- **amiami.com / animate-onlineshop.jp / mandarake**：robots.txt 抓取未成功（空响应 / 403 / 跳转），说明这些站点对自动化请求本身就比较敏感，实现时需要人工逐一确认，第一阶段先归类为"手动导入 or 待验证"，不默认可自动爬。
- **BanG Dream! / Bushiroad 官方商品页**：搜索没能直接定位到官方 goods 页面的稳定 URL，需要在实现 Source Adapter 时人工找到具体入口并单独检查 robots.txt。

结论：**第一阶段不会对任何第三方网站跑真实的自动化爬取**。会把 Source Adapter 接口、Raw/Candidate 数据模型、Review Queue 全部搭好，但真实上线的 adapter 只接入"确认安全"的来源，且默认用**手动 URL 导入 + 搜索引擎 discovery**这两种最保守的方式先跑通 pipeline，自动 crawl 等用户对具体来源逐个拍板后再开。这与用户反复强调的"宁可少爬、不要爬错"原则一致。

## 架构总览

```
Internet
   │
   ▼
┌─────────────────────────────────────────┐
│ Discovery                                │  手动 URL / 搜索引擎结果 / (未来) 站内 adapter
└─────────────────────────────────────────┘
   │
   ▼
RawProduct (原始快照，永不覆盖，带 parserVersion)
   │  normalize (per-source parser)
   ▼
Candidate (标准化后的候选商品 + confidence)
   │  entity resolution / dedup
   ▼
┌───────────────┐      ┌─────────────────────────┐
│ High confidence│ ───▶ │ CatalogItem (自动确认)   │
│ Medium confidence│──▶ │ Review Queue (人工确认)  │
│ Low confidence │ ───▶ │ 留在 Candidate，不进图鉴 │
└───────────────┘      └─────────────────────────┘
                              │ Accept/Merge/Reject/Edit
                              ▼
                        CatalogItem ── CatalogItemSource[] (多来源追溯)
                              │
                              ▼
                   UserCollection (owned/wishlist/quantity/notes)
```

两个系统的边界：`CatalogItem` 永远不包含 `owned`/`purchasePrice` 等个人字段；`UserCollection` 只存 `catalogItemId` + 个人状态，一对一关联但物理表分离，方便未来把 Catalog 公开而不泄露个人收藏。

## 数据模型（PostgreSQL）

核心表（用 SQLAlchemy + Alembic 迁移）：

- `character(id, name, japanese_name, english_name, aliases[], band_id, sort_order)` — 角色可扩展，非写死两个人
- `band(id, name, japanese_name)` — 为未来乐队扩展预留
- `source(id, name, kind[official|manufacturer|retailer|secondhand|search|user_submitted], base_url, trust_priority, crawl_policy[auto|search_discovery_only|manual_import_only|disabled], robots_checked_at, notes)`
- `raw_product(id, source_id, source_url, crawled_at, raw_title, raw_description, raw_price, raw_currency, raw_images jsonb, raw_metadata jsonb, raw_html_hash, parser_version, content_hash, etag, last_modified)` — 只追加，不覆盖
- `candidate(id, raw_product_id, canonical_name, japanese_name, character_ids[], series, item_type, manufacturer, release_date, price, currency, product_number, images jsonb, confidence, status[pending|accepted|rejected|merged], reviewed_at, review_note)`
- `catalog_item(id, canonical_name, japanese_name, original_title, translated_title, translation_source, character_ids[], band_id, series, item_type, manufacturer, release_date, release_date_source, release_date_confidence, official_price, currency, product_number, data_completeness, created_by, updated_by, created_at, updated_at)`
- `catalog_item_image(id, catalog_item_id, image_url, source_id, source_item_url, is_primary)` — 图片 metadata 和图片本体分离，不擅自存储/再分发受限图片
- `catalog_item_source(catalog_item_id, source_id, source_url, source_price, last_seen_at)` — 一个商品多来源
- `duplicate_review_pair(id, candidate_id, matched_catalog_item_id, similarity_score, match_reason, status[pending|same|different])` — 疑似重复人工确认队列
- `user_collection(id, catalog_item_id, status[owned|wishlist|not_owned], quantity, purchase_price, currency, purchase_date, purchase_source, notes)`
- `price_history(id, catalog_item_id, source_id, price, currency, observed_at)` — 表先建，第一阶段不强制填充

`item_type` 用可扩展的查找表而不是硬编码 enum（`item_type(id, code, label_en, label_ja)`），方便以后加新类型。

## 后端结构（FastAPI）

```
backend/
  app/
    main.py
    api/            # catalog, collection, review, sources 路由
    models/         # SQLAlchemy models
    schemas/        # Pydantic schemas
    services/
      catalog.py
      collection.py
      review.py
  pipeline/
    sources/
      base.py        # SourceAdapter Protocol
      manual_import.py   # 第一个 adapter：粘贴 URL 手动解析公开 HTML
      search_discovery.py # 用搜索结果做 discovery，不直接爬站内
    normalize/
      normalizer.py   # RawProduct -> Candidate
    dedup/
      matcher.py      # 名称相似度(rapidfuzz) + 图片哈希(imagehash) + 商品编号
    crawl_runner.py   # 编排：discovery -> raw -> normalize -> dedup -> queue
  alembic/
  tests/
```

### Source Adapter 接口（核心抽象）

```python
class SourceAdapter(Protocol):
    source_key: str
    crawl_policy: CrawlPolicy  # auto | search_discovery_only | manual_import_only | disabled

    async def discover(self, params: DiscoveryParams) -> list[DiscoveredUrl]: ...
    async def fetch(self, url: str, etag: str | None) -> FetchResult | NotModified: ...
    def parse(self, fetch_result: FetchResult) -> RawProductDraft: ...
```

每个 adapter 自己声明 `crawl_policy`，`crawl_runner` 在执行前检查该字段，`disabled`/`manual_import_only` 的来源不会被自动调度，只能通过"粘贴 URL"手动触发 `fetch+parse`。所有 adapter 共用一个带并发限制、延迟、指数退避、429 降速的 HTTP client（`pipeline/http.py`），并遵守 `robots.txt`（用 `urllib.robotparser` 在 adapter 初始化时检查一次并写回 `source.robots_checked_at`）。

### 去重策略（`pipeline/dedup/matcher.py`）

按可信度顺序：
1. `product_number` 完全一致 → 强匹配
2. 稳定的来源商品 ID/URL 一致 → 强匹配
3. `rapidfuzz` 名称相似度（含别名归一化）+ 角色/系列/类型一致 → 中等信号
4. 图片感知哈希（`imagehash.phash`）相似度 → 辅助信号，绝不单独作为合并依据
5. 综合打分得出 `confidence`：
   - `>= 0.9` 自动写入/更新 `catalog_item`（含来源合并）
   - `0.6–0.9` 写入 `duplicate_review_pair`，人工在 Review Queue 选 `Same Item` / `Different Item`
   - `< 0.6` 保留在 `candidate`，不进图鉴

### Review Queue

`api/review.py` 提供：`GET /candidates?status=pending`、`POST /candidates/{id}/accept`、`/reject`、`/edit`、`/merge`、`duplicate_review_pair` 同理。前端一个 `ReviewQueue` 页面，卡片式展示（图片/名称/来源/confidence + Accept/Reject/Edit/Duplicate 按钮），操作直接调用上述 API。

## 前端结构（React + TS + Vite）

```
frontend/
  src/
    pages/
      CatalogHome.tsx       # 角色筛选(All/香澄/有咲/两人/全员, Exact/Includes) + 搜索 + 网格
      ItemDetail.tsx        # 图片 gallery、多来源列表、data completeness、收藏操作
      MyCollection.tsx      # owned/wishlist 筛选、统计
      ReviewQueue.tsx       # 人工审核
      Sources.tsx           # 数据源管理：last crawl / policy / Run Crawl(仅对 auto 来源可用)
    api/                    # 简单 fetch wrapper
    types/
```

筛选逻辑（`characterIds` 数组 + Exact/Includes）放在后端查询层（Postgres `@>`/`&&` 数组操作符），不要在前端 `items.filter`，为未来上千条数据的全文搜索/索引留空间（第一阶段可以先用 Postgres `ILIKE` + trigram index，不引入 Elasticsearch）。

## 本次实现范围（P0 + 爬虫骨架，不含真实自动爬取）

1. 项目脚手架：`backend/`(FastAPI + SQLAlchemy + Alembic) + `frontend/`(Vite + React + TS)，docker-compose 起本地 Postgres
2. 数据模型 + 首个 migration（上面列出的全部表）
3. Seed script：写入 Character(Kasumi/Arisa/Poppin'Party 5人)、Source(占位)、约 10-12 条 mock CatalogItem（5 个 Kasumi 单人、5 个 Arisa 单人、2 个多人商品）+ mock UserCollection 状态
4. 后端 API：catalog（列表+筛选+详情）、collection（状态更新）、review（候选队列 CRUD，先用 mock candidate 数据）、sources（列表 + policy 展示）
5. 前端页面：CatalogHome、ItemDetail、MyCollection、ReviewQueue（用 mock candidate）、Sources（只读展示，Run Crawl 按钮先 disabled 并注明"待来源逐个确认后开放"）
6. Pipeline 骨架：`SourceAdapter` Protocol、`manual_import` adapter（粘贴一个公开 URL → fetch → parse → 写入 raw_product → normalize → candidate，人工在 Review Queue 确认），dedup matcher 的基础实现（product_number + rapidfuzz，先不接图片哈希）
7. 不实现：真正针对 AmiAmi/Mandarake/Mercari/官方站的自动 discovery/scheduled crawl —— 待用户对每个来源单独确认 ToS 后再逐个打开 `crawl_policy = auto`

## Git

远程仓库：`https://github.com/m4a1gai/GoodsGallery`（用户已给出，说明可以在做完一部分工作后自行 commit 保存进度）。执行顺序：先 `git remote add origin ...`，实现过程中按里程碑（脚手架、数据模型+migration、mock 数据+API、前端页面、pipeline 骨架）分别提交，不用一次性一个大 commit。是否 `push` 到远程在第一次提交前单独跟用户确认一下（push 会让内容出现在 GitHub 上，属于对外可见的操作）。

## 验证方式

- 后端：`pytest` 覆盖 dedup matcher 的几个关键 case（同 product_number 合并、名称相似但类型不同不合并、confidence 分档正确）
- `docker compose up` 起 Postgres，跑 Alembic migration + seed script，`uvicorn` 起 API，手动 `curl` 关键端点
- 前端：`npm run dev` 起 Vite，用 mock 数据在浏览器里过一遍 CatalogHome → 筛选角色 → ItemDetail → 标记 Owned/Wishlist → MyCollection 统计更新 → ReviewQueue 走一遍 Accept/Reject/Merge
- manual_import adapter：用一个我们确认过允许访问的公开页面（或用户自己提供一个 URL）手动跑一次，验证 raw_product → candidate → review queue 全链路能跑通
