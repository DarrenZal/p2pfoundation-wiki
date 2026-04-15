# P2P Foundation Wiki → Personal KOI Integration

**Date:** 2026-04-14
**Branch:** `live-sync` (sensor writes go here; `main` stays as Jeff's upstream)
**Status:** Phase 1 complete — live-synced via polling sensor + cross-corpus search.

## What this is

This clone of Jeff Emmett's [p2pfoundation-wiki archive](https://github.com/Jeff-Emmett/p2pfoundation-wiki) is the **filesystem half** of a live-synced copy of `wiki.p2pfoundation.net`. The **database half** lives in the local `personal_koi` PostgreSQL (`localhost:5432`) running under `koi-processor`.

- **Semantic / FTS queries:** `mcp__personal-koi__unified_search` (wiki surface)
- **Graph / aggregate queries:** `mcp__personal-koi__koi_query` (SQL against `mediawiki_*` tables)
- **Filesystem mirror:** `./wiki/*.mediawiki` — sensor rewrites on live-wiki edits

## Why

- Feed the P2P Foundation corpus into personal knowledge-graph workflows (cross-surface RRF search with entities/facts/sessions).
- Have a local byte-current copy independent of `wiki.p2pfoundation.net` availability.
- Seed for Phase 2 structured KG extraction (claims, bioregional indexing, section synthesis).
- Sent with Jeff's knowledge via Telegram on 2026-04-14 (P2PF wiki findings message); ship-first, coordinate with him on dump format + hosting later.

## What lives where

| | Where | Detail |
|---|---|---|
| Jeff's original `.mediawiki` files | `wiki/` (on disk, branch `live-sync`) | 41,049 files; APFS case-collisions exist (see "Known issues") |
| Jeff's XML dumps | `xmldump/*.xml` (LFS) | 31 files, 23,019 NS-0 pages total across all dumps. Newest revision from **2014** — not used for bootstrap. |
| KOI pages | `mediawiki_page_state` in `personal_koi` | **40,239** rows, NS 0 only |
| KOI chunks + vectors | `koi_memory_chunks WHERE document_rid LIKE 'mediawiki:%'` | **96,775** chunks @ 1024-dim Qwen embeddings |
| KOI full documents | `koi_memories WHERE source_sensor = 'mediawiki-sensor'` | 33,346 rows (entity-bearing or semantically meaningful pages) |
| Wikilink graph | `mediawiki_page_links` | **42,997** edges, **39,561 resolved** to `target_page_id` (92%) |
| Wiki registration | `mediawiki_wikis WHERE id=1` | `sync_mode=poll`, `status=active`, 10-min poll interval |
| Bootstrap artifacts | `.bootstrap-cache/` (gitignored) | ~2.4 GB: live-export JSON, parsed pages, chunk JSONL, embedding JSONL |

## How the bootstrap was done (2026-04-14)

Original plan assumed a full XML dump; Jeff's dumps turned out to be from 2014 and only cover 23K pages (vs 41K on live wiki). We walked the live API instead.

1. **Clone repo** — `git clone` + `git lfs pull` + `git checkout -b live-sync`.
2. **Fix migration 063** — removed a trailing comma that was blocking `mediawiki_page_links` creation (koi-processor commit `3a334ab6`).
3. **Live-API walk** — `scripts/mediawiki_live_export.py` in koi-processor walks `allpages` → 40,239 pages, 172 MB JSON, **~8 min** (1 req/s rate limit).
4. **Parse** → 5a `mediawiki_parse_dump.py --format json` → per-page JSON + manifest + edges JSONL (40K pages, 43K edges).
5. **Bulk import** → 5b `mediawiki_bulk_import.py` → `mediawiki_page_state` + `mediawiki_page_links`.
6. **Chunk + emit reembed JSONL** → `mediawiki_chunks_to_db_and_jsonl.py` (new, koi-processor) → 96,775 chunks to DB (NULL embeddings) + `chunks_for_h200.jsonl` (144 MB).
7. **H200 reembed** — TELUS pod `model-deployment-0b50s.paas.ai.telus.com`, `reembed_on_h200.py` at batch=16 (shared GPU constraint), Qwen3-Embedding-0.6B, ~25 min for 96K chunks.
8. **Import embeddings** → `import_mediawiki_embeddings.py` (new, local-only) → `koi_memory_chunks.embedding` populated.
9. **Resolve wikilinks** — direct SQL UPDATE matching `normalized_target_title` → `page_state.normalized_title`, following one-level redirects. 92% resolution (see "Known issues" for the 8%).
10. **Upgrade wiki row to poll mode** — `sync_mode='poll'`, `last_scan_at=NOW()-2h`, config JSONB sets `local_path + write_filesystem + git_branch=live-sync`.
11. **Sensor starts on KOI restart** — `MEDIAWIKI_SENSOR_ENABLED=true` in `config/personal.env`.

## Commits (all cross-referenced)

**koi-processor** — branch `p2pfoundation-wiki-sensor` (github.com/gaiaaiagent/koi-processor):

| SHA | Title |
|---|---|
| `3a334ab6` | fix(migrations): remove trailing comma in mediawiki_page_links DDL |
| `c1042c29` | feat(mediawiki): live-sync sensor + filesystem mirror + wiki search surface |
| `345419e4` | feat(query): whitelist mediawiki_* tables for koi_query dynamic SQL |

**personal-koi-mcp** — branch `main` (github.com/DarrenZal/personal-koi-mcp):

| SHA | Title |
|---|---|
| `9c6ab4c` | feat(koi_query): document mediawiki_* tables now available for SQL queries |

**darren/CLAUDE.md** — one-liner added under "What's Done" so every Claude session sees it.

## How the sensor works

- Background asyncio task started by `api/profiles/personal.py` when `MEDIAWIKI_SENSOR_ENABLED=true`.
- Polls registered wikis (`mediawiki_wikis WHERE status='active' AND sync_mode='poll'`) every `MEDIAWIKI_POLL_INTERVAL` seconds (default 600).
- Queries `action=query&list=recentchanges&rctype=edit|new|log&rcprop=title|ids|timestamp|loginfo` since `last_scan_at - 1s` (1s overlap guards same-second boundary misses).
- For **edit/new** events: fetches page content in batches of 50, runs the full KOI pipeline (parse → upsert `page_state` → store links → process entity-bearing → rechunk/embed → emit event). Also rewrites `wiki/<title>.mediawiki` on the clone.
- For **delete log** events: deletes the filesystem file + sets `mediawiki_page_state.status='deleted'`. Chunks retained (tombstone pattern).
- For **move log** events: renames the filesystem file, updates `mediawiki_page_state.title` (page_id + source_rid are stable across renames). Redirect stub at old title appears as a `new` event on next poll.
- Branch safety: sensor skips all filesystem writes unless the clone is on the configured branch (`config.git_branch`, default `live-sync`). Keeps `main` clean for upstream pulls.

## Querying the data

### Via MCP (preferred in Claude sessions)

```
# Semantic search
mcp__personal-koi__unified_search(query="commons transition", limit=10)

# Aggregate / graph query
mcp__personal-koi__koi_query(
  sql="SELECT ps.title, COUNT(DISTINCT pl.source_page_id) AS inbound
       FROM mediawiki_page_links pl
       JOIN mediawiki_page_state ps ON ps.id = pl.target_page_id
       WHERE pl.resolution_status IN ($1, $2)
       GROUP BY ps.title ORDER BY inbound DESC LIMIT 10",
  params=["resolved", "redirect_resolved"]
)
```

### Via direct psql

```bash
psql "postgresql://darrenzal:@localhost:5432/personal_koi"

# Top-linked pages (resolved graph)
SELECT ps.title, COUNT(DISTINCT pl.source_page_id) AS inbound
FROM mediawiki_page_links pl
JOIN mediawiki_page_state ps ON ps.id = pl.target_page_id
WHERE pl.resolution_status IN ('resolved','redirect_resolved')
GROUP BY ps.title ORDER BY inbound DESC LIMIT 10;

# 1-hop neighbors of "Commons"
SELECT ps_t.title
FROM mediawiki_page_links pl
JOIN mediawiki_page_state ps_s ON ps_s.id = pl.source_page_id
JOIN mediawiki_page_state ps_t ON ps_t.id = pl.target_page_id
WHERE ps_s.title = 'Commons' AND pl.resolution_status LIKE '%resolved%'
LIMIT 20;

# Pages linking to BOTH "Peer Production" AND "Michel Bauwens"
SELECT ps.title FROM mediawiki_page_state ps
WHERE ps.id IN (
  SELECT pl.source_page_id FROM mediawiki_page_links pl
  JOIN mediawiki_page_state t ON t.id = pl.target_page_id
  WHERE t.title = 'Peer Production' AND pl.resolution_status LIKE '%resolved%'
) AND ps.id IN (
  SELECT pl.source_page_id FROM mediawiki_page_links pl
  JOIN mediawiki_page_state t ON t.id = pl.target_page_id
  WHERE t.title = 'Michel Bauwens' AND pl.resolution_status LIKE '%resolved%'
);

# FTS on chunks
SELECT content->>'title', ts_rank(tsv, q) AS r
FROM koi_memory_chunks, plainto_tsquery('english', 'commons based peer production') q
WHERE document_rid LIKE 'mediawiki:%' AND tsv @@ q
ORDER BY r DESC LIMIT 5;
```

## Operational runbook

```bash
# Health / status
psql personal_koi -c "SELECT wiki_name, status, sync_mode, last_scan_at,
  last_success_at, last_error_at, page_count FROM mediawiki_wikis;"

# Most recent sensor events
grep 'MediaWiki sync' ~/.config/personal-koi/koi-server.log | tail -20

# Pause sync (no restart needed)
psql personal_koi -c "UPDATE mediawiki_wikis SET status='paused'
  WHERE base_url='https://wiki.p2pfoundation.net';"

# Resume
psql personal_koi -c "UPDATE mediawiki_wikis SET status='active'
  WHERE base_url='https://wiki.p2pfoundation.net';"

# Force full rescan (pulls last 24 h)
psql personal_koi -c "UPDATE mediawiki_wikis SET last_scan_at=NULL
  WHERE base_url='https://wiki.p2pfoundation.net';"

# Pull Jeff's non-wiki upstream updates (blog/, infra/, README) — leaves our wiki/ alone
cd /Users/darrenzal/projects/p2pfoundation-wiki
git fetch origin
git checkout main && git pull
git checkout live-sync
git checkout main -- blog/ infra/ README.md CONTRIBUTING.md LICENSE

# Reset the filesystem clone to Jeff's snapshot (if drift needs cleaning)
git checkout live-sync -- wiki/      # drop sensor writes, keep Jeff's versions
```

## Known issues / limitations

### APFS case-collisions (~512 files)
Jeff's archive has pairs of pages whose titles differ only in case (e.g. `@ Is For Activism` vs `@ is for Activism`). On case-insensitive APFS they collide on the same filename. `git clone` writes one then overwrites with the other — on this checkout, the **redirect stub** won the race for many files. `git status` shows them as modified vs the committed full version.

**Impact:** filesystem mirror is not byte-fidelitous with Jeff's repo. KOI DB has both variants correctly (keyed by `page_id`), so search is unaffected. Fix would require a case-sensitive filesystem (HFS+ with case-sensitive option or APFS case-sensitive volume).

### 8% unresolved wikilinks (expected)
3,436 of 42,997 links didn't resolve. Breakdown:
- **2,715 (79%) red links** — targets that don't exist on the wiki (standard MediaWiki pattern).
- **666 (19%) `Category:` / `File:` / `Template:` links** — Phase 1 is NS 0 only; these target NS 14/6/10. Phase 2 should expand.
- **~55 tail** — anchor-only, Semantic MediaWiki properties (`has type::string`), malformed titles.

92% is the structural ceiling at current scope.

### Phase 1 is NS-0 only
We sync main-namespace articles but not `Category:`, `Template:`, `File:`, `Talk:`, `User:` pages. Matches Jeff's archive scope, but the live wiki has ~18 namespaces. Templates especially matter for rendering. Phase 2 expansion is easy (MediaWiki API exposes all namespaces publicly; just extend the sensor's `rcnamespace` parameter).

### `source_sensor='mediawiki-sensor'` is NOT doc-scanner
Our chunks go into `koi_memory_chunks` with `document_rid LIKE 'mediawiki:%'`. The `docs` surface of `unified_search` uses a metadata `repo` filter that skips our rows — we added a dedicated `wiki` surface instead. See `api/routers/knowledge_router.py` in koi-processor commit `c1042c29`.

### Bootstrap cache kept for now
`.bootstrap-cache/` has the intermediate artifacts (live-export JSON, parsed pages, chunk JSONL, 2.1 GB embeddings JSONL). Safe to delete — re-bootstrapping is cheap if ever needed (mostly re-running the live API walk).

## Phase 2 backlog (deferred — needs its own plan)

- **Namespace expansion** — Category:, Template:, File: pages. Closes the 666-link gap + enables proper wiki rendering.
- **Structured claim + evidence extraction** using the existing Claims Engine in koi-processor.
- **Entity extraction beyond wikilinks** — map P2P template patterns to entity types in `entity_schema.py`.
- **Bioregional indexing layer** (Michel's ask) — tag/index pages by bioregion instead of nation-state.
- **Section-based synthetic layer per Category** (Michel's ask, e.g. `Category:Housing`).
- **Coordinate with Jeff on dump hosting** — see Telegram on 2026-04-14. Options mentioned: server-side `dumpBackup.php` full dump, HuggingFace Datasets, IPFS, Internet Archive.
- **Case-sensitive mirror** — optional separate APFS case-sensitive volume to get byte-fidelity with Jeff's repo.

## Contact

- **Wiki owner** (hosting): Jeff Emmett (Telegram: "Jeff Emmett, Mycopunk 🍄 ✌️")
- **P2P Foundation founder**: Michel Bauwens (email: michelsub2004@gmail.com)
- **Integration maintainer**: Darren Zal (<zaldarren@gmail.com>)
