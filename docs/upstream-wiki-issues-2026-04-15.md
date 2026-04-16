# Upstream Wiki Issues — 2026-04-15

During automated redirect-chain resolution of the P2P Foundation wiki archive
(analysis date: 2026-04-15, archive snapshot from live-sync import), three classes
of data-quality issues were identified that require upstream action. The analysis
resolved 1,597 redirect chains successfully; the items below are the ones that
could not be resolved automatically and that maintainers may want to address on
the live wiki.

---

## 1. Redirect Cycles (35 pages)

These redirects form loops that prevent resolution. The most common pattern is a
**self-redirect**: the target page exists on the wiki, but is itself configured as
a redirect pointing back to the same title. The fix in each case is to ensure the
canonical target page contains actual content rather than a redirect.

### Self-redirect loops (one upstream target page redirects to itself)

Each entry below shows the redirect source(s), the cycle chain, and the canonical
title that should become a real article.

**Appropriate Technology** — 1 redirect
- `Appropriate technologies` → Appropriate Technology → *(self-loop)*
- Action: Remove the redirect on `Appropriate Technology`; ensure it is a real article.

**BUX/BUXB/Buxxb/BUXXB chain** — 3 redirects
- `Bux` → BUXB → Buxxb → BUXXB → *(self-loop)*
- `BUXB` → Buxxb → BUXXB → *(self-loop)*
- Action: Determine the canonical spelling (likely `BUXXB` or `BUX`), make it a
  real article, and redirect all variants to it.

**Commons-Based Peer Production** — 2 redirects
- `CBPP` → Commons-Based Peer Production → *(self-loop)*
- `Commons-based peer to peer production` → Commons-Based Peer Production → *(self-loop)*
- Action: Remove the self-redirect on `Commons-Based Peer Production`.

**CopyFair License** — 1 redirect
- `Copyfair Licence` → CopyFair License → *(self-loop)*
- Action: Remove the self-redirect on `CopyFair License`.

**Don Tapscott on Four Principles for the Open World** — 2 redirects
- `Don Tapscott on Four Principles for an Open World` → Don Tapscott on Four Principles for the Open World → *(self-loop)*
- `Don Tapscott on the Four Principles for the Open World` → Don Tapscott on Four Principles for the Open World → *(self-loop)*
- Action: Remove the self-redirect on `Don Tapscott on Four Principles for the Open World`.

**Ethics for Officials of Citizens Movements** — 2 redirects
- `Ethics for political candidates of WeBXL` → Ethics for Officials of Citizens Movements → *(self-loop)*
- `Ethics for political candidates of citizens movements` → Ethics for Officials of Citizens Movements → *(self-loop)*
- Action: Remove the self-redirect on `Ethics for Officials of Citizens Movements`.

**Free-Form Authority Models** — 1 redirect
- `Peer Governance - Free-form Authority Models` → Free-Form Authority Models → *(self-loop)*
- Action: Remove the self-redirect on `Free-Form Authority Models`.

**HackLab de Barracas** — 1 redirect
- `HackLab de Barracas-es` → HackLab de Barracas → *(self-loop)*
- Action: Remove the self-redirect on `HackLab de Barracas`.

**How Far Will User-Generated Content Go** — 1 redirect
- `How far will User Generated Content Go` → How Far Will User-Generated Content Go → *(self-loop)*
- Action: Remove the self-redirect on `How Far Will User-Generated Content Go`.

**Importance of Distributed Digital Production** — 1 redirect
- `Importance of istributed Digital Production` (note: missing "D") → Importance of Distributed Digital Production → *(self-loop)*
- Action: Remove the self-redirect on `Importance of Distributed Digital Production`.

**Localization Papers** — 1 redirect
- `Localizationpapers` → Localization Papers → *(self-loop)*
- Action: Remove the self-redirect on `Localization Papers`.

**NetDevice** — 1 redirect
- `Device2.0` → NetDevice → *(self-loop)*
- Action: Remove the self-redirect on `NetDevice`.

**Network Resource Planning** — 3 redirects *(NRP cluster)*
- `NRP-CAS` → Network Resource Planning → *(self-loop)*
- `NRP` → NRP-CAS → Network Resource Planning → *(self-loop)*
- `Network resource planning and contribution accounting` → NRP-CAS → Network Resource Planning → *(self-loop)*
- Action: Remove the self-redirect on `Network Resource Planning`; also verify
  `NRP-CAS` points to the right canonical title.

**Open Design** — 1 redirect
- `Free Design` → Open Design → *(self-loop)*
- Action: Remove the self-redirect on `Open Design`.

**Open Source Appropriate Technology** — 2 redirects
- `OSAT` → Open Source Appropriate Technology → *(self-loop)*
- `Open source appropriate technologies` → Open Source Appropriate Technology → *(self-loop)*
- Action: Remove the self-redirect on `Open Source Appropriate Technology`.

**Open Source Software** — 1 redirect
- `Open-source software` → Open Source Software → *(self-loop)*
- Action: Remove the self-redirect on `Open Source Software`.

**Owner-Centric Authority Model** — 1 redirect
- `Peer Governance - Owner-centric Authority Model` → Owner-Centric Authority Model → *(self-loop)*
- Action: Remove the self-redirect on `Owner-Centric Authority Model`.

**P2P Lending** — 1 redirect
- `Peer to peer lending` → P2P Lending → *(self-loop)*
- Action: Remove the self-redirect on `P2P Lending`.

**Peer Production** — 1 redirect
- `P2p production` → Peer Production → *(self-loop)*
- Action: Remove the self-redirect on `Peer Production`.

**Peer to Peer** — 1 redirect
- `P2P` → Peer to Peer → *(self-loop)*
- Action: Remove the self-redirect on `Peer to Peer`.

**Product-Centered Local Economy vs People-Centered Local Economy** — 1 redirect
- `Product-Centered local economyvs People-Centered local economy` → Product-Centered Local Economy vs People-Centered Local Economy → *(self-loop)*
- Action: Remove the self-redirect on `Product-Centered Local Economy vs People-Centered Local Economy`.

**Resource-Based Economy** — 2 redirects
- `RBE` → Resource-Based Economy → *(self-loop)*
- `Resource Based Economy` → Resource-Based Economy → *(self-loop)*
- Action: Remove the self-redirect on `Resource-Based Economy`.

**Some Remarks Regarding the Contributions of Michel Bauwens to the Activities of the University of Amsterdam** — 1 redirect
- `Some remarks regarding the contributions of Michel Bauwensto the activities of the University of Amsterdam` → Some Remarks Regarding... → *(self-loop)*
- Action: Remove the self-redirect on the long-form canonical title.

**Technological Singularity** — 2 redirects
- `Singularity` → Technological Singularity → *(self-loop)*
- `The Singularity` → Technological Singularity → *(self-loop)*
- Action: Remove the self-redirect on `Technological Singularity`.

**Who's Who** — 1 redirect
- `Who's who de la P2P Foundation` → Who's Who → *(self-loop)*
- Action: Remove the self-redirect on `Who's Who`.

**Wiki-Historias** — 1 redirect
- `Wiki-historias-es` → Wiki-Historias → *(self-loop)*
- Action: Remove the self-redirect on `Wiki-Historias`.

---

## 2. Broken Redirect Targets (64 unique pages)

These redirects point to a target page that does not exist in the wiki. They are
grouped below by target type. For each, the options are: (a) delete the redirect,
(b) create the target page, or (c) correct the redirect to point to an existing page.

### 2a. Content pages with missing or mis-named targets (18 pages)

These redirect to content pages that appear to have been renamed, deleted, or
never created.

| Redirect title | Target | Issue |
|---|---|---|
| `Becoming a Member the P2P Foundation` | `New_Member_Questionnaire` | Target page not found |
| `Bookcrossings` | `Book Crossing` | Target page not found |
| `Cinquieme Pouvoir` | `Cinquième_Pouvoir` | Accented title not found (encoding issue) |
| `Common Resources Distribution Pool` | `P2P Resource Distribution Pool` | Target page not found |
| `Common Resources in a P2P Network` | `Common Resource` | Target page not found |
| `Commons Based` | `Commons-Based_Business_Models` | Target page not found |
| `Commons Based Business` | `Commons-Based_Business_Models` | Target page not found |
| `Commons-Based` | `Commons-Based_Business_Models` | Target page not found |
| `Commons-Based Enterprise` | `Commons-Based_Business_Models` | Target page not found |
| `Dafermos, George` | `George_Dafermos` | Target page not found |
| `Drieghe, Geert` | `Geert Drieghe` | Target page not found |
| `Generation Participation` | `Génération_Participation` | Accented title not found (encoding issue) |
| `Mode of exchange` | `Mode of Eexchange` | **Typo in target** — "Eexchange" has double-e; correct to `Mode of Exchange` |
| `Orange Report` | `Synthetic_Overview_of_the_Collaborative_Economy\|Synthetic Overview of the Collaborative Economy` | **Malformed target** — pipe character in redirect target is invalid MediaWiki syntax |
| `P2P Foundation Knowledge Commons Peer Property Channel` | `P2P Foundation Channels` | Target page not found |
| `P2P Property Development and Management` | `P2P Development and Management of Common Resources` | Target page not found |
| `Posting and Publishing Feeds` | `OccupyWeb Posting and Publishing Feeds` | Target page not found |
| `Quilligan, James` | `James_Quilligan` | Target page not found |

### 2b. Category namespace redirects (13 pages)

These redirect into Category: or :Category: namespace. The leading-colon form
(`:Category:Foo`) is non-standard and may not resolve correctly on all wiki
software versions.

| Redirect title | Target |
|---|---|
| `Africa` | `Category:Africa` |
| `Category-Open Intelligence` *(filesystem only)* | `:Category:Open Decision-Support` |
| `Category-P2P Wiki Projects` *(filesystem only)* | `:Category:P2P Resource Collections` |
| `Collaborative Economy` | `:Category:Collaborative Economy` |
| `Government Owned` | `Category:Government Owned` |
| `Municipally Owned` | `Category:Government Owned` |
| `Open Source Medical Imaging` | `:Category:Medical Imaging` |
| `P2P Foundation Global Network` | `:Category:World` |
| `P2P Foundation Knowledge Commons` | `:Category:P2P Foundation Knowledge Commons` |
| `P2P Foundation Wiki` | `:Category:P2P Foundation Wiki` |
| `P2P Politics` | `:Category:P2P Politics` |
| `P2P Toolkit` | `:Category:P2P Infrastructure` |
| `P2PStack` | `:Category:P2P Collaboration Stack` |
| `P2P Women` | `Category:P2P_Women` |
| `State Owned` | `Category:Government Owned` |
| `Templates` | `:Category:Templates` |
| `User Ownership Theory` | `:Category:User Owned` |

> Note: Redirects to Category pages are sometimes intentional (to help readers find
> category pages via article-style titles). If these are intentional, they are
> working correctly on the live wiki — these are flagged only because the
> category pages themselves were not in our article corpus.

### 2c. User page redirects (9 pages)

These biographical redirects point to User: account pages rather than proper
biographical articles.

| Redirect title | Target |
|---|---|
| `Andrés Delgado` | `User:Jorgeandr3s` |
| `Eli Farley` | `User:Elifarley` |
| `Hellekin O. Wolf` | `User:hellekin` |
| `Inquiry Live` | `User:JonAwbrey` |
| `James Burke` | `User:Jamesburke` |
| `Joshua Pearce` | `User:J.M.Pearce` |
| `Kevin Flanagan` | `User:KevinF` |
| `Logic Live` | `User:JonAwbrey` |
| `Patrick Anderson` | `:User:Patrick-T-Anderson` |

> Recommended: Create a biographical article for each person and redirect to
> the article rather than the User page, or delete these redirects if the
> subjects are no longer active contributors.

### 2d. Help page redirects (10 pages)

These redirect to `Help:` namespace pages. They are likely navigation shortcuts.

| Redirect title | Target |
|---|---|
| `Creating a Biographical Entry` | `Help:Creating a Biographical Entry` |
| `Differences Between This Wiki and Wikipedia` | `Help:Differences Between This Wiki and Wikipedia` |
| `P2P Foundation Blog Maintenance` | `Help:Contents` |
| `P2P Foundation Wiki Advanced Editing` | `Help:Editing wiki pages` |
| `P2P Foundation Wiki Category Usage` | `Help:Using Categories` |
| `P2P Foundation Wiki Introduction to Editing` | `Help:Contents` |
| `P2P Foundation Wiki LST` | `Help:Using LST` |
| `P2P Foundation Wiki for Shameless Promotion` | `Help:Your User Page and Bio` |
| `P2pFoundation:Help` | `Help:Contents` |
| `Template-Deliciousfeed` *(filesystem only)* | `Help:Adding RSS Feeds` |
| `Using Citations on the P2P Foundation Wiki` | `Help:References` |

### 2e. Other namespace redirects (9 pages)

| Redirect title | Target | Namespace |
|---|---|---|
| `A Definition of P2P Urbanism` | `File:P2PUrbanism definition.pdf` | File |
| `About` | `project:About` | Project |
| `About The Foundation` | `project:About` | Project |
| `Category` | `Special:Categories` | Special |
| `P2P Foundation` | `P2P Foundation:About` | Project |
| `Testpage2` | `P2P Foundation:LinkList template explanation` | Project |
| `Welcome` | `MediaWiki:Welcomecreation` | MediaWiki |
| `WikiSprint - 20M-es` | `Form:WikiSprint20M-es` | Form |
| `WikiSprint - 20M/es` | `Form:WikiSprint20M-es` | Form |

---

## 3. Recommendation

The issues above were generated by an automated redirect-chain resolver applied to
a local archive of the P2P Foundation wiki (40,239 pages, imported 2026-04-14).
The SQL query that generated these lists can be re-run periodically against any
updated archive to detect new issues as the wiki evolves.

**Highest-priority fixes** (would help most readers):
1. **Self-redirect loops** — 35 pages. Each affected canonical title is likely
   a real article with a misconfigured redirect tag. Removing the
   `#REDIRECT` from the canonical page resolves the entire cluster of upstream
   redirects pointing to it.
2. **Typo in `Mode of exchange` target** — `Mode of Eexchange` has a double-e;
   correcting this fixes at least two redirects.
3. **Malformed pipe in `Orange Report`** — the target
   `Synthetic_Overview_of_the_Collaborative_Economy|Synthetic Overview...`
   is invalid MediaWiki redirect syntax; the target should be the title only
   (no pipe).
4. **Biographical redirects to User pages** — 9 pages where person articles
   redirect to user accounts rather than biographical content.

If you would like to share the underlying SQL or the redirect-manifest tooling
so you can run this analysis yourselves, please ask. Happy to help set this up
as a recurring diagnostic.
