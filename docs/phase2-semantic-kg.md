# Phase 2 Planning — Semantic Knowledge Graph for P2P Foundation Wiki

**Status:** DRAFT — planning only, not a commitment to any specific approach yet.
**Depends on:** Phase 1 (see `koi-integration.md`).
**Prerequisite decision before execution:** hosting/serving architecture (see §7 below).

## Context

Phase 1 gave us a **link graph**: 40K pages as nodes, 43K wikilinks as undifferentiated `related_to` edges. That's enough for FTS + vector search and basic graph traversal. It is *not* a semantic knowledge graph.

Phase 2 transforms this into a **typed semantic graph** where:
- People, organizations, concepts, books, projects, places are first-class entities with stable IDs
- Relationships are typed (`authored_by`, `founded`, `part_of`, `critiques`, `located_in`, etc.)
- Claims, questions, and evidence can be extracted and linked to their entities of origin
- The corpus becomes queryable in semantically meaningful ways ("what has Michel Bauwens written about the commons?" answered by the graph, not just by keyword co-occurrence)

Michel flagged two specific asks in the Jan-Feb email thread:
1. **Bioregional indexing** — index pages by bioregion rather than nation-state (see Mark Whitaker's Commodity Ecology Project)
2. **Section-based synthetic layer per Category** — his `Category:Housing` experiment showed what AI-generated per-category summaries could look like

Phase 2 has room for both.

## What's NOT this plan

- Ingesting non-NS-0 namespaces (Categories, Templates, Files) — **that's Phase 1.5**. Needs to happen before or alongside Phase 2 to have full context.
- Operational concerns handled in Phase 1 (sensor, filesystem mirror, live updates).
- Deciding Jeff's hosting situation — see `koi-integration.md` § Contact; ongoing thread on Telegram.

## Corpus-first principle

**Before designing the schema, inspect the corpus.** The P2P Foundation wiki has 18 years of content across many loose conventions. Guessing at entity types produces a schema that doesn't fit. Plan:

1. Sample ~50 pages across apparent categories (articles, book notes, person bios, concept definitions, project profiles, category pages).
2. Catalog the 10-20 most common "page shapes" — what templates, fields, section patterns recur.
3. Identify the 10-20 most important entity types actually present (not aspirationally).
4. Look at the top-linked pages — what are they? People? Concepts? Projects?
5. Look at the 512 APFS-case-collision pairs — they're often `X` article + `x` redirect, giving hints about alias patterns.

Output: a **corpus field guide** (markdown doc, ~2 hrs of work) that Phase 2 schema decisions ground in.

## Proposed tracks (5 parallel, sortable by priority)

### Track 1 — Entity extraction (foundation)

Extract mentions from page title + content → register in `entity_registry` → resolve against existing entities from other sources (many are already there from meeting notes, bookshelf, etc.).

- **Techniques**: LLM pass over plain-text chunks (Claude or Gemini), NER + type-classify, de-duplicate via existing 5-tier resolver (`personal_ingest_api.py:resolve_entity`).
- **Candidate entity types** (refine from corpus inspection):
  - `Person` — Michel Bauwens, Yochai Benkler, Silvia Federici
  - `Organization` — P2P Foundation, Creative Commons, Linux Foundation
  - `Concept` — Commons, Peer Production, Commons-Based Peer Production
  - `Project` — Wikipedia, Linux, Bitcoin
  - `Publication` — books, papers
  - `Place` — cities, regions, bioregions
  - `Event` — conferences, summits
  - `Technology` — specific platforms, protocols
- **Expected scale**: 5K-20K entities across the corpus (guess — validated by corpus inspection).
- **Cost estimate**: ~33K chunks × context size → maybe $50-200 of Claude/Gemini API, or local with Qwen/Gemma on TELUS catalog.

### Track 2 — Typed relationship extraction

- **From structure**: page titled "Foo" with `[[Michel Bauwens]]` in `Author =` field ⇒ `foo --authored_by--> michel_bauwens`. High precision, low recall.
- **From prose**: LLM extracts `(subject, predicate, object)` triples from sentences. Higher recall, lower precision — needs confidence gating.
- **Predicate vocabulary** (starter — refine from corpus):
  - `authored_by`, `founded`, `founded_by`, `part_of`, `subtype_of`, `located_in`
  - `critiques`, `extends`, `builds_on`, `collaborates_with`
  - `mentioned_in` (the default wikilink)
- Lands in `entity_relationships` with typed predicates, confidence scores, provenance (source page + chunk).

### Track 3 — Template / infobox field promotion

- Parser (`api/mediawiki_parser.py`) already detects `{{template}}` blocks and field patterns (`URL =`, `Author =`, year patterns).
- Map these to structured entity properties (e.g. `Publication { title, author, publisher, year, url }`).
- Cheaper than LLM extraction; high confidence.
- Should run before Track 1/2 — template fields give the LLM context anchors.

### Track 4 — Discourse extraction (Claims Engine integration)

The big one. P2P writing is dense with claims, questions, and arguments.

- **Claims**: assertion-style statements in prose → `koi_claims` table (exists in koi-processor). Linked to: claimant entity (author), supporting evidence, pages that cite/contradict.
- **Questions**: explicit research questions (often marked `? = ` in this wiki) → `koi_questions` table (needs design).
- **Evidence**: citations, URLs, quoted passages → link to claims they support.
- **Arguments**: pro/con relationships between claims (`supports`, `contradicts`, `extends`).
- Existing infra: Claims Engine v2 is deployed, has provenance + attestation. Perfect landing zone.

### Track 5 — Domain-specific layers

- **Bioregional tagging** (Michel): index each page by bioregion using the BKC `Bioregion` schema. Cross-references: `p2pf_page --concerns--> bioregion`. Requires bioregion resolution of place mentions.
- **Category synthesis** (Michel): AI-generated per-category overview from pages in that category. Needs Phase 1.5 (Category namespace ingested) first. Storage: `koi_knowledge_synthesis` table (new, proposed).
- **Cross-wiki entity alignment**: many entities on P2PF wiki also exist on Wikidata (Michel Bauwens, Creative Commons, etc.). Wikidata ID resolution opens federation.

## Hosting & serving the semantic graph — the strategic decision

This is the biggest architecture question. Each option has different implications for authority, maintenance, community participation, and long-term sustainability.

### Option A — KG lives in personal_koi, published as a read-only service
- Schema in PostgreSQL + Fuseki (already part of koi stack)
- Public interfaces: SPARQL endpoint + JSON-LD bulk dumps + a simple explorer UI
- **Pros**: Full schema control, fast iteration, zero new infra
- **Cons**: Not wiki-native; discovery requires knowing KOI exists; can't be collaboratively curated by the P2PF community
- **Best when**: Phase 2 is our research / our analytical lens, not a P2PF community product

### Option B — Semantic MediaWiki (SMW) on a mirror wiki we host
- Run a separate MediaWiki + SMW instance that imports P2PF content + adds property assertions
- **Pros**: Wiki-native browsing; property markup editable in-line; mature browse/query UIs
- **Cons**: Running two wikis is a divergence nightmare (our SMW wiki vs Jeff's canonical wiki); 41K pages need retrofitted property markup; SMW is 2005-era tech with scale concerns; community won't know which is "real"
- **Best when**: we're willing to take over authoritative hosting (not the current intent)

### Option C — SMW on wiki.p2pfoundation.net itself (needs Jeff)
- Jeff enables SMW; we contribute property markup via pull requests / dump imports
- **Pros**: No divergence; community curates; Jeff gets richer search / browse for free
- **Cons**: Needs Jeff's agreement + admin lift; SMW install on an 18-year-old wiki is non-trivial; property coverage grows slowly from community effort
- **Best when**: we and Jeff are aligned on long-term semantic layer

### Option D — Wikibase (separate instance)
- Wikibase (the Wikidata engine) is the modern successor to SMW. Run a Wikibase instance that indexes P2PF pages as items, adds statements (`P` properties).
- **Pros**: Modern, well-maintained, federates with Wikidata, strong multilingual support, better UI than SMW
- **Cons**: Another service to run; Wikibase Cloud exists as hosted option (free for community instances); learning curve for editors
- **Best when**: we envision an ongoing shared resource across P2P/commons communities

### Option E — JSON-LD / SPARQL overlay published alongside the wiki
- We extract + maintain the KG in our own stack; publish as JSON-LD files + SPARQL endpoint as an overlay service. No edits to Jeff's wiki.
- **Pros**: Zero impact on Jeff; machine-readable for any downstream consumer; cheap; simple
- **Cons**: Not browseable without a viewer UI; low discoverability for humans
- **Best when**: primary audience is AI/data tooling, not humans browsing

### Recommendation — hybrid of A + E, with D as a potential 12-month target

Short term: **build Phase 2 KG in personal_koi (Option A)**, publish a **read-only SPARQL + JSON-LD overlay (Option E)** for external consumers. This is the fastest path to value, requires no coordination with Jeff, and produces artifacts that can later feed SMW/Wikibase if/when that path opens.

Long term: once the schema and extraction pipelines are stable, **consider Wikibase Cloud (Option D)** as a community-facing shared resource. Wikibase Cloud hosts instances for free and federates with Wikidata — attractive for the P2P / commons research community beyond us.

**Decisively NOT recommended**: running a parallel SMW wiki (Option B). Divergence will burn us.

## Sequencing & dependencies

```
Phase 1.5: ingest Category / Template / File namespaces
     │
     ├──> Corpus field guide (~2 hrs inspection)
     │         │
     │         ├──> Track 3 (template field promotion) — cheap, high-precision, feeds other tracks
     │         ├──> Track 1 (entity extraction) — needs template context
     │         ├──> Track 2 (typed relations) — needs entities
     │         ├──> Track 4 (discourse) — needs entities; can run in parallel with Track 2
     │         └──> Track 5a (bioregional) — needs place entities + BKC bioregion schema
     │
     └──> Hosting/serving decision (Option A vs D vs hybrid)
                    │
                    ├──> SPARQL endpoint setup (Fuseki already in stack)
                    ├──> JSON-LD export pipeline
                    └──> Explorer UI (optional, small)
```

Minimum viable Phase 2: Phase 1.5 + Tracks 1+2+3 + SPARQL/JSON-LD publishing. Estimated effort: 2-4 weeks of focused work (not full-time).

## Open questions to resolve before executing

1. **Scope of entity types** — wide & shallow (more types, each sparsely populated) or narrow & deep (5-8 core types, each richly modeled)? Corpus inspection answers.
2. **LLM extraction budget** — Claude API (paid, high quality) vs Gemini (cheap, maybe lower recall) vs local Qwen/Gemma via TELUS catalog (free, quality TBD). Suggest: Claude for initial gold-standard on ~500 pages, then local for bulk with gold set as eval.
3. **Attribution / provenance model** — every extracted fact needs `(source_page, source_chunk, extraction_method, confidence, timestamp)`. Claims Engine v2 already has this pattern — reuse.
4. **Community participation** — do we want P2PF community to correct/extend our extractions? (Yes changes the architecture: need write-path + audit trail). If we're going toward Option D, community participation is the whole point.
5. **Integration with Wikidata** — for entities that exist in Wikidata (Michel Bauwens, Creative Commons, etc.), do we import Wikidata IDs? Yes probably — federation is valuable.
6. **Michel + Jeff alignment** — do we coordinate Phase 2 with them (invite Michel to review schema; ask Jeff for SMW install) or ship first and show them? Same ship-first vs align-first tension as Phase 1.
7. **Bioregional schema** — use BKC's `Bioregion` entity type as-is, or refine for global coverage (P2PF is international; BKC was Salish Sea + adjacent).
8. **Public URL** — where do we host the overlay? `kg.p2pfoundation.net` (requires Jeff) vs own domain (e.g. `p2pfwiki.gaiaai.xyz` under existing infra) vs subpath on an existing site.

## Success criteria (for Phase 2 v1)

- 5K+ entities extracted, resolved, typed across Person/Organization/Concept/Project
- 10K+ typed relationships (beyond generic `related_to`)
- Every entity backed to at least one source page with citation
- SPARQL endpoint returns useful queries ("list all Concepts attributed to Michel Bauwens", "list all Organizations in bioregion X")
- JSON-LD dump is valid schema.org / PROV-O compliant
- At least one non-trivial discourse claim chain extracted (e.g. "Commons-Based Peer Production" has N supporting + M contradicting claims, each with evidence)
- Michel + Jeff can query it and find value

## Estimated cost

- **Engineering time**: 2-4 focused weeks for v1
- **LLM API budget**: $100-500 depending on mix of Claude vs local
- **Infra**: negligible (Fuseki + PG already running); Wikibase Cloud is free if we go Option D

## Next concrete step

When ready to start:
1. Run the corpus inspection (2 hrs) → `docs/phase2-corpus-field-guide.md`
2. Reconvene on this doc's open questions
3. Write `/new-plan` for Phase 2 v1 (Tracks 1+2+3 + publish)
4. Decide Phase 1.5 (namespace expansion) timing

Not urgent. Phase 1 is sufficient for current usage (search + link-graph analytics). Phase 2 unlocks the "why did you build this?" value — likely worth doing within a few months, probably not this week.
