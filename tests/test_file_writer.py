"""Tests for file_writer — deterministic actuator (atomic writes)."""

from __future__ import annotations

import builtins
import json
from pathlib import Path
from typing import Any

import pytest

from lumina.staging.file_writer import write_from_template, _deep_merge
from lumina.staging import file_writer as _file_writer


# ------------------------------------------------------------------
# _deep_merge
# ------------------------------------------------------------------

class TestDeepMerge:
    def test_overlay_wins(self):
        base = {"a": 1, "b": 2}
        overlay = {"b": 99, "c": 3}
        result = _deep_merge(base, overlay)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_nested_merge(self):
        base = {"x": {"y": 1, "z": 2}}
        overlay = {"x": {"z": 99}}
        result = _deep_merge(base, overlay)
        assert result == {"x": {"y": 1, "z": 99}}

    def test_base_unchanged(self):
        base = {"a": {"b": 1}}
        overlay = {"a": {"b": 2}}
        _deep_merge(base, overlay)
        assert base == {"a": {"b": 1}}


# ------------------------------------------------------------------
# write_from_template
# ------------------------------------------------------------------

_PHYSICS_PAYLOAD: dict[str, Any] = {
    "id": "domain/test/demo/v1",
    "version": "1.0.0",
    "admin": {"name": "Test DA", "role": "admin", "pseudonymous_id": "da-001"},
    "invariants": [],
    "standing_orders": [],
    "escalation_triggers": [],
    "artifacts": [],
    "meta_authority_id": "ma-001",
}


class TestWriteFromTemplate:
    def test_writes_json(self, tmp_path: Path):
        target = tmp_path / "output" / "physics.json"
        result = write_from_template("domain-physics", _PHYSICS_PAYLOAD, target)
        assert result == target.resolve()
        assert target.exists()
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["id"] == "domain/test/demo/v1"
        # default_structure fields merged in
        assert "glossary" in data
        assert "subsystem_configs" in data

    def test_creates_parent_dirs(self, tmp_path: Path):
        target = tmp_path / "a" / "b" / "c" / "out.json"
        write_from_template("domain-physics", _PHYSICS_PAYLOAD, target)
        assert target.exists()

    def test_unknown_template_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Unknown template_id"):
            write_from_template("nonexistent", {}, tmp_path / "x.json")

    def test_missing_required_fields_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="missing required fields"):
            write_from_template("domain-physics", {"id": "x"}, tmp_path / "x.json")

    def test_atomic_no_partial_on_bad_path(self, tmp_path: Path):
        """If the target directory cannot be created, no temp file leaks."""
        # We can't easily simulate os.replace failure, but we verify
        # that a successful write doesn't leave temp files around.
        target = tmp_path / "clean" / "out.json"
        write_from_template("domain-physics", _PHYSICS_PAYLOAD, target)
        parent_files = list(target.parent.iterdir())
        assert len(parent_files) == 1  # only the target, no .tmp remnants

    def test_evidence_schema_template(self, tmp_path: Path):
        payload = {
            "schema_id": "lumina:evidence:test:v1",
            "version": "1.0.0",
            "domain_id": "domain/test/v1",
            "fields": {"score": {"type": "number"}},
        }
        target = tmp_path / "evidence.json"
        write_from_template("evidence-schema", payload, target)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["schema_id"] == "lumina:evidence:test:v1"

    def test_tool_adapter_template(self, tmp_path: Path):
        payload = {
            "id": "adapter/test/calc/v1",
            "version": "1.0.0",
            "tool_name": "Calculator",
            "description": "A calculator.",
            "domain_id": "domain/test/v1",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        }
        target = tmp_path / "adapter.yaml"
        write_from_template("tool-adapter", payload, target)
        content = target.read_text(encoding="utf-8")
        assert "Calculator" in content
        # Should have default authorization merged in
        assert "who_may_call" in content or "authorization" in content

    def test_context_hint_template(self, tmp_path: Path):
        payload = {
            "hint_id": "hint-001",
            "domain_id": "domain/test/v1",
            "content": "Common failure: negative numbers in sqrt.",
        }
        target = tmp_path / "hint.json"
        write_from_template("context-hint", payload, target)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["hint_id"] == "hint-001"
        assert data["source_task"] == "context_crawler"  # from default_structure

    def test_atomic_cleanup_when_replace_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        target = tmp_path / "cleanup" / "out.json"

        monkeypatch.setattr(_file_writer.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("replace failed")))

        with pytest.raises(OSError, match="replace failed"):
            write_from_template("domain-physics", _PHYSICS_PAYLOAD, target)

        tmp_files = list(target.parent.glob(".lumina_stage_*.tmp"))
        assert tmp_files == []

    def test_replace_failure_still_raises_when_unlink_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        target = tmp_path / "cleanup-unlink-fails" / "out.json"

        monkeypatch.setattr(_file_writer.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("replace failed")))
        monkeypatch.setattr(_file_writer.os, "unlink", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("unlink failed")))

        with pytest.raises(OSError, match="replace failed"):
            write_from_template("domain-physics", _PHYSICS_PAYLOAD, target)

        tmp_files = list(target.parent.glob(".lumina_stage_*.tmp"))
        assert len(tmp_files) == 1


class TestYamlFallback:
    def test_to_yaml_falls_back_to_json_when_yaml_is_missing(self, monkeypatch: pytest.MonkeyPatch):
        real_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("yaml unavailable")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)

        rendered = _file_writer._to_yaml({"alpha": 1, "nested": {"beta": True}})
        parsed = json.loads(rendered)
        assert parsed["alpha"] == 1
        assert parsed["nested"]["beta"] is True
