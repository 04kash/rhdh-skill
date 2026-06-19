"""Tests for rhdh-templates skill scripts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "rhdh-templates"
SCRIPTS = SKILL_DIR / "scripts"
REFERENCES = SKILL_DIR / "references"
BUNDLED_EXAMPLES = SKILL_DIR / "assets" / "examples"


def run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestRhdhTemplatesSkillMd:
    @pytest.fixture
    def skill_md(self) -> str:
        return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    @pytest.fixture
    def skill_frontmatter(self, skill_md: str) -> dict:
        match = re.match(r"^---\n(.*?)\n---", skill_md, re.DOTALL)
        assert match, "SKILL.md missing YAML frontmatter"
        return yaml.safe_load(match.group(1))

    def test_frontmatter_name(self, skill_frontmatter: dict) -> None:
        assert skill_frontmatter["name"] == "rhdh-templates"
        assert SKILL_DIR.name == skill_frontmatter["name"]

    def test_frontmatter_description(self, skill_frontmatter: dict) -> None:
        assert len(skill_frontmatter["description"]) > 50
        assert len(skill_frontmatter["description"]) <= 1024

    def test_has_intake_and_routing(self, skill_md: str) -> None:
        assert "<intake>" in skill_md
        assert "<routing>" in skill_md
        assert "**Wait for response before proceeding.**" in skill_md

    def test_has_essential_principles(self, skill_md: str) -> None:
        assert "<essential_principles>" in skill_md
        assert "<success_criteria>" not in skill_md

    def test_command_metadata_exists(self) -> None:
        meta = SCRIPTS / "command-metadata.json"
        data = json.loads(meta.read_text(encoding="utf-8"))
        expected = {
            "init",
            "templatize",
            "create",
            "add-parameter",
            "add-step",
            "add-skeleton",
            "create-location",
            "fix-gotchas",
            "validate",
            "list-actions",
            "dry-run",
            "explain-action",
            "examples",
        }
        assert expected.issubset(set(data.keys()))


class TestRhdhTemplatesReferences:
    @pytest.fixture
    def skill_md(self) -> str:
        return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_all_referenced_files_exist(self, skill_md: str) -> None:
        refs = re.findall(r"references/([\w./-]+\.(?:md|json))", skill_md)
        for ref in sorted(set(refs)):
            path = SKILL_DIR / "references" / ref
            assert path.is_file(), f"Missing reference file: {ref}"

    def test_schema_file_exists(self) -> None:
        schema = SKILL_DIR / "references" / "schemas" / "template-v1beta3.schema.json"
        assert schema.is_file()
        data = json.loads(schema.read_text(encoding="utf-8"))
        assert data["properties"]["apiVersion"]["enum"] == ["scaffolder.backstage.io/v1beta3"]

    def test_best_practices_reference_structure(self) -> None:
        content = (REFERENCES / "best-practices.md").read_text(encoding="utf-8")
        assert "<process>" in content
        assert "<authoring_checklist>" in content
        assert "Template Editor" in content
        assert "parameter-widgets.md" in content
        assert "parseEntityRef" in content

    def test_command_references_have_xml_structure(self) -> None:
        command_refs = [
            "init.md",
            "templatize.md",
            "create.md",
            "add-parameter.md",
            "add-step.md",
            "add-skeleton.md",
            "create-location.md",
            "fix-gotchas.md",
            "validate.md",
            "list-actions.md",
            "dry-run.md",
            "explain-action.md",
            "example-catalog.md",
        ]
        for name in command_refs:
            content = (REFERENCES / name).read_text(encoding="utf-8")
            assert "<process>" in content, f"{name} missing <process>"
            assert "<success_criteria>" in content, f"{name} missing <success_criteria>"


class TestInitScript:
    def test_scaffolds_layout(self, tmp_path: Path) -> None:
        result = run_script("init.py", "--path", str(tmp_path), "--json")
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert (tmp_path / "templates" / "example-template" / "template.yaml").exists()
        assert (tmp_path / "location.yaml").exists()
        assert data["ok"] is True


class TestAnalyzeScript:
    def test_detects_nodejs_project(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "demo-service", "description": "Demo app"}),
            encoding="utf-8",
        )
        (tmp_path / "catalog-info.yaml").write_text(
            "metadata:\n  name: demo-service\n  owner: group:default/team-a\n",
            encoding="utf-8",
        )
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yaml").write_text(
            "jobs:\n  build:\n    steps:\n      - run: echo ${{ github.ref }}\n"
        )

        result = run_script("analyze.py", "--path", str(tmp_path), "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "nodejs" in data["project_types"]
        assert data["candidate_count"] >= 1
        assert data["workflow_files"][0]["needs_raw_block"] is True


class TestCreateLocationScript:
    def test_discovers_templates(self, tmp_path: Path) -> None:
        template_dir = tmp_path / "templates" / "demo"
        template_dir.mkdir(parents=True)
        (template_dir / "template.yaml").write_text("kind: Template\n", encoding="utf-8")

        result = run_script("create_location.py", "--path", str(tmp_path), "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["template_count"] == 1
        assert (tmp_path / "location.yaml").exists()

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        template_dir = tmp_path / "templates" / "demo"
        template_dir.mkdir(parents=True)
        (template_dir / "template.yaml").write_text("kind: Template\n", encoding="utf-8")

        result = run_script("create_location.py", "--path", str(tmp_path), "--dry-run", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["written"] is False
        assert not (tmp_path / "location.yaml").exists()


class TestFixGotchasScript:
    def test_minimal_example_passes(self) -> None:
        template = BUNDLED_EXAMPLES / "minimal-template" / "template.yaml"
        result = run_script("fix_gotchas.py", "--path", str(template), "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["critical_count"] == 0

    def test_detects_wrong_api_version(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: backstage.io/v1beta2\nkind: Template\nspec:\n  steps: []\n",
            encoding="utf-8",
        )
        result = run_script("fix_gotchas.py", "--path", str(bad), "--json")
        data = json.loads(result.stdout)
        assert data["critical_count"] >= 1

        apply = run_script("fix_gotchas.py", "--path", str(bad), "--apply", "--json")
        assert "scaffolder.backstage.io/v1beta3" in bad.read_text(encoding="utf-8")
        assert json.loads(apply.stdout)["applied"] is True

    def test_fixes_pascal_case_action(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: scaffolder.backstage.io/v1beta3\n"
            "kind: Template\n"
            "spec:\n"
            "  parameters: []\n"
            "  steps:\n"
            "    - id: pub\n"
            "      action: publish:GitHub\n"
            "      input: {}\n",
            encoding="utf-8",
        )
        run_script("fix_gotchas.py", "--path", str(bad), "--apply")
        assert "action: publish:github" in bad.read_text(encoding="utf-8")

    def test_detects_sensitive_param_without_secret_field(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: scaffolder.backstage.io/v1beta3\n"
            "kind: Template\n"
            "metadata:\n"
            "  name: bad\n"
            "  tags:\n"
            "    - test\n"
            "spec:\n"
            "  parameters:\n"
            "    - title: Auth\n"
            "      properties:\n"
            "        apiToken:\n"
            "          title: API Token\n"
            "          type: string\n"
            "  steps: []\n",
            encoding="utf-8",
        )
        result = run_script("fix_gotchas.py", "--path", str(bad), "--json")
        data = json.loads(result.stdout)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        assert "sensitive-param-secret-field" in rule_ids

    def test_detects_missing_metadata_tags(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: scaffolder.backstage.io/v1beta3\n"
            "kind: Template\n"
            "metadata:\n"
            "  name: bad\n"
            "spec:\n"
            "  parameters: []\n"
            "  steps: []\n",
            encoding="utf-8",
        )
        result = run_script("fix_gotchas.py", "--path", str(bad), "--json")
        data = json.loads(result.stdout)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        assert "metadata-tags" in rule_ids


class TestExampleTemplates:
    @pytest.mark.parametrize(
        "example_dir",
        [
            "minimal-template",
            "nodejs-backend",
            "java-springboot",
        ],
    )
    def test_examples_pass_validate(self, example_dir: str) -> None:
        path = BUNDLED_EXAMPLES / example_dir
        result = run_script("validate.py", "--path", str(path), "--json")
        data = json.loads(result.stdout)
        assert result.returncode == 0, data
        assert data["ok"] is True
        assert data["critical_count"] == 0

    def test_examples_readme_exists(self) -> None:
        readme = BUNDLED_EXAMPLES / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "nodejs-backend" in text
        assert "java-springboot" in text


class TestSchemaValidateModule:
    @pytest.fixture
    def schema_module(self):
        sys.path.insert(0, str(SCRIPTS))
        import schema_validate

        return schema_validate

    def test_detects_missing_required_parameter(self, schema_module) -> None:
        data = {
            "apiVersion": "scaffolder.backstage.io/v1beta3",
            "kind": "Template",
            "metadata": {"name": "bad"},
            "spec": {
                "type": "service",
                "parameters": [
                    {
                        "title": "Details",
                        "required": ["missing"],
                        "properties": {"name": {"type": "string", "title": "Name"}},
                    }
                ],
                "steps": [{"id": "x", "action": "debug:log", "input": {}}],
            },
        }
        findings = schema_module.validate_structural(data)
        messages = " ".join(f["message"] for f in findings)
        assert "missing" in messages

    def test_detects_duplicate_step_ids(self, schema_module) -> None:
        data = {
            "apiVersion": "scaffolder.backstage.io/v1beta3",
            "kind": "Template",
            "metadata": {"name": "dup"},
            "spec": {
                "type": "service",
                "parameters": [],
                "steps": [
                    {"id": "same", "action": "debug:log", "input": {}},
                    {"id": "same", "action": "debug:log", "input": {}},
                ],
            },
        }
        findings = schema_module.validate_structural(data)
        assert any("Duplicate step id" in f["message"] for f in findings)

    def test_detects_unknown_parameter_reference(self, schema_module) -> None:
        data = {
            "apiVersion": "scaffolder.backstage.io/v1beta3",
            "kind": "Template",
            "metadata": {"name": "ref"},
            "spec": {
                "type": "service",
                "parameters": [
                    {
                        "title": "Details",
                        "properties": {"name": {"type": "string", "title": "Name"}},
                    }
                ],
                "steps": [
                    {
                        "id": "fetch",
                        "action": "fetch:template",
                        "input": {"url": "./s", "values": {"x": "${{ parameters.unknown }}"}},
                    }
                ],
            },
        }
        findings = schema_module.validate_cross_references(data)
        assert any("unknown parameter" in f["message"] for f in findings)

    def test_jsonschema_validates_good_example(self, schema_module) -> None:
        template = BUNDLED_EXAMPLES / "nodejs-backend" / "template.yaml"
        data = yaml.safe_load(template.read_text(encoding="utf-8"))
        findings, note = schema_module.validate_with_jsonschema(data, SKILL_DIR)
        if note and "not installed" in note:
            pytest.skip(note)
        critical = [f for f in findings if f["severity"] == "critical"]
        assert critical == []


class TestValidateScript:
    def test_minimal_example_passes(self) -> None:
        template = BUNDLED_EXAMPLES / "minimal-template"
        result = run_script("validate.py", "--path", str(template), "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["critical_count"] == 0

    def test_detects_bad_api_version(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: backstage.io/v1beta2\n"
            "kind: Template\n"
            "metadata:\n"
            "  name: bad\n"
            "spec:\n"
            "  parameters: []\n"
            "  steps: []\n",
            encoding="utf-8",
        )
        result = run_script("validate.py", "--path", str(bad), "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["critical_count"] >= 1

    def test_detects_missing_required_in_schema(self, tmp_path: Path) -> None:
        bad = tmp_path / "template.yaml"
        bad.write_text(
            "apiVersion: scaffolder.backstage.io/v1beta3\n"
            "kind: Template\n"
            "metadata:\n"
            "  name: bad\n"
            "spec:\n"
            "  type: service\n"
            "  parameters:\n"
            "    - title: Details\n"
            "      required:\n"
            "        - ghost\n"
            "      properties:\n"
            "        name:\n"
            "          type: string\n"
            "  steps:\n"
            "    - id: x\n"
            "      action: debug:log\n"
            "      input: {}\n",
            encoding="utf-8",
        )
        result = run_script("validate.py", "--path", str(bad), "--json")
        data = json.loads(result.stdout)
        schema_findings = [f for f in data["findings"] if f["check"] == "json_schema"]
        assert any("ghost" in f["message"] for f in schema_findings)

    def test_repo_flag_checks_location(self, tmp_path: Path) -> None:
        template_dir = tmp_path / "templates" / "demo"
        template_dir.mkdir(parents=True)
        (template_dir / "template.yaml").write_text(
            (BUNDLED_EXAMPLES / "minimal-template" / "template.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        result = run_script("validate.py", "--path", str(template_dir), "--repo", "--json")
        data = json.loads(result.stdout)
        location_findings = [f for f in data["findings"] if f["check"] == "location"]
        assert any("location.yaml not found" in f["message"] for f in location_findings)


class TestScaffolderApiHelpers:
    def test_parse_template_ref(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        from scaffolder_api import parse_template_ref

        kind, namespace, name = parse_template_ref("template:default/my-template")
        assert (kind, namespace, name) == ("template", "default", "my-template")

    def test_load_directory_contents(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(SCRIPTS))
        from scaffolder_api import load_directory_contents

        (tmp_path / "README.md").write_text("hello", encoding="utf-8")
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "file.txt").write_text("data", encoding="utf-8")

        contents = load_directory_contents(tmp_path)
        paths = {item["path"] for item in contents}
        assert paths == {"README.md", "nested/file.txt"}
        assert all("base64Content" in item for item in contents)


class TestExplainActionScript:
    def test_requires_exactly_one_mode(self) -> None:
        result = run_script(
            "explain_action.py",
            "--rhdh-url",
            "http://localhost:7007",
            "--json",
        )
        assert result.returncode == 2
        assert "exactly one" in result.stderr.lower()


class TestListExamplesScript:
    def test_help(self) -> None:
        result = run_script("list_examples.py", "--help")
        assert result.returncode == 0
        assert "--match" in result.stdout

    def test_recommended_backend_match(self) -> None:
        result = run_script(
            "list_examples.py",
            "--match",
            "spring boot backend with ci",
            "--limit",
            "3",
            "--json",
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["count"] >= 1
        ids = {item["id"] for item in data["examples"]}
        assert "spring-boot-backend" in ids

    def test_local_only_filter(self) -> None:
        result = run_script("list_examples.py", "--local-only", "--json")
        data = json.loads(result.stdout)
        assert data["count"] >= 2
        assert all(item.get("local_bundled") for item in data["examples"])

    def test_catalog_file_exists(self) -> None:
        catalog = SKILL_DIR / "assets" / "example-catalog.json"
        assert catalog.is_file()
        data = json.loads(catalog.read_text(encoding="utf-8"))
        assert len(data["examples"]) >= 20


class TestListActionsScript:
    def test_help(self) -> None:
        result = run_script("list_actions.py", "--help")
        assert result.returncode == 0
        assert "--rhdh-url" in result.stdout


class TestDryRunScript:
    def test_missing_template(self, tmp_path: Path) -> None:
        result = run_script(
            "dry_run.py",
            "--rhdh-url",
            "http://localhost:7007",
            "--path",
            str(tmp_path),
        )
        assert result.returncode != 0
