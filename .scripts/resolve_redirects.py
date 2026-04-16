#!/usr/bin/env python3
"""
Filesystem redirect resolver for the P2P Foundation wiki archive.

Detects #REDIRECT files, follows redirect chains, and inlines canonical
target content into redirect files so agents get content on first read.

Modes:
    --dry-run --manifest <path>   Generate a JSON manifest of all redirects
    --apply --manifest <path>     Rewrite redirect files using the manifest
    --verify-apply                Post-apply integrity check

The authoritative redirect regex:
    ^\\s*#REDIRECT\\s*\\[\\[([^\\]]+)\\]\\]   (case-insensitive, first non-empty line)

Usage:
    python .scripts/resolve_redirects.py --dry-run --manifest .scripts/redirect-manifest.json
    python .scripts/resolve_redirects.py --apply --manifest .scripts/redirect-manifest.json --branch redirect-resolver-fs-2026-04-15
    python .scripts/resolve_redirects.py --verify-apply --manifest .scripts/redirect-manifest.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Authoritative redirect regex — case-insensitive, first non-empty line
REDIRECT_RE = re.compile(r'^\s*#REDIRECT\s*\[\[([^\]]+)\]\]', re.IGNORECASE)

# Marker for already-normalized files
RESOLVED_AT_RE = re.compile(r'<!--\s*resolved-at:\s*(.+?)\s*-->')

# Marker sentinel for inlined content
INLINE_BEGIN = '<!-- BEGIN INLINED TARGET CONTENT [plan082-8f3a] -->'
INLINE_END = '<!-- END INLINED TARGET CONTENT [plan082-8f3a] -->'

# Max redirect chain depth
MAX_HOPS = 5

# Wiki API defaults
DEFAULT_API_URL = 'https://wiki.p2pfoundation.net/api.php'
USER_AGENT = 'Mozilla/5.0 (compatible; resolve_redirects/1.0; +p2pfoundation-wiki-archive; contact: zaldarren@gmail.com)'
API_TIMEOUT = 10  # seconds per request
API_RATE_LIMIT = 1.0  # seconds between requests


def parse_redirect(content: str) -> Optional[str]:
    """Extract redirect target from file content. Returns None if not a redirect."""
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = REDIRECT_RE.match(stripped)
        return m.group(1) if m else None
    return None


def split_target(raw_target: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Split redirect target into (title, section_fragment, label).

    e.g. "Target#Section|Label" -> ("Target", "Section", "Label")
    """
    section = None
    label = None
    title = raw_target

    # Strip pipe-label first (MediaWiki convention: [[Target|Label]])
    if '|' in title:
        title, label = title.split('|', 1)

    # Strip section fragment
    if '#' in title:
        title, section = title.split('#', 1)

    return title.strip(), section, label


def find_target_file(wiki_dir: Path, target_title: str) -> Tuple[Optional[Path], str]:
    """Find the .mediawiki file for a target title.

    Returns (path, status) where status is 'found', 'ambiguous', or 'not_found'.
    Lookup order:
    1. Exact filename match: <target_title>.mediawiki
    2. Case-insensitive first-char fallback
    """
    # Exact match
    exact = wiki_dir / f"{target_title}.mediawiki"
    if exact.exists():
        return exact, 'found'

    # Case-insensitive first-char fallback
    if target_title:
        # Try swapping case of first character
        variants = []
        alt = target_title[0].swapcase() + target_title[1:]
        alt_path = wiki_dir / f"{alt}.mediawiki"
        if alt_path.exists():
            variants.append(alt_path)

        # Also do a broader case-insensitive glob for first char
        # (handles edge cases beyond simple swap)
        pattern = f"[{target_title[0].lower()}{target_title[0].upper()}]{target_title[1:]}.mediawiki"
        try:
            for candidate in wiki_dir.glob(pattern):
                if candidate not in variants and candidate != exact:
                    variants.append(candidate)
        except Exception:
            pass

        if len(variants) == 1:
            return variants[0], 'found'
        elif len(variants) > 1:
            return None, 'ambiguous'

    return None, 'not_found'


def resolve_chain(wiki_dir: Path, start_target: str,
                  source_path: Optional[Path] = None) -> Dict[str, Any]:
    """Follow a redirect chain from start_target to its canonical page.

    Args:
        wiki_dir: Directory containing .mediawiki files
        start_target: The redirect target string (may include #section|label)
        source_path: Path to the source redirect file (for self-reference detection
                     on case-insensitive filesystems)

    Returns a dict with:
        target_title: final resolved title
        target_path: Path to the canonical file
        hops: number of redirects followed
        status: resolved | unresolvable | ambiguous | cycle_detected | depth_exceeded
        chain: list of titles visited
        section: section fragment from original redirect (if any)
    """
    title, section, label = split_target(start_target)
    visited = []
    current_title = title
    hops = 0

    while True:
        if current_title in visited:
            return {
                'target_title': None,
                'target_path': None,
                'hops': hops,
                'status': 'cycle_detected',
                'chain': visited + [current_title],
                'section': section,
            }

        visited.append(current_title)

        target_path, find_status = find_target_file(wiki_dir, current_title)

        if find_status == 'ambiguous':
            return {
                'target_title': current_title,
                'target_path': None,
                'hops': hops,
                'status': 'ambiguous',
                'chain': visited,
                'section': section,
            }

        if target_path is None:
            return {
                'target_title': current_title,
                'target_path': None,
                'hops': hops,
                'status': 'unresolvable',
                'chain': visited,
                'section': section,
            }

        # Detect self-reference on case-insensitive FS: if the found file
        # is the same inode as the source redirect, it's unresolvable (the
        # wiki had a case-variant redirect pointing to itself).
        # os.path.samefile compares inodes, unlike Path.resolve() which
        # preserves case on macOS.
        if source_path and hops == 0:
            try:
                if os.path.samefile(str(target_path), str(source_path)):
                    return {
                        'target_title': current_title,
                        'target_path': None,
                        'hops': 0,
                        'status': 'unresolvable',
                        'chain': visited,
                        'section': section,
                    }
            except OSError:
                pass

        # Read the target file
        try:
            target_content = target_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return {
                'target_title': current_title,
                'target_path': str(target_path),
                'hops': hops,
                'status': 'target_encoding_error',
                'chain': visited,
                'section': section,
            }

        # Check if target is also a redirect
        next_target = parse_redirect(target_content)
        if next_target is None:
            # Found the canonical page
            return {
                'target_title': current_title,
                'target_path': target_path,
                'hops': hops,
                'status': 'resolved',
                'chain': visited,
                'section': section,
            }

        # Follow the chain
        hops += 1
        if hops >= MAX_HOPS:
            return {
                'target_title': current_title,
                'target_path': None,
                'hops': hops,
                'status': 'depth_exceeded',
                'chain': visited,
                'section': section,
            }

        next_title, _, _ = split_target(next_target)
        current_title = next_title


def fetch_wiki_content(title: str, api_url: str = DEFAULT_API_URL) -> Dict[str, Any]:
    """Fetch canonical wikitext for a page title from the MediaWiki API.

    The API follows redirect chains server-side (redirects=1).

    Returns a dict with:
        status: 'found' | 'missing' | 'error'
        content: wikitext string (only when status == 'found')
        error: error message (only when status == 'error')
    """
    params = urllib.parse.urlencode({
        'action': 'query',
        'titles': title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'format': 'json',
        'redirects': '1',
    })
    url = f"{api_url}?{params}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        return {'status': 'error', 'error': str(e)}

    pages = data.get('query', {}).get('pages', {})
    for page_id, page in pages.items():
        if 'missing' in page or int(page_id) < 0:
            return {'status': 'missing'}
        revisions = page.get('revisions', [])
        if not revisions:
            return {'status': 'missing'}
        slots = revisions[0].get('slots', {})
        main_slot = slots.get('main', {})
        content = main_slot.get('*')
        if content is None:
            return {'status': 'missing'}
        return {'status': 'found', 'content': content}

    return {'status': 'missing'}


def compute_fs_snapshot_hash(wiki_dir: Path) -> str:
    """Compute deterministic hash of redirect-source files (un-normalized only)."""
    entries = []
    for f in sorted(wiki_dir.glob("*.mediawiki")):
        try:
            content = f.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        # Skip already-normalized files
        if RESOLVED_AT_RE.search(content):
            continue
        if parse_redirect(content) is not None:
            file_hash = hashlib.sha256(f.read_bytes()).hexdigest()
            rel = f.name
            entries.append(f"{rel}\0{file_hash}")

    payload = "\n".join(entries)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def generate_manifest(wiki_dir: Path, manifest_path: Path,
                      fetch_missing: bool = False,
                      api_url: str = DEFAULT_API_URL) -> Dict[str, Any]:
    """Generate a redirect manifest by scanning all .mediawiki files."""
    records = []
    stats = {
        'resolved': 0, 'unresolvable': 0, 'ambiguous': 0,
        'cycle_detected': 0, 'depth_exceeded': 0,
        'encoding_error': 0, 'target_encoding_error': 0,
        'resolved_via_api': 0, 'api_error': 0,
    }
    last_api_call: float = 0.0

    for f in sorted(wiki_dir.glob("*.mediawiki")):
        # Read file
        try:
            content = f.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            stats['encoding_error'] += 1
            records.append({
                'source': f.name,
                'original_target': None,
                'resolved_target': None,
                'hops': 0,
                'status': 'encoding_error',
                'body_bytes': 0,
                'notes': f'Non-UTF-8 file: {f.name}',
            })
            continue

        # Skip already-normalized files
        if RESOLVED_AT_RE.search(content):
            continue

        # Check if redirect
        target = parse_redirect(content)
        if target is None:
            continue

        # Resolve chain (pass source_path for self-reference detection)
        result = resolve_chain(wiki_dir, target, source_path=f)
        status = result['status']

        body_bytes = 0
        api_content = None

        # --fetch-missing: try the wiki API for unresolvable redirects
        if fetch_missing and status == 'unresolvable' and result.get('target_title'):
            # Rate limit: wait at least API_RATE_LIMIT since last call
            now = time.monotonic()
            elapsed = now - last_api_call
            if last_api_call > 0 and elapsed < API_RATE_LIMIT:
                time.sleep(API_RATE_LIMIT - elapsed)

            api_result = fetch_wiki_content(result['target_title'], api_url=api_url)
            last_api_call = time.monotonic()

            if api_result['status'] == 'found':
                status = 'resolved_via_api'
                api_content = api_result['content']
                body_bytes = len(api_content.encode('utf-8'))
            elif api_result['status'] == 'error':
                status = 'api_error'
            # else: 'missing' → stays unresolvable

        stats[status] += 1

        if status == 'resolved' and result['target_path']:
            body_bytes = result['target_path'].stat().st_size

        record = {
            'source': f.name,
            'original_target': target,
            'resolved_target': result['target_title'],
            'hops': result['hops'],
            'status': status,
            'body_bytes': body_bytes,
            'notes': '',
        }

        # Store API-fetched content in the manifest so --apply can use it
        if api_content is not None:
            record['api_content'] = api_content

        if result['section']:
            record['notes'] = f"section fragment: #{result['section']}"

        if status == 'ambiguous':
            record['notes'] = f"ambiguous case-variant match for '{result['target_title']}'"

        if status == 'cycle_detected':
            record['notes'] = f"cycle: {' → '.join(result['chain'])}"

        if status == 'api_error':
            record['notes'] = f"API error: {api_result.get('error', 'unknown')}"

        records.append(record)

    fs_hash = compute_fs_snapshot_hash(wiki_dir)

    manifest = {
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'wiki_dir': str(wiki_dir),
        'filesystem_snapshot_hash': fs_hash,
        'total_redirects': len(records),
        'stats': stats,
        'records': records,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                             encoding='utf-8')

    return manifest


def build_normalized_content(
    original_target: str,
    target_body: str,
    target_hash: str,
    hops,
    section: Optional[str],
) -> str:
    """Build the normalized redirect file content.

    hops can be an int (local resolution) or the string 'api' (resolved via API).
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    lines = [
        f'#REDIRECT [[{original_target}]]',
        '',
        f'<!-- resolved-at: {now} -->',
        f'<!-- resolved-hops: {hops} -->',
        f'<!-- target-hash: sha256-{target_hash} -->',
    ]
    if section:
        lines.append(f'<!-- resolved-section: {section} -->')
    lines.extend([
        INLINE_BEGIN,
        target_body,
        INLINE_END,
    ])
    return '\n'.join(lines) + '\n'


def build_status_content(
    original_redirect_line: str,
    original_target: str,
    status: str,
    notes: str,
) -> str:
    """Build content for unresolvable/ambiguous/cycle/depth-exceeded files."""
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    lines = [
        original_redirect_line,
        '',
        f'<!-- resolved-at: {now} -->',
        f'<!-- resolution-status: {status} -->',
    ]
    if notes:
        lines.append(f'<!-- resolution-notes: {notes} -->')
    return '\n'.join(lines) + '\n'


def apply_manifest(wiki_dir: Path, manifest_path: Path, branch: Optional[str],
                   force_gates: bool = False) -> Dict[str, int]:
    """Apply the manifest to rewrite redirect files.

    Pre-flight gates (skip with force_gates=True for tests):
    - Clean working tree
    - Correct branch
    - No open file handles
    - Manifest matches current filesystem state
    """
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    counters = {'written': 0, 'skipped_hash': 0, 'skipped_status': 0, 'errors': 0}

    if not force_gates:
        # Gate: clean working tree
        result = subprocess.run(
            ['git', 'diff', '--quiet'],
            cwd=str(wiki_dir.parent), capture_output=True,
        )
        if result.returncode != 0:
            print("ERROR: Working tree has unstaged changes. Commit or stash first.",
                  file=sys.stderr)
            sys.exit(1)

        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            cwd=str(wiki_dir.parent), capture_output=True,
        )
        if result.returncode != 0:
            print("ERROR: Working tree has staged changes. Commit or stash first.",
                  file=sys.stderr)
            sys.exit(1)

        # Gate: correct branch
        if branch:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=str(wiki_dir.parent), capture_output=True, text=True,
            )
            current_branch = result.stdout.strip()
            if current_branch != branch:
                print(f"ERROR: Expected branch '{branch}', currently on '{current_branch}'.",
                      file=sys.stderr)
                sys.exit(1)

        # Gate: manifest snapshot matches
        current_hash = compute_fs_snapshot_hash(wiki_dir)
        expected_hash = manifest.get('filesystem_snapshot_hash')
        if current_hash != expected_hash:
            print("ERROR: Filesystem has changed since manifest was generated. "
                  "Re-run --dry-run to regenerate the manifest.",
                  file=sys.stderr)
            sys.exit(1)

    for record in manifest['records']:
        source_path = wiki_dir / record['source']
        status = record['status']

        if not source_path.exists():
            counters['errors'] += 1
            continue

        if status == 'encoding_error':
            # Never touch encoding_error files
            counters['skipped_status'] += 1
            continue

        try:
            content = source_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            counters['errors'] += 1
            continue

        # Check if already normalized — idempotency via target-hash
        if RESOLVED_AT_RE.search(content):
            if status in ('resolved', 'resolved_via_api') and record.get('resolved_target'):
                # For resolved_via_api, check hash against stored api_content
                if status == 'resolved_via_api':
                    api_body = record.get('api_content', '')
                    current_target_hash = hashlib.sha256(
                        api_body.encode('utf-8')
                    ).hexdigest()
                else:
                    target_path = find_target_file(wiki_dir, record['resolved_target'])[0]
                    if not target_path:
                        counters['skipped_hash'] += 1
                        continue
                    current_target_hash = hashlib.sha256(
                        target_path.read_bytes()
                    ).hexdigest()
                # Extract existing target-hash
                hash_match = re.search(
                    r'<!--\s*target-hash:\s*sha256-([0-9a-f]+)\s*-->',
                    content
                )
                if hash_match and hash_match.group(1) == current_target_hash:
                    counters['skipped_hash'] += 1
                    continue
                # Target changed — rewrite
                if status == 'resolved_via_api':
                    target_body = api_body
                else:
                    target_body = target_path.read_text(encoding='utf-8')
                _, section_frag, _ = split_target(record['original_target'])
                hops = 'api' if status == 'resolved_via_api' else record['hops']
                new_content = build_normalized_content(
                    record['original_target'], target_body,
                    current_target_hash, hops, section_frag,
                )
            else:
                counters['skipped_status'] += 1
                continue
        elif status == 'resolved':
            target_path = find_target_file(wiki_dir, record['resolved_target'])[0]
            if not target_path:
                counters['errors'] += 1
                continue
            try:
                target_body = target_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                counters['errors'] += 1
                continue
            target_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
            _, section_frag, _ = split_target(record['original_target'])
            new_content = build_normalized_content(
                record['original_target'], target_body,
                target_hash, record['hops'], section_frag,
            )
        elif status == 'resolved_via_api':
            api_body = record.get('api_content', '')
            if not api_body:
                counters['errors'] += 1
                continue
            target_hash = hashlib.sha256(api_body.encode('utf-8')).hexdigest()
            _, section_frag, _ = split_target(record['original_target'])
            new_content = build_normalized_content(
                record['original_target'], api_body,
                target_hash, 'api', section_frag,
            )
        else:
            # Non-resolved statuses (unresolvable, ambiguous, cycle, depth,
            # api_error): write status marker
            first_line = content.splitlines()[0] if content.splitlines() else ''
            new_content = build_status_content(
                first_line, record['original_target'],
                status, record.get('notes', ''),
            )

        # Atomic write
        tmp_path = source_path.with_suffix('.mediawiki.tmp')
        try:
            tmp_path.write_text(new_content, encoding='utf-8')
            os.replace(str(tmp_path), str(source_path))
            counters['written'] += 1
        except Exception as e:
            counters['errors'] += 1
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

    return counters


def verify_apply(wiki_dir: Path, manifest_path: Path) -> Dict[str, int]:
    """Post-apply integrity check: verify inlined content matches target-hash."""
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    counters = {'verified': 0, 'mismatch': 0, 'skipped': 0, 'errors': 0}

    for record in manifest['records']:
        status = record['status']
        if status not in ('resolved', 'resolved_via_api'):
            counters['skipped'] += 1
            continue

        source_path = wiki_dir / record['source']
        if not source_path.exists():
            counters['errors'] += 1
            continue

        try:
            content = source_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            counters['errors'] += 1
            continue

        # Extract target-hash marker
        hash_match = re.search(
            r'<!--\s*target-hash:\s*sha256-([0-9a-f]+)\s*-->', content
        )
        if not hash_match:
            counters['errors'] += 1
            continue

        embedded_hash = hash_match.group(1)

        # Extract inlined content
        begin_idx = content.find(INLINE_BEGIN)
        end_idx = content.find(INLINE_END)
        if begin_idx < 0 or end_idx < 0:
            counters['errors'] += 1
            continue

        # The inlined content is between the markers
        inlined = content[begin_idx + len(INLINE_BEGIN) + 1:end_idx]
        if inlined.endswith('\n'):
            inlined = inlined[:-1]

        if status == 'resolved_via_api':
            # For API-resolved, verify the embedded hash matches the
            # inlined content itself (no local target file to compare)
            inlined_hash = hashlib.sha256(inlined.encode('utf-8')).hexdigest()
            if inlined_hash == embedded_hash:
                counters['verified'] += 1
            else:
                counters['mismatch'] += 1
        else:
            # Verify against actual target file
            target_path = find_target_file(wiki_dir, record['resolved_target'])[0]
            if not target_path:
                counters['errors'] += 1
                continue
            actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
            if actual_hash == embedded_hash:
                counters['verified'] += 1
            else:
                counters['mismatch'] += 1

    return counters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve #REDIRECT files in the P2P Foundation wiki archive."
    )
    parser.add_argument('--wiki-dir', type=Path,
                        default=Path(__file__).resolve().parent.parent / 'wiki',
                        help="Wiki directory (default: ../wiki relative to this script)")
    parser.add_argument('--manifest', type=Path,
                        help="Path to manifest JSON file")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true',
                      help="Generate manifest without modifying files")
    mode.add_argument('--apply', action='store_true',
                      help="Apply manifest to rewrite redirect files")
    mode.add_argument('--verify-apply', action='store_true',
                      help="Post-apply integrity check")

    parser.add_argument('--branch', type=str, default=None,
                        help="Expected branch name (for --apply gate)")
    parser.add_argument('--fetch-missing', action='store_true',
                        help="Fetch unresolvable redirects from the wiki API")
    parser.add_argument('--api-url', type=str, default=DEFAULT_API_URL,
                        help=f"MediaWiki API URL (default: {DEFAULT_API_URL})")
    parser.add_argument('--force-reresolve', action='store_true',
                        help="Force re-resolution of already-normalized files")
    parser.add_argument('--i-have-checked-the-gates', action='store_true',
                        help="Skip pre-flight gates (for testing only)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    wiki_dir = args.wiki_dir.resolve()
    if not wiki_dir.exists():
        print(f"ERROR: Wiki directory not found: {wiki_dir}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        if not args.manifest:
            print("ERROR: --manifest is required with --dry-run", file=sys.stderr)
            sys.exit(1)
        manifest = generate_manifest(wiki_dir, args.manifest,
                                      fetch_missing=args.fetch_missing,
                                      api_url=args.api_url)
        stats = manifest['stats']
        total = manifest['total_redirects']
        print(f"Manifest generated: {args.manifest}")
        print(f"Total redirects: {total}")
        for k, v in stats.items():
            if v == 0:
                continue
            pct = f" ({v/total*100:.1f}%)" if total > 0 else ""
            print(f"  {k}: {v}{pct}")
        resolved_total = stats.get('resolved', 0) + stats.get('resolved_via_api', 0)
        if total > 0:
            print(f"Total resolved: {resolved_total}/{total} ({resolved_total/total*100:.1f}%)")
        print(f"Filesystem snapshot hash: {manifest['filesystem_snapshot_hash']}")
        if args.fetch_missing:
            api_resolved = stats.get('resolved_via_api', 0)
            api_errors = stats.get('api_error', 0)
            still_unresolvable = stats.get('unresolvable', 0)
            print(f"\nFetch-missing results: "
                  f"{api_resolved} resolved_via_api, "
                  f"{still_unresolvable} still unresolvable, "
                  f"{api_errors} api_error")

    elif args.apply:
        if not args.manifest:
            print("ERROR: --manifest is required with --apply", file=sys.stderr)
            sys.exit(1)
        if not args.manifest.exists():
            print(f"ERROR: Manifest not found: {args.manifest}", file=sys.stderr)
            sys.exit(1)
        counters = apply_manifest(
            wiki_dir, args.manifest, args.branch,
            force_gates=args.i_have_checked_the_gates,
        )
        print(f"Apply complete:")
        print(f"  Written:      {counters['written']}")
        print(f"  Skipped (hash match): {counters['skipped_hash']}")
        print(f"  Skipped (status):     {counters['skipped_status']}")
        print(f"  Errors:       {counters['errors']}")

    elif args.verify_apply:
        if not args.manifest:
            print("ERROR: --manifest is required with --verify-apply", file=sys.stderr)
            sys.exit(1)
        counters = verify_apply(wiki_dir, args.manifest)
        print(f"Verify complete:")
        print(f"  Verified:  {counters['verified']}")
        print(f"  Mismatch:  {counters['mismatch']}")
        print(f"  Skipped:   {counters['skipped']}")
        print(f"  Errors:    {counters['errors']}")
        if counters['mismatch'] > 0 or counters['errors'] > 0:
            sys.exit(1)


if __name__ == '__main__':
    main()
