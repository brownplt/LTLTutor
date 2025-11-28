"""Utilities for producing cognitively-framed glosses of LTL formulae.

This module takes an LTL AST node and produces three English glosses that
highlight different cognitive frames:

1. Abstract / Logical (AL): operator-forward phrasing.
2. Deontic / Obligation (DO): emphasises guarantees the system must provide.
3. Narrative / Story (NS): event-focused narrative phrasing.

It also scores the glosses with a lightweight n-gram heuristic so callers can
pick the best-fitting gloss while keeping track of which frame was selected.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable

import ltlnode
import ltltoeng


class CognitiveFrame(Enum):
    ABSTRACT_LOGICAL = "AL"
    DEONTIC_OBLIGATION = "DO"
    NARRATIVE_STORY = "NS"


@dataclass
class GlossResult:
    """Result container for gloss generation."""

    best_gloss: str
    frame: CognitiveFrame
    frame_glosses: Dict[CognitiveFrame, str]


_FRAME_NGRAMS: Dict[CognitiveFrame, Iterable[str]] = {
    CognitiveFrame.ABSTRACT_LOGICAL: ("if", "implies", "always", "eventually", "until"),
    CognitiveFrame.DEONTIC_OBLIGATION: ("must", "should", "guarantee", "ensure", "oblig"),
    CognitiveFrame.NARRATIVE_STORY: ("over time", "story", "unfold", "event", "happen"),
}


def _normalize_sentence(text: str) -> str:
    """Clean a sentence and ensure it ends with punctuation."""

    cleaned = ltltoeng.correct_grammar(text.strip())
    if cleaned and cleaned[-1] not in {".", "!", "?"}:
        cleaned += "."
    return cleaned


def _normalize_base_gloss(node: ltlnode.LTLNode) -> str:
    """Obtain a base English gloss for an LTL node."""

    base = node.__to_english__()
    if base is None:
        return ""

    return _normalize_sentence(base)


def _gloss_do(node: ltlnode.LTLNode) -> str:
    """Recursively build a Deontic/Obligation gloss."""

    if isinstance(node, ltlnode.LiteralNode):
        return f"{node.value} holds in the current state"
    if isinstance(node, ltlnode.NotNode):
        return f"the system must ensure that not ({_gloss_do(node.operand)})"
    if isinstance(node, ltlnode.AndNode):
        return f"the system must satisfy both ({_gloss_do(node.left)}) and ({_gloss_do(node.right)})"
    if isinstance(node, ltlnode.OrNode):
        return f"the system must satisfy at least one of ({_gloss_do(node.left)}) or ({_gloss_do(node.right)})"
    if isinstance(node, ltlnode.ImpliesNode):
        return f"whenever ({_gloss_do(node.left)}) occurs, the system is obligated to ensure ({_gloss_do(node.right)})"
    if isinstance(node, ltlnode.GloballyNode):
        return f"the system must ensure at all times that ({_gloss_do(node.operand)}) holds"
    if isinstance(node, ltlnode.FinallyNode):
        return f"the system must eventually bring about ({_gloss_do(node.operand)})"
    if isinstance(node, ltlnode.NextNode):
        return f"on the next step, the system must enforce ({_gloss_do(node.operand)})"
    if isinstance(node, ltlnode.UntilNode):
        return f"the system must keep ({_gloss_do(node.left)}) true until it achieves ({_gloss_do(node.right)})"

    fallback = _normalize_base_gloss(node)
    return fallback.rstrip(".") if fallback else ""


def _gloss_ns(node: ltlnode.LTLNode) -> str:
    """Recursively build a Narrative/Event gloss."""

    if isinstance(node, ltlnode.LiteralNode):
        return f"{node.value} happens"
    if isinstance(node, ltlnode.NotNode):
        return f"it never happens that ({_gloss_ns(node.operand)})"
    if isinstance(node, ltlnode.AndNode):
        return f"({_gloss_ns(node.left)}) happens while ({_gloss_ns(node.right)}) also happens"
    if isinstance(node, ltlnode.OrNode):
        return f"either ({_gloss_ns(node.left)}) happens or ({_gloss_ns(node.right)}) happens"
    if isinstance(node, ltlnode.ImpliesNode):
        return f"whenever ({_gloss_ns(node.left)}) ever happens, ({_gloss_ns(node.right)}) must also happen"
    if isinstance(node, ltlnode.GloballyNode):
        return f"from now on, ({_gloss_ns(node.operand)}) always holds"
    if isinstance(node, ltlnode.FinallyNode):
        return f"sooner or later, ({_gloss_ns(node.operand)}) will happen"
    if isinstance(node, ltlnode.NextNode):
        return f"right after this, ({_gloss_ns(node.operand)}) happens"
    if isinstance(node, ltlnode.UntilNode):
        return f"({_gloss_ns(node.left)}) keeps happening until eventually ({_gloss_ns(node.right)}) happens"

    fallback = _normalize_base_gloss(node)
    return fallback.rstrip(".") if fallback else ""


def _build_frame_glosses(node: ltlnode.LTLNode, base_gloss: str) -> Dict[CognitiveFrame, str]:
    """Create three frame-specific glosses from a base gloss."""

    return {
        CognitiveFrame.ABSTRACT_LOGICAL: base_gloss,
        CognitiveFrame.DEONTIC_OBLIGATION: _normalize_sentence(_gloss_do(node)),
        CognitiveFrame.NARRATIVE_STORY: _normalize_sentence(_gloss_ns(node)),
    }


def _score_gloss(frame: CognitiveFrame, gloss: str) -> int:
    """Score a gloss using a lightweight frame-specific n-gram heuristic."""

    lowered = gloss.lower()
    return sum(lowered.count(ng) for ng in _FRAME_NGRAMS[frame])


def gloss_formula(node: ltlnode.LTLNode) -> GlossResult:
    """Generate and score glosses for an LTL formula.

    Args:
        node: Parsed LTL AST node.

    Returns:
        GlossResult containing the winning gloss, its frame, and all candidates.
    """

    base_gloss = _normalize_base_gloss(node)
    if base_gloss == "":
        return GlossResult(best_gloss="", frame=CognitiveFrame.ABSTRACT_LOGICAL, frame_glosses={})

    frame_glosses = _build_frame_glosses(node, base_gloss)

    best_frame = max(
        frame_glosses,
        key=lambda frame: (_score_gloss(frame, frame_glosses[frame]), frame.value),
    )

    return GlossResult(
        best_gloss=frame_glosses[best_frame],
        frame=best_frame,
        frame_glosses=frame_glosses,
    )
