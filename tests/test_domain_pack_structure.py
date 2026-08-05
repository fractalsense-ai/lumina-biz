"""Structural consistency tests for standardized domain pack layout."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PACKS = REPO_ROOT / "model-packs"
SYSTEM_PACK = DOMAIN_PACKS / "system"


def _discover_domain_packs() -> list[Path]:
    packs: list[Path] = []
    for pack_dir in sorted(DOMAIN_PACKS.iterdir()):
        if not pack_dir.is_dir():
            continue
        if (pack_dir / "pack.yaml").is_file():
            packs.append(pack_dir)
    return packs


ALL_PACKS = _discover_domain_packs()
PACK_IDS = [pack.name for pack in ALL_PACKS]


class TestReferenceDirectoryExists:
    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_reference_dir(self, pack: Path):
        assert (pack / "domain-lib" / "reference").is_dir()


class TestTurnInterpretationSpecExists:
    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_turn_interpretation_spec(self, pack: Path):
        spec = pack / "domain-lib" / "reference" / "turn-interpretation-spec-v1.md"
        assert spec.is_file(), f"Missing turn-interpretation-spec-v1.md in {pack.name}"


class TestSystemCommandInterpreterSpec:
    def test_command_interpreter_spec_exists(self):
        spec = SYSTEM_PACK / "domain-lib" / "reference" / "command-interpreter-spec-v1.md"
        assert spec.is_file()


class TestSensorsDirectory:
    def test_system_sensors(self):
        assert (SYSTEM_PACK / "domain-lib" / "sensors").is_dir()


class TestPromptsContainOnlyPersona:
    """prompts/ should contain only persona files, no interpretation specs."""

    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_no_turn_interpretation_in_prompts(self, pack: Path):
        prompts = pack / "prompts"
        if prompts.is_dir():
            assert not (prompts / "turn-interpretation.md").exists()

    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_no_command_translator_in_prompts(self, pack: Path):
        prompts = pack / "prompts"
        if prompts.is_dir():
            assert not (prompts / "command-translator.md").exists()

    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_persona_file_exists(self, pack: Path):
        persona = pack / "prompts" / "domain-persona-v1.md"
        assert persona.is_file(), f"Missing domain-persona-v1.md in {pack.name}"

    @pytest.mark.parametrize("pack", ALL_PACKS, ids=PACK_IDS)
    def test_no_old_persona_file(self, pack: Path):
        old = pack / "prompts" / "domain-system-override.md"
        assert not old.exists(), f"Old file domain-system-override.md still in {pack.name}"
