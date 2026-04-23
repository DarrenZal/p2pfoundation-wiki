# Research Synthesis Notes — Three Reports on Evolving the P2P Foundation Wiki

**Author:** Darren Zal, with Claude as drafting assistant.
**Date:** 2026-04-15 (living doc — update when new research lands).
**Status:** First pass. Synthesizes Report A (stewardship/governance) + Report B Part 1 (technical Q1–7) + Report B Part 2 (technical Q8–17). Feeds into Phase 2 planning and the interview guides.

## What we have in `docs/`

| File | What it is |
|---|---|
| `research-a-stewardship-governance-cultural-architecture.{md,pdf}` | Report A — ChatGPT Deep Research on stewardship, succession, AI editorial practice, cultural protocols, multilingualism, economic sustainability, platform choice. 12 questions, ~8K words. |
| `research-b-technical-services-q1-7.{md,pdf}` | Report B Part 1 — ChatGPT Deep Research on graph analysis (Leiden/k-core), GNN vs sheaf NN selection, Sheaf Laplacian at 40K nodes, learnable restriction maps, poset cohomology, discourse extraction, dynamic updates. |
| `research-b-technical-services-q8-17.{md,pdf}` | Report B Part 2 — incremental re-extraction, hybrid clustering, Wikidata federation, JSON-LD dumps, viz stack, UMAP, concept drift, sheaf-cohomology viz, citation verification, MediaWiki AI extensions. |
| `research-enhancing-wikis-with-ai-and-graphs.md` | Earlier Gemini Deep Research on GraphRAG + Leiden + LLM Wiki pattern. Less P2P-specific; some temporal-confabulation issues. Treat as warm-up, not authoritative. |
| `phase2-semantic-kg.md` | Our own Phase 2 plan draft (pre-research). Five tracks + hosting options. Needs revision now that the research has landed. |
| `interview-guides.md` | Michel (8Q) / Jeff (5Q) / contributor (5Q) guides. Pre-interview. |
| `koi-integration.md` | Phase 1 as-built documentation. |

## Top-level frame

The three reports together validate a three-layer frame that was only implicit in the original Phase 2 plan:

1. **Stewardship layer** (Report A) — governance, succession, cultural protocols, political stance, economic sustainability. *Determines whose wiki this is and how it stays healthy.*
2. **Editorial surface layer** (Report A §3 + Report B Q17) — provenance labels, AI-assisted writing with attribution, co-authorship UX. *Determines how humans and AI agents co-author trustably.*
3. **Technical substrate layer** (Report B Q1–Q16) — ingestion, entity extraction, graph analysis, viz. *Determines what the editorial surface can know and show.*

Technical work without the other two layers produces a research artifact, not a living commons. All prior tension between "build the KG" and "engage the community" dissolves when these layers are sequenced deliberately: stewardship first, then the editorial surface, then the technical substrate fills in.

## Cross-report load-bearing decisions

These are the decisions I believe are load-bearing — meaning delaying them constrains everything downstream, and getting them wrong is costly to reverse. Numbered for reference in the interviews.

### LBD-1. Formalize governance and succession within 12 months

**Source:** Report A §1, §6, Executive Summary decision #1. OERF dissolved 2025-12-13 as the strongest recent negative example; WikiEducator collapsed under founder-dependent governance. Debian / Apache / Wikipedia survived by formalizing early; Linux (34-year contingency plan) and WordPress (active 2025 governance crisis) show what happens when you don't.

**Why load-bearing:** Michel is 65+. Without legal stewardship entity and written succession process, a single health event or dispute fractures 18 years of intellectual canon.

**Concrete form:** 501(c)(3) foundation or cooperative (Appropedia path is the cheapest validated template), written bylaws, elected board, multi-stakeholder roles (editors, stewards, technical admin), arbitration process.

**Verification before committing:** confirm OERF dissolution via the Dec 2025 URL; re-check WordPress governance crisis status; ask Michel directly how he's thought about this.

### LBD-2. Build a provenance labeling layer ourselves

**Source:** Report A §3 (co-authorship with legible provenance) + Report B Q17 (no existing MediaWiki AI extension includes provenance labels for AI-generated content). Report B Part 2's Q17 is the single most important finding across all three reports: NeoWiki, Wanda, AI Assistant, AIEditingAssistant, VIKI — none of them.

**Why load-bearing:** Every other AI augmentation we might build (summarization, translation, category synthesis, Q&A) requires provenance to be trustable. If we build those first and retrofit provenance later, we pollute the wiki and lose community trust.

**Concrete form:** Wikidata-qualifier-style metadata + Hypothesis-style annotation layer + per-revision tag identifying AI involvement + mandatory source links in every AI-generated edit. Not platform-specific — we build this regardless of MediaWiki vs Wikibase vs NeoWiki choice.

**Reuses existing in-house work:** Claims Engine v2 already has attestation + provenance + confidence-score patterns. We're extending, not starting from scratch.

### LBD-3. Incremental re-extraction on the DBpedia-Live pattern

**Source:** Report B Part 2 Q8. Lehmann et al. 2012 validated the priority-queue + delta-extraction + cached-static-mappings pattern on enwiki at 108 pages/min. Our scale is 800× smaller, so single-server is fine.

**Why load-bearing:** Without this, every edit triggers full re-extraction and costs scale with corpus size, not with edit rate. At our 10–50 edits/day (Part 1 Q7), full recompute is currently cheap, but Phase 2 adds entity/claim/relationship extraction on top, and those scale badly.

**Concrete form:** on edit event, re-run NER/linking/claim extraction only on the changed page; update embeddings for changed chunks; leave static category/template mappings cached. ~1s/page with modern GPU embeddings.

### LBD-4. Political stance preservation as first-class requirement

**Source:** Report A §2. The P2PF wiki is explicitly activist. Off-the-shelf LLMs strip nuance and lean liberal-moderate; Wikipedia's AI lede summary experiment was paused after editor backlash. Wikipedia NPOV is the *wrong* model for this site.

**Why load-bearing:** Any AI-summarization, translation, or synthesis tool we deploy will silently shift the editorial line if we don't make stance preservation explicit. This breaks the wiki's reason for existing.

**Concrete form:** prompt prefixes that state stance ("from the perspective of commons-based peer production; preserve critique of capital enclosure"); human-review gate before any AI-generated text goes to the reader surface; editorial feedback loop that corrects ideological drift when detected; stance-preservation tests in any extraction evaluation.

**Verification:** ask Michel (interview Q5–Q6) what stance-drift looks like to him, and what examples he's already caught.

### LBD-5. Cultural and local-knowledge protocols before indexing sensitive content

**Source:** Report A §4. CARE Principles + Traditional Knowledge Labels (localcontexts.org) + Mukurtu CMS precedent. No wiki has implemented this natively yet — this is a place P2PF could lead.

**Why load-bearing:** If the wiki ingests Indigenous / community-organizing / unpublished-testimony content without consent protocols, we risk violating CARE + may be forced to retract later. Retraction is more expensive than prevention.

**Concrete form:** TK Label templates on sensitive pages, editorial "Consent to Share" review for new sensitive content, explicit ethics review process, collaboration with Local Contexts project.

### LBD-6. Preservation layer before expansion

**Source:** Report A §12 + LBD-1. 18-year archive must survive platform shifts. Internet Archive + Zenodo deposit + monthly XML dumps + optional Software Heritage for any custom code.

**Why load-bearing:** If the wiki goes down tomorrow, 18 years of argumentative canon is at risk. Phase 1 captured a local byte-current copy, but external preservation is the insurance.

**Concrete form:** monthly automated XML dump → Zenodo (DOI) + Internet Archive + optional IPFS pin. Automate via scheduled GitHub Action or cron.

## Connections to existing in-house work

### Sheaf theory bridge (Spore + Intelligence Commons + personal vault)

Our prior sheaf work — restriction maps as governed YAML protocol, H¹ as preserved tension, Bosca–Ghrist 2026 as target algorithm — maps cleanly onto:

- **Report B Q3 (Fiedler eigenvector at 40K nodes)**: directly computable, 10–60s with scipy. Gives us a named diagnostic: *which concept is the information-flow bottleneck of the P2PF corpus?*
- **Report B Q4 (learnable restriction maps)**: Bosca–Ghrist's local-discrepancy rule is federation-friendly (no central trainer); SGPC's Wasserstein-Entropic Lift requires shared gradients. For a federation of P2PF ↔ BKC ↔ Spore ↔ Wikidata, Bosca–Ghrist is the structural fit even if performance is lower.
- **Report B Q5 (poset cohomology on category hierarchies)**: novel application. `pysheaf` has no cohomology solver — we'd build custom. Treat as research track (publication with Spore/IC), not product.
- **Report B Q15 (sheaf viz)**: the Fiedler result from Q3 is actually a better starting primitive than the vague "H¹ contradictions" framing the researcher used. The Fiedler vector *names* the bottleneck node. That's the visualization seed.

### Claims Engine v2

Already has provenance, attestation, confidence-scoring infrastructure. LBD-2 (provenance labeling) is an *extension* of this, not a rebuild. Also connects to Report B Q16 (citation verification) — a "bad citation" flag can land in the same provenance store.

### Personal KOI search surfaces

Existing `unified_search` has entities / facts / sessions / docs / wiki surfaces with RRF fusion. Report B Q12–Q13 (visualization + UMAP) would plug into the wiki surface's chunk/embedding data directly.

### Bioregional Knowledge Commons (BKC)

BKC already uses the sheaf / restriction-map patterns. P2PF wiki as a new stalk → restriction map → BKC stalk is the concrete federation prototype. Michel's bioregional indexing ask becomes "populate the P2PF↔bioregion restriction map."

## Gaps the research didn't resolve

These are places where the research was honest about "not found" or the evidence was one blog post:

1. **No commons-specific ontology exists** (Report A §10). P2PF maintaining one (as Wikidata schema or SKOS vocabulary) would be a real movement contribution — but requires ontology design expertise we don't yet have on the team.
2. **No wiki has implemented CARE / TK Labels natively** (Report A §4). Mukurtu CMS is the closest — but it's not a wiki. Collaboration with Local Contexts is a real next-step action.
3. **No 40K-scale precedent for RDF dumps from a small wiki** (Report B Q11). We'd be pioneering, and adoption expectations should be low (WikiData5M-KG gets ~40 HF downloads/month).
4. **No concept-drift UI for wiki content exists** (Report B Q14). HistWords and gensim DTM give us the algorithms; the UI is custom. Could be a movement-valuable deliverable given P2PF's 18-year record — or a distraction.
5. **No sheaf-cohomology visualization tool exists** (Report B Q15). Only one Medium-blog citation in the entire report. If we build this, it's research not product.
6. **No published AI-political-stance-drift study specific to activist wikis** (Report A §2). General AI-bias literature + the Wikipedia editor backlash are all the researcher found. The gold-test-set work is ours to do.

## Verification probes still pending

Before citing any of these findings to Michel or Jeff, verify the claim directly:

- [ ] **OERF 2025 dissolution** — open https://oerfoundation.org/2025/12/13/terminating-oer-foundation-services/ and confirm. (Load-bearing for LBD-1 argument.)
- [ ] **WordPress 2025 governance crisis** — check TechCrunch article (Report A ref 3) plus a second source. (Supports LBD-1.)
- [ ] **Bastola & Choi 2025 Silhouette 0.927 number** — open arXiv 2509.00990 and verify the benchmark details before trusting the hybrid-clustering recommendation.
- [ ] **SIDE 70% human-preference rate** — Nature Machine Intelligence 2023 paper. Before committing to SIDE as our citation-verification anchor, read the paper.
- [ ] **NeoWiki activity claim ("multiple commits in April 2026")** — check the actual repo. If the researcher was confabulating temporal detail, we lose trust in the Q17 ranking.

## What to build first (concrete next 30 days)

Ordered by sequencing logic (earlier steps unblock later ones):

1. **Run the 3 interviews** (Michel, Jeff, one active contributor). These are the single highest-value input we can get. Reports provide a priori framing; interviews provide ground truth. Everything downstream shifts based on what they say.
2. **Verify the 5 pending citations** above. ~1 hour.
3. **Half-day Leiden + k-core spike** on our existing `mediawiki_page_links` data. k=2 or 3 prune, then Leiden on the backbone. Produces named communities + "god nodes" list. Visible, shareable, concrete deliverable.
4. **Paper-prototype the provenance label UX.** What does a reader see when they hover over an AI-assisted claim? What does an editor see when reviewing an AI suggestion? Paper beats code for this phase.
5. **Schedule a preservation-first action** — monthly XML dump → Zenodo deposit. One-time setup, ongoing automation.

## What explicitly NOT to build now

- **Poset cohomology on category hierarchies** (Part 1 Q5) — research track only, unless paired with a publication goal.
- **Sheaf-cohomology visualization** (Part 2 Q15) — evidence is one Medium blog. Do not build without stronger grounding.
- **HuggingFace Datasets release** (Part 2 Q11) — no consumers. Zenodo DOI + IPFS pin is sufficient for preservation.
- **A parallel Semantic MediaWiki mirror** (phase2-semantic-kg.md Option B) — divergence nightmare, already documented as not-recommended.
- **Full custom Wikibase instance** (phase2-semantic-kg.md Option D) — premature until we've done Wikidata entity alignment via OpenRefine first and know what we'd be federating.

## Open questions for the interviews

Add to `interview-guides.md` based on what the research surfaced:

**For Michel, add probes on:**
- The OERF-2025 dissolution as a concrete succession-failure example — what does good succession look like *to him*?
- Has he ever caught an AI-generated summary misrepresenting the P2PF political frame? If so, where, when?
- What ontology / vocabulary does he already use in his head when categorizing pages? (We may extract the commons ontology from him.)

**For Jeff, add probes on:**
- Preservation readiness: monthly XML dumps → Internet Archive + Zenodo — what's the operational ask from his side?
- Wikidata federation: appetite for QuickStatements + OpenRefine work against a reconciled entity set?
- Bot flags: willing to apply for one for our use, or should we stay with manual QuickStatements?

**For contributors, add probes on:**
- Has an AI-assisted edit on any wiki ever felt like it flattened a political frame they cared about? Details.
- What would make them want to review AI-suggested edits vs dread it?

## Document maintenance

- Update this synthesis when new research lands.
- When an LBD is acted on (e.g. legal entity formed), move it to a "Done" section with dates.
- Link back from `phase2-semantic-kg.md` — this doc is now an input to the revised Phase 2 plan.
- Interviews should produce a companion `interview-findings.md` that modifies or overrides these LBDs where community voice differs from research-derived recommendations.
