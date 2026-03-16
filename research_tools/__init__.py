"""Compatibility package exposing gait_research_platform/research_tools at the top level."""

from __future__ import annotations

from pathlib import Path


__path__ = [str(Path(__file__).resolve().parents[1] / "gait_research_platform" / "research_tools")]
