"""
Tests for resolve_redirects.py — pure Python, no DB, uses tmpdir fixtures.

Covers: redirect parsing, chain resolution, case-insensitive fallback,
ambiguous matches, cycle detection, depth exceeded, idempotency,
encoding errors, section/label stripping, manifest generation, apply, verify,
--fetch-missing API fallback.
"""

import json
import os
import hashlib
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the script under test
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolve_redirects import (
    parse_redirect,
    split_target,
    find_target_file,
    resolve_chain,
    generate_manifest,
    apply_manifest,
    verify_apply,
    build_normalized_content,
    build_status_content,
    fetch_wiki_content,
    REDIRECT_RE,
    RESOLVED_AT_RE,
    INLINE_BEGIN,
    INLINE_END,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_wiki(tmp_path: Path, files: dict) -> Path:
    """Create a wiki directory with the given files (name → content)."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    for name, content in files.items():
        (wiki_dir / name).write_text(content, encoding='utf-8')
    return wiki_dir


def make_redirect(target: str) -> str:
    """Create a #REDIRECT file content."""
    return f"#REDIRECT [[{target}]]\n"


# ---------------------------------------------------------------------------
# parse_redirect
# ---------------------------------------------------------------------------

class TestParseRedirect:
    def test_basic_redirect(self):
        assert parse_redirect("#REDIRECT [[Target]]") == "Target"

    def test_case_insensitive(self):
        assert parse_redirect("#redirect [[Target]]") == "Target"

    def test_leading_whitespace(self):
        assert parse_redirect("  #REDIRECT [[Target]]") == "Target"

    def test_empty_lines_before(self):
        assert parse_redirect("\n\n#REDIRECT [[Target]]") == "Target"

    def test_section_fragment(self):
        assert parse_redirect("#REDIRECT [[Target#Section]]") == "Target#Section"

    def test_pipe_label(self):
        assert parse_redirect("#REDIRECT [[Target|Label]]") == "Target|Label"

    def test_not_a_redirect(self):
        assert parse_redirect("Some regular content") is None

    def test_empty_content(self):
        assert parse_redirect("") is None

    def test_see_link_not_redirect(self):
        assert parse_redirect("See [[Target]]") is None


# ---------------------------------------------------------------------------
# split_target
# ---------------------------------------------------------------------------

class TestSplitTarget:
    def test_plain_title(self):
        assert split_target("Target") == ("Target", None, None)

    def test_with_section(self):
        assert split_target("Target#Section") == ("Target", "Section", None)

    def test_with_label(self):
        assert split_target("Target|Label") == ("Target", None, "Label")

    def test_with_section_and_label(self):
        assert split_target("Target#Section|Label") == ("Target", "Section", "Label")


# ---------------------------------------------------------------------------
# find_target_file
# ---------------------------------------------------------------------------

class TestFindTargetFile:
    def test_exact_match(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {"Target.mediawiki": "content"})
        path, status = find_target_file(wiki_dir, "Target")
        assert status == 'found'
        assert path == wiki_dir / "Target.mediawiki"

    def test_case_insensitive_first_char(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {"Foo.mediawiki": "content"})
        path, status = find_target_file(wiki_dir, "foo")
        assert status == 'found'
        # On macOS (case-insensitive FS) exact match may find it directly;
        # on case-sensitive FS the first-char fallback kicks in.
        # Either way, the file should be readable.
        assert path is not None
        assert path.exists()
        assert path.read_text() == "content"

    def test_not_found(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {"Other.mediawiki": "content"})
        path, status = find_target_file(wiki_dir, "Missing")
        assert status == 'not_found'
        assert path is None

    def test_empty_title(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {"Other.mediawiki": "content"})
        path, status = find_target_file(wiki_dir, "")
        assert status == 'not_found'


# ---------------------------------------------------------------------------
# resolve_chain
# ---------------------------------------------------------------------------

class TestResolveChain:
    def test_direct_resolution(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Target.mediawiki": "Canonical content here",
        })
        result = resolve_chain(wiki_dir, "Target")
        assert result['status'] == 'resolved'
        assert result['hops'] == 0
        assert result['target_title'] == "Target"

    def test_one_hop(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Alias.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Canonical content",
        })
        result = resolve_chain(wiki_dir, "Alias")
        assert result['status'] == 'resolved'
        assert result['hops'] == 1
        assert result['target_title'] == "Target"

    def test_two_hop_chain(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "A.mediawiki": "#REDIRECT [[B]]\n",
            "B.mediawiki": "#REDIRECT [[C]]\n",
            "C.mediawiki": "Final content",
        })
        result = resolve_chain(wiki_dir, "A")
        assert result['status'] == 'resolved'
        assert result['hops'] == 2
        assert result['target_title'] == "C"

    def test_unresolvable(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {})
        result = resolve_chain(wiki_dir, "Missing")
        assert result['status'] == 'unresolvable'

    def test_cycle_detected(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "A.mediawiki": "#REDIRECT [[B]]\n",
            "B.mediawiki": "#REDIRECT [[C]]\n",
            "C.mediawiki": "#REDIRECT [[A]]\n",
        })
        result = resolve_chain(wiki_dir, "A")
        assert result['status'] == 'cycle_detected'
        assert 'A' in result['chain']

    def test_depth_exceeded(self, tmp_path):
        """6-hop chain of distinct titles → depth_exceeded."""
        files = {}
        for i, name in enumerate("ABCDEFG"):
            if name == "G":
                files[f"{name}.mediawiki"] = "Final content"
            else:
                next_name = "ABCDEFG"[i + 1]
                files[f"{name}.mediawiki"] = f"#REDIRECT [[{next_name}]]\n"
        wiki_dir = make_wiki(tmp_path, files)
        result = resolve_chain(wiki_dir, "A")
        assert result['status'] == 'depth_exceeded'
        assert result['hops'] >= 5

    def test_section_fragment(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Target.mediawiki": "Content here",
        })
        result = resolve_chain(wiki_dir, "Target#Section")
        assert result['status'] == 'resolved'
        assert result['section'] == 'Section'

    def test_pipe_label(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Target.mediawiki": "Content here",
        })
        result = resolve_chain(wiki_dir, "Target|Label")
        assert result['status'] == 'resolved'
        assert result['target_title'] == "Target"


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

class TestGenerateManifest:
    def test_basic_manifest(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Canonical content",
            "Normal.mediawiki": "Regular page content",
        })
        manifest_path = tmp_path / "manifest.json"
        manifest = generate_manifest(wiki_dir, manifest_path)

        assert manifest['total_redirects'] == 1
        assert manifest['stats']['resolved'] == 1
        assert manifest_path.exists()

        records = manifest['records']
        assert len(records) == 1
        assert records[0]['source'] == 'Redirect.mediawiki'
        assert records[0]['status'] == 'resolved'

    def test_manifest_with_unresolvable(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Broken.mediawiki": "#REDIRECT [[Missing]]\n",
        })
        manifest_path = tmp_path / "manifest.json"
        manifest = generate_manifest(wiki_dir, manifest_path)

        assert manifest['stats']['unresolvable'] == 1

    def test_manifest_has_snapshot_hash(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Content",
        })
        manifest_path = tmp_path / "manifest.json"
        manifest = generate_manifest(wiki_dir, manifest_path)

        assert 'filesystem_snapshot_hash' in manifest
        assert len(manifest['filesystem_snapshot_hash']) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

class TestApply:
    def test_basic_apply(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Canonical content here",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)

        counters = apply_manifest(wiki_dir, manifest_path, branch=None,
                                  force_gates=True)
        assert counters['written'] == 1

        # Verify the rewritten file
        content = (wiki_dir / "Redirect.mediawiki").read_text(encoding='utf-8')
        assert content.startswith('#REDIRECT [[Target]]')
        assert '<!-- resolved-at:' in content
        assert INLINE_BEGIN in content
        assert 'Canonical content here' in content
        assert INLINE_END in content

    def test_idempotent_second_apply(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Canonical content",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)

        # First apply
        apply_manifest(wiki_dir, manifest_path, branch=None, force_gates=True)
        first_content = (wiki_dir / "Redirect.mediawiki").read_text()

        # Generate new manifest (already-normalized files excluded from hash)
        generate_manifest(wiki_dir, manifest_path)

        # Second apply — should skip via hash match
        counters = apply_manifest(wiki_dir, manifest_path, branch=None,
                                  force_gates=True)
        # The manifest from second dry-run won't include already-normalized files
        # so there's nothing to apply
        assert counters['written'] == 0

    def test_apply_unresolvable(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Broken.mediawiki": "#REDIRECT [[Missing]]\n",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)

        counters = apply_manifest(wiki_dir, manifest_path, branch=None,
                                  force_gates=True)
        assert counters['written'] == 1

        content = (wiki_dir / "Broken.mediawiki").read_text()
        assert '<!-- resolved-at:' in content
        assert '<!-- resolution-status: unresolvable -->' in content

    def test_apply_with_section_fragment(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target#Section]]\n",
            "Target.mediawiki": "Content with sections",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)

        apply_manifest(wiki_dir, manifest_path, branch=None, force_gates=True)

        content = (wiki_dir / "Redirect.mediawiki").read_text()
        assert '<!-- resolved-section: Section -->' in content

    def test_target_unchanged_no_rewrite(self, tmp_path):
        """Already-normalized file with unchanged target → zero diff."""
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Stable content",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)
        apply_manifest(wiki_dir, manifest_path, branch=None, force_gates=True)

        content_after_first = (wiki_dir / "Redirect.mediawiki").read_text()

        # Now create a manifest that references the already-normalized file
        # by inserting a record manually
        manifest = json.loads(manifest_path.read_text())
        manifest['records'] = [{
            'source': 'Redirect.mediawiki',
            'original_target': 'Target',
            'resolved_target': 'Target',
            'hops': 0,
            'status': 'resolved',
            'body_bytes': 14,
            'notes': '',
        }]
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

        counters = apply_manifest(wiki_dir, manifest_path, branch=None,
                                  force_gates=True)
        assert counters['skipped_hash'] == 1
        assert counters['written'] == 0

        content_after_second = (wiki_dir / "Redirect.mediawiki").read_text()
        assert content_after_first == content_after_second


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class TestVerify:
    def test_verify_success(self, tmp_path):
        wiki_dir = make_wiki(tmp_path, {
            "Redirect.mediawiki": "#REDIRECT [[Target]]\n",
            "Target.mediawiki": "Content",
        })
        manifest_path = tmp_path / "manifest.json"
        generate_manifest(wiki_dir, manifest_path)
        apply_manifest(wiki_dir, manifest_path, branch=None, force_gates=True)

        counters = verify_apply(wiki_dir, manifest_path)
        assert counters['verified'] == 1
        assert counters['mismatch'] == 0
        assert counters['errors'] == 0


# ---------------------------------------------------------------------------
# Encoding errors
# ---------------------------------------------------------------------------

class TestEncodingError:
    def test_non_utf8_source_skipped(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        # Write a non-UTF-8 file
        (wiki_dir / "Bad.mediawiki").write_bytes(b'\xff\xfe#REDIRECT [[Target]]')
        (wiki_dir / "Target.mediawiki").write_text("Content", encoding='utf-8')

        manifest_path = tmp_path / "manifest.json"
        manifest = generate_manifest(wiki_dir, manifest_path)
        assert manifest['stats']['encoding_error'] == 1

        # Apply should skip it
        counters = apply_manifest(wiki_dir, manifest_path, branch=None,
                                  force_gates=True)
        assert counters['skipped_status'] == 1


# ---------------------------------------------------------------------------
# --fetch-missing API fallback
# ---------------------------------------------------------------------------

def _mock_api_response(content: str) -> bytes:
    """Build a mock MediaWiki API JSON response with the given wikitext."""
    return json.dumps({
        'query': {
            'pages': {
                '12345': {
                    'pageid': 12345,
                    'title': 'Target',
                    'revisions': [{
                        'slots': {
                            'main': {
                                'contentmodel': 'wikitext',
                                'contentformat': 'text/x-wiki',
                                '*': content,
                            }
                        }
                    }]
                }
            }
        }
    }).encode('utf-8')


def _mock_api_missing() -> bytes:
    """Build a mock MediaWiki API JSON response for a missing page."""
    return json.dumps({
        'query': {
            'pages': {
                '-1': {
                    'ns': 0,
                    'title': 'Missing Page',
                    'missing': '',
                }
            }
        }
    }).encode('utf-8')


class TestFetchMissing:
    def test_api_success_resolves_self_reference(self, tmp_path):
        """Self-referencing redirect + mock API returning wikitext → resolved_via_api."""
        wiki_dir = make_wiki(tmp_path, {
            # On a case-insensitive FS, "Target.mediawiki" and a redirect
            # pointing to "Target" are the same file (self-reference).
            # Simulate by making the only file be the redirect stub itself.
            "Target.mediawiki": "#REDIRECT [[Target]]\n",
        })
        manifest_path = tmp_path / "manifest.json"

        canonical_content = "This is the canonical page content from the wiki."
        mock_resp = MagicMock()
        mock_resp.read.return_value = _mock_api_response(canonical_content)
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('resolve_redirects.urllib.request.urlopen', return_value=mock_resp):
            manifest = generate_manifest(wiki_dir, manifest_path,
                                         fetch_missing=True)

        assert manifest['stats']['resolved_via_api'] == 1
        assert manifest['stats']['unresolvable'] == 0
        record = manifest['records'][0]
        assert record['status'] == 'resolved_via_api'
        assert record['api_content'] == canonical_content

    def test_api_missing_stays_unresolvable(self, tmp_path):
        """Mock API returns missing-page → status stays unresolvable."""
        wiki_dir = make_wiki(tmp_path, {
            "Broken.mediawiki": "#REDIRECT [[Nonexistent Page]]\n",
        })
        manifest_path = tmp_path / "manifest.json"

        mock_resp = MagicMock()
        mock_resp.read.return_value = _mock_api_missing()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('resolve_redirects.urllib.request.urlopen', return_value=mock_resp):
            manifest = generate_manifest(wiki_dir, manifest_path,
                                         fetch_missing=True)

        assert manifest['stats']['unresolvable'] == 1
        assert manifest['stats'].get('resolved_via_api', 0) == 0

    def test_api_error_marks_api_error(self, tmp_path):
        """Mock API raises network timeout → status is api_error."""
        wiki_dir = make_wiki(tmp_path, {
            "Broken.mediawiki": "#REDIRECT [[Timeout Page]]\n",
        })
        manifest_path = tmp_path / "manifest.json"

        import urllib.error
        with patch('resolve_redirects.urllib.request.urlopen',
                   side_effect=urllib.error.URLError('timeout')):
            manifest = generate_manifest(wiki_dir, manifest_path,
                                         fetch_missing=True)

        assert manifest['stats']['api_error'] == 1
        assert manifest['stats']['unresolvable'] == 0
        record = manifest['records'][0]
        assert record['status'] == 'api_error'
        assert 'timeout' in record['notes'].lower()

    def test_rate_limiting_enforced(self, tmp_path):
        """N API calls take >= N-1 seconds (1 req/sec throttle)."""
        # Create 3 unresolvable redirects
        wiki_dir = make_wiki(tmp_path, {
            "A.mediawiki": "#REDIRECT [[Missing A]]\n",
            "B.mediawiki": "#REDIRECT [[Missing B]]\n",
            "C.mediawiki": "#REDIRECT [[Missing C]]\n",
        })
        manifest_path = tmp_path / "manifest.json"

        call_count = 0
        def mock_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.read.return_value = _mock_api_missing()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        start = time.monotonic()
        with patch('resolve_redirects.urllib.request.urlopen', side_effect=mock_urlopen):
            generate_manifest(wiki_dir, manifest_path, fetch_missing=True)
        elapsed = time.monotonic() - start

        assert call_count == 3
        # 3 calls → at least 2 seconds of sleep (N-1)
        assert elapsed >= 2.0, f"Expected >= 2.0s, got {elapsed:.2f}s"

    def test_fetch_missing_off_by_default(self, tmp_path):
        """Without --fetch-missing, self-references stay unresolvable, no API calls."""
        wiki_dir = make_wiki(tmp_path, {
            "Target.mediawiki": "#REDIRECT [[Target]]\n",
        })
        manifest_path = tmp_path / "manifest.json"

        with patch('resolve_redirects.urllib.request.urlopen') as mock_urlopen:
            manifest = generate_manifest(wiki_dir, manifest_path,
                                         fetch_missing=False)

        mock_urlopen.assert_not_called()
        assert manifest['stats']['unresolvable'] == 1
        assert manifest['stats'].get('resolved_via_api', 0) == 0
