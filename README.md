# GoodsGallery

Poppin'Party（戸山香澄 × 市ヶ谷有咲）谷子数据库 + 个人收藏管理器。

架构和第一阶段范围见 `docs/plan.md`（从会话计划文件复制）。核心理念：

```
Internet → Discovery → Raw → Normalize → Dedup → Confidence → Review Queue → Catalog → Collection
```

- **Global Catalog**：客观存在的商品图鉴，与个人是否拥有无关。
- **Personal Collection**：仅存储 owned/wishlist/购买记录，与 Catalog 物理分离。
- **Pipeline**：`backend/pipeline/` 下的 Source Adapter / normalize / dedup，第一阶段只启用 `manual_import`（人工粘贴 URL），没有任何来源被自动调度爬取。

## 本地开发

### 依赖

- Python 3.13+, Node 22+, Docker（本机通过 colima 提供 daemon）

### 启动 Postgres

```bash
docker compose up -d db
```

### 后端

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed        # 写入 mock 数据（角色、商品、来源、review candidate）
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000/api/health

手动导入一个商品 URL 到 pipeline（会检查 robots.txt，写入 raw_product → candidate，人工在 Review Queue 确认）：

```bash
python -m scripts.import_url manual_import "https://example.com/some-product-page"
```

跑 pipeline 单元测试（去重 matcher）：

```bash
pytest
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173 — Catalog / My Collection / Review Queue / Sources 四个页面。

## 数据来源合规性

`source` 表里的 `crawl_policy` 字段控制一个来源能否被自动爬取：

- `manual_import_only`（默认）：只能通过粘贴 URL 手动触发。
- `search_discovery_only`：只用搜索引擎结果做 discovery，不直接爬站内页面。
- `auto`：允许 pipeline 自动调度抓取——**目前没有任何来源被设为这个值**，需要先人工确认该网站的 robots.txt 和 ToS。
- `disabled`：不使用。

新增/升级一个来源前，请先读一遍它的 robots.txt 和服务条款。
