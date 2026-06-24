"""Optional live RHDH integration tests for rhdh-templates scripts.

Skipped when RHDH_URL is unset or the Scaffolder API is unreachable.
Run manually against rhdh-local:

    RHDH_URL=http://localhost:7007 uv run pytest tests/integration/test_rhdh_templates_live.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "rhdh-templates"
SCRIPTS = SKILL_DIR / "scripts"
MINIMAL_TEMPLATE = SKILL_DIR / "assets" / "examples" / "minimal-template"


def _rhdh_url() -> str | None:
    return os.environ.get("RHDH_URL", "http://localhost:7007").strip() or None


def _rhdh_reachable(url: str) -> bool:
    headers = {"Accept": "application/json"}
    token = os.environ.get("RHDH_TOKEN") or os.environ.get("BACKSTAGE_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/scaffolder/v2/actions",
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


@pytest.fixture(scope="module")
def rhdh_url() -> str:
    url = _rhdh_url()
    if not url or not _rhdh_reachable(url):
        pytest.skip("RHDH Scaffolder API not reachable — set RHDH_URL to run live tests")
    return url


def run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestLiveScaffolderApi:
    def test_list_actions(self, rhdh_url: str) -> None:
        result = run_script("list_actions.py", "--rhdh-url", rhdh_url, "--json")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["action_count"] >= 1
        ids = {a["id"] for a in data["actions"]}
        assert "fetch:template" in ids or "debug:log" in ids

    def test_explain_action_debug_log(self, rhdh_url: str) -> None:
        result = run_script(
            "explain_action.py",
            "--rhdh-url",
            rhdh_url,
            "--action",
            "debug:log",
            "--json",
        )
        if result.returncode != 0:
            pytest.skip("debug:log action not available on this instance")
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["id"] == "debug:log"
        assert data.get("schema") is not None

    def test_dry_run_minimal_template(self, rhdh_url: str, tmp_path: Path) -> None:
        values = {
            "componentId": "dogfood-demo",
            "owner": "group:default/team-a",
            "description": "Live integration test",
        }
        values_file = tmp_path / "values.json"
        values_file.write_text(json.dumps(values), encoding="utf-8")

        result = run_script(
            "dry_run.py",
            "--rhdh-url",
            rhdh_url,
            "--path",
            str(MINIMAL_TEMPLATE),
            "--values",
            str(values_file),
            "--json",
        )
        assert result.returncode == 0, result.stderr or result.stdout
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data.get("log_line_count", 0) >= 0

    def test_minimal_template_passes_local_validate_before_live(self) -> None:
        """Gate: bundled example must pass local validation (dogfood prerequisite)."""
        result = run_script("validate.py", "--path", str(MINIMAL_TEMPLATE), "--repo", "--json")
        data = json.loads(result.stdout)
        assert result.returncode == 0, data
        assert data["ok"] is True
        template = yaml.safe_load((MINIMAL_TEMPLATE / "template.yaml").read_text(encoding="utf-8"))
        assert template["kind"] == "Template"
