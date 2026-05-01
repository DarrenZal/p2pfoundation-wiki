# P2P Foundation Wiki

Local fork of Jeff Emmett's p2pfoundation-wiki archive + research/planning docs for a semantic knowledge graph layer.

## Current Status

**Date:** 2026-05-01
**Status:** Post-2026-04-30 Jeff call. Five-thread collab map accepted (matchmaking/intent grammar; JANUS addressing; P2P Wiki intelligence layer with bioregional lens; sheaf side-research; commitment weaving). Lead-with-tools / dogfood posture explicitly chosen over paid integration. Waiting on Jeff to ship holonic task board / collaborative spec system in next couple days — that becomes the operational substrate. Board-chair call did NOT surface in this call; "wait on Michel" is the new posture for the $40K. April 28 scheduled routine `trig_01Kd9XLJ7EdX6c6VpjgE5o5Z` fired but board outcome unknown.

## Remotes + Branches

- **origin** → `Jeff-Emmett/p2pfoundation-wiki` (upstream)
- **fork** → `DarrenZal/p2pfoundation-wiki` (personal)
- `research-docs-2026-04-23` (fork, HEAD `ae98bd60`) — 8 markdown research docs in `docs/`. PDFs dropped as redundant.
- `redirect-resolver-fs-2026-04-15` (fork, `b1ca468e`) — redirect-resolution work.
- `live-sync` (fork, `bf1df389`) — upstream issues report.

## Known Structural Issue

Working tree on this case-insensitive APFS volume shows ~533 phantom "modifications" in `wiki/`. Root cause: the `b1ca468e` tree has **520 case-variant duplicate file pairs** (e.g. `ALLMENDA.mediawiki` + `Allmenda.mediawiki`). Git sees them as distinct paths; the filesystem can only materialize one per pair. Not real uncommitted work — `git status` noise is inevitable on this FS. Fix is a separate workstream (dedupe to canonical case, or move repo to case-sensitive APFS volume).

## Live-Wiki Sensor

Per `~/.claude/plans/transient-strolling-mochi.md`, a MediaWiki sensor was built to auto-write live-wiki edits to the local filesystem mirror (via `_write_local_mirror()` in `api/mediawiki_sensor.py` in `RegenAI/koi-processor`). Deliberately does NOT auto-commit. Accumulates sensor writes as uncommitted state in the working tree. These are wiki-editors' work, not yours — don't publish to fork without coordinating with Jeff.

## What's Done (recent)

- 2026-04-30 Jeff Emmett follow-up call — fully processed (meeting note + transcript + 11 tasks + 17 new entity stubs + 42 entity `mentionedIn` propagations) at `~/Documents/Notes/Meetings/People/2026-04-30 Jeff Emmett Meeting.md`. Post-call DM artifacts: Darren sent Jeff the team-commitment-stewardship memo link, Salish Sea Dreaming v5 web app, and Andrew Millison's YouTube channel — closes the Millison-link task (Darren self-served + shared back rather than waiting on Jeff).
- Pre-call artifacts ready (not yet shared async): JANUS↔Spore sheaf bridge note (`~/projects/spore/docs/research/connections/janus-addressing-sheaf-bridge.md`); rTime↔Poietic Match/Spore intent bridge; SHEAF-CAPABILITIES comparative-read plan; bioregional-lens pilot proposal; gardening pilot proposal; Jeff×Darren collaboration braid; JANUS visualizer plan.
- Process-Note Operational Log expanded (`~/Documents/Notes/Meta/Entity Resolution Issues.md`): now three sections (Entries / Pattern Flags / Tooling Issues). 10 new bad-merge entries logged for the 2026-04-30 run; 3 cross-cutting Pattern Flags (recurring Guard E miss on Project distinctive-suffix drops); 2 Tooling Issues.
- MCP bug fixed: `personal-koi-mcp@46520bc` patches `markUnavailable()` so a single op-level timeout no longer poisons the availability cache for 30s. Pushed to `feat/agentic-web-crawl-phase4`. Picked up on next Claude Code session start.
- Vault rename: `People/Andrew Millicent.md` → `People/Andrew Millison.md` after backend canonical correction (transcription error in audio).
- 2026-04-23 prior-call legacy: research docs at `fork/research-docs-2026-04-23` (`ae98bd60`); Telegram recap msg 28106; APFS case-collision artifact diagnosed (520 case-variant duplicate pairs in `wiki/` tree).

## What's Left

**Now (waiting on Jeff):**
1. Wait on Jeff's holonic task board / collaborative specs+roadmap system (next couple days). That artifact becomes the operational substrate for the dogfood collaboration; matchmaking + commitment-weaving mapping note lands on top of it.
2. Watch for Jeff's response to the team-commitment-stewardship memo link Darren sent via Telegram DM 2026-04-30 21:55 (https://github.com/gaiaaiagent/koi-processor/blob/regen-prod/docs/claims/team-commitment-stewardship.md). Original task framing was inverted — Darren sent the memo link to Jeff, not the other way. Jeff's reply will indicate what surface he's actually building for the holonic task board.

**This week:**
3. Surface matchmaking repo + rTime/Mycelium-solver/Poietic-Match/Spore intent-grammar comparison as concrete first joint artifact (2-page mapping note, not runtime integration).
4. Send Jeff three small async emails (don't bundle): JANUS↔Spore sheaf bridge note; rTime mapping note; bioregional-lens pilot. Let him respond at his own pace — the over-built packet from prep is too dense for his cadence.
5. Cherry-pick MCP fix `46520bc` from `feat/agentic-web-crawl-phase4` to `main` if desired (it's a generic bug fix riding on a feature branch).

**Mid-term decisions:**
6. Decide on Crypto Commons Gathering + Valley of the Commons attendance (Vienna, ~$500 one-way from Seattle, mid-Aug to end-Sept).
7. Investigate Bonding Curve Research Group as flow-funding pathway (Jeff's soft offer — most flow-functional venue in the TEC orbit).
8. Plan July overlap: Darren Comox arrival 2026-07-12; Texada Jul 12-17 (helping John in the woods, optional); Patricia's Imaginal House Salt Spring weekend of Jul 17; DWeb two weeks after.

**Waiting on Jeff (carryover):**
9. Brian's addressing-math paper + addressing-system email thread (originally promised Apr 23, still pending; not surfaced Apr 30).

**Park/defer:**
10. JANUS sheaf-formalism / Vince thread — formal-confidence-blocker only, not implementation-blocker. Darren's comparative-intake offer stands as second-source review.
11. Wikibase / `phase2-semantic-kg.md` revision — board-chair call still gates this; don't restructure until P2PF authority structure clarifies.
12. `p2pfoundation.wikibase.cloud` spin-up — never unilaterally; needs Jeff as co-admin.
13. Case-collision dedupe workstream on `wiki/` tree.
14. Backend cleanup: dangling `andrew-millicent` RID points at the same canonical as the live `andrew-millison` RID (post-rename artifact). Backend admin op when convenient.

## Open Questions

- **Has the P2PF board-chair call happened?** Not surfaced Apr 30. Per Eve Swinnen update: Brussels P2PF is a one-person rescue vehicle, not an institution — the "board-chair outcome" may be more theatre than real authority. Real question: does Michel direct the $40K toward Jeff/Brian's infra work? That's a personal-relationship ask, not a governance ask.
- **Brian's still-private "escape vector" work** — Jeff alluded to a major next-gen system he and Brian are building, NDA-soft. Don't probe; don't surface externally. Jeff said Darren will be in the first hands-in cohort when ready.
- **Does Jeff's addressing architecture displace Wikibase?** Still partially. Bridge-note + mapping-note exploration before any plan restructure.

## Private / Not for Public Fork

- Infrastructure-funding / Michel-stipend thinking (in meeting note Reflections, vault-only)
- Bonfires team concerns (proprietary nature) — Jeff raised VC concerns, don't add to that
- Any architectural positioning not explicitly discussed with Jeff (e.g. Wikibase compression thinking)
