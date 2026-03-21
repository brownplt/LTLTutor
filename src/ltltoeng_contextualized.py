"""
Contextualized English translation for LTL formulas.

Inspired by the Wason selection task: people reason far better about logical
rules when framed in concrete, familiar terms rather than abstract symbols.

This module translates LTL formulas using a concrete "theme" — a mapping from
abstract proposition letters to real-world descriptions.  The default theme is
a 3-light panel (red, green, blue), but custom themes can be supplied.

Public API
----------
    translate(node, theme=None) -> str
    THEMES: dict of built-in theme names -> Theme objects

Example:
    node = parse_ltl_string("G(r -> F g)")
    translate(node, theme=THEMES["lights"])
    # => "Whenever the red light turns on, then eventually the green light is on."
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

import ltlnode


# ---------------------------------------------------------------------------
# Theme definition
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    """Maps abstract literals to concrete descriptions.

    Attributes:
        name:        Human-readable theme name.
        description: One-line description of the scenario.
        literals:    Maps literal names to (positive_phrase, negative_phrase).
                     e.g. {"p": ("the red light is on", "the red light is off")}
        event_form:  Maps literal names to an "event" phrasing for triggers.
                     e.g. {"p": ("the red light turns on", "the red light turns off")}
                     Falls back to the positive/negative phrase if not provided.
    """
    name: str
    description: str
    literals: Dict[str, tuple[str, str]]  # lit -> (positive, negative)
    event_form: Dict[str, tuple[str, str]] = field(default_factory=dict)  # lit -> (becomes_true, becomes_false)

    def positive(self, lit: str) -> str:
        if lit in self.literals:
            return self.literals[lit][0]
        return f"'{lit}'"

    def negative(self, lit: str) -> str:
        if lit in self.literals:
            return self.literals[lit][1]
        return f"'{lit}' does not hold"

    def event_on(self, lit: str) -> str:
        """Event phrasing for when the literal becomes true."""
        if lit in self.event_form:
            return self.event_form[lit][0]
        return self.positive(lit)

    def event_off(self, lit: str) -> str:
        """Event phrasing for when the literal becomes false."""
        if lit in self.event_form:
            return self.event_form[lit][1]
        return self.negative(lit)


# ---------------------------------------------------------------------------
# Built-in themes
# ---------------------------------------------------------------------------

THEMES: Dict[str, Theme] = {}

THEMES["lights"] = Theme(
    name="Light Panel",
    description="A panel with three colored lights: red, green, and blue.",
    literals={
        "r": ("the red light is on",    "the red light is off"),
        "g": ("the green light is on",  "the green light is off"),
        "b": ("the blue light is on",   "the blue light is off"),
    },
    event_form={
        "r": ("the red light turns on",    "the red light turns off"),
        "g": ("the green light turns on",  "the green light turns off"),
        "b": ("the blue light turns on",   "the blue light turns off"),
    },
)



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capitalize(text: str) -> str:
    if not text:
        return text
    text = " ".join(text.split())
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()


def _ensure_period(text: str) -> str:
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _join(*parts: str) -> str:
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        p = _capitalize(p)
        p = _ensure_period(p)
        out.append(p)
    return " ".join(out)


def _same_literal(a: ltlnode.LTLNode, b: ltlnode.LTLNode) -> bool:
    return (isinstance(a, ltlnode.LiteralNode) and
            isinstance(b, ltlnode.LiteralNode) and
            a.value == b.value)


def _count_next(node: ltlnode.LTLNode) -> tuple[int, ltlnode.LTLNode]:
    n = 0
    while isinstance(node, ltlnode.NextNode):
        n += 1
        node = node.operand
    return n, node


def _steps(n: int) -> str:
    if n == 1:
        return "the very next step"
    return f"{n} steps from now"


# ---------------------------------------------------------------------------
# Core translator
# ---------------------------------------------------------------------------

def _t(node: ltlnode.LTLNode, theme: Theme) -> str:
    """Recursively translate *node* using *theme*.

    Returns a sentence fragment (lowercase, no trailing period).
    """

    # --- Literal ---
    if isinstance(node, ltlnode.LiteralNode):
        return theme.positive(node.value)

    # --- Not ---
    if isinstance(node, ltlnode.NotNode):
        return _t_not(node, theme)

    # --- And ---
    if isinstance(node, ltlnode.AndNode):
        return _t_and(node, theme)

    # --- Or ---
    if isinstance(node, ltlnode.OrNode):
        return _t_or(node, theme)

    # --- Implies ---
    if isinstance(node, ltlnode.ImpliesNode):
        return _t_implies(node, theme)

    # --- Equivalence ---
    if isinstance(node, ltlnode.EquivalenceNode):
        return _t_equiv(node, theme)

    # --- Globally ---
    if isinstance(node, ltlnode.GloballyNode):
        return _t_globally(node, theme)

    # --- Finally ---
    if isinstance(node, ltlnode.FinallyNode):
        return _t_finally(node, theme)

    # --- Next ---
    if isinstance(node, ltlnode.NextNode):
        return _t_next(node, theme)

    # --- Until ---
    if isinstance(node, ltlnode.UntilNode):
        return _t_until(node, theme)

    return str(node)


# --- NOT ------------------------------------------------------------------

def _t_not(node: ltlnode.NotNode, theme: Theme) -> str:
    inner = node.operand

    if isinstance(inner, ltlnode.LiteralNode):
        return theme.negative(inner.value)

    # !(F p) -> never
    if isinstance(inner, ltlnode.FinallyNode) and isinstance(inner.operand, ltlnode.LiteralNode):
        return f"it is never the case that {theme.positive(inner.operand.value)}"

    # !!p
    if isinstance(inner, ltlnode.NotNode):
        return _t(inner.operand, theme)

    # !(p & q) -> not both
    if isinstance(inner, ltlnode.AndNode):
        return f"it is not the case that both {_t(inner.left, theme)} and {_t(inner.right, theme)}"

    # !(p | q) -> neither/nor
    if isinstance(inner, ltlnode.OrNode):
        return f"neither {_t(inner.left, theme)} nor {_t(inner.right, theme)}"

    # !(p -> q)
    if isinstance(inner, ltlnode.ImpliesNode):
        left_text = _t(inner.left, theme)
        if isinstance(inner.right, ltlnode.LiteralNode):
            right_text = theme.negative(inner.right.value)
        else:
            right_text = f"not {_t(inner.right, theme)}"
        return f"{left_text}, but {right_text}"

    return f"it is not the case that {_t(inner, theme)}"


# --- AND ------------------------------------------------------------------

def _t_and(node: ltlnode.AndNode, theme: Theme) -> str:
    # !p & !q -> neither/nor
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        ll = node.left.operand
        rr = node.right.operand
        if isinstance(ll, ltlnode.LiteralNode) and isinstance(rr, ltlnode.LiteralNode):
            return f"neither {_t(ll, theme)} nor {_t(rr, theme)}"
    return f"both {_t(node.left, theme)} and {_t(node.right, theme)}"


# --- OR -------------------------------------------------------------------

def _t_or(node: ltlnode.OrNode, theme: Theme) -> str:
    # !p | !q -> not both
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        ll = node.left.operand
        rr = node.right.operand
        if isinstance(ll, ltlnode.LiteralNode) and isinstance(rr, ltlnode.LiteralNode):
            return f"it cannot be the case that both {_t(ll, theme)} and {_t(rr, theme)}"
    return f"either {_t(node.left, theme)} or {_t(node.right, theme)}"


# --- IMPLIES --------------------------------------------------------------

def _t_implies(node: ltlnode.ImpliesNode, theme: Theme) -> str:
    # (p & q) -> r
    if isinstance(node.left, ltlnode.AndNode):
        r = _t(node.right, theme)
        return f"if both {_t(node.left.left, theme)} and {_t(node.left.right, theme)}, then {r}"

    # (p | q) -> r
    if isinstance(node.left, ltlnode.OrNode):
        r = _t(node.right, theme)
        return f"if either {_t(node.left.left, theme)} or {_t(node.left.right, theme)}, then {r}"

    return f"if {_t(node.left, theme)}, then {_t(node.right, theme)}"


# --- EQUIVALENCE ----------------------------------------------------------

def _t_equiv(node: ltlnode.EquivalenceNode, theme: Theme) -> str:
    return f"{_t(node.left, theme)} exactly when {_t(node.right, theme)}"


# --- GLOBALLY -------------------------------------------------------------

def _t_globally(node: ltlnode.GloballyNode, theme: Theme) -> str:
    inner = node.operand

    # G(!p) -> never
    if isinstance(inner, ltlnode.NotNode):
        negated = inner.operand
        if isinstance(negated, ltlnode.LiteralNode):
            return f"it is never the case that {theme.positive(negated.value)}"
        return f"at no point may it be the case that {_t(negated, theme)}"

    # G(p -> ...) patterns
    if isinstance(inner, ltlnode.ImpliesNode):
        left = inner.left
        right = inner.right

        # G(p -> X p) or G(p -> G p) — persistence
        if isinstance(right, (ltlnode.NextNode, ltlnode.GloballyNode)):
            if _same_literal(left, right.operand):
                lit = left.value
                return f"once {theme.event_on(lit)}, it stays that way forever"

        # G(p -> F q) — response
        if isinstance(right, ltlnode.FinallyNode):
            if isinstance(left, ltlnode.UntilNode):
                p = _t(left.left, theme)
                q = _t(left.right, theme)
                r = _t(right.operand, theme)
                return _join(
                    f"suppose {p} continues until {q}",
                    f"then eventually, {r}",
                    "this rule applies every time",
                )
            trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
            response = theme.positive(right.operand.value) if isinstance(right.operand, ltlnode.LiteralNode) else _t(right.operand, theme)
            return f"whenever {trigger}, then eventually {response}"

        # G(p -> X(F q)) — bounded response
        if isinstance(right, ltlnode.NextNode) and isinstance(right.operand, ltlnode.FinallyNode):
            trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
            response = theme.positive(right.operand.operand.value) if isinstance(right.operand.operand, ltlnode.LiteralNode) else _t(right.operand.operand, theme)
            return f"whenever {trigger}, starting from the very next step, eventually {response}"

        # G(p -> X q) — immediate response
        if isinstance(right, ltlnode.NextNode):
            trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
            response = _t(right.operand, theme)
            return f"whenever {trigger}, then {response} in the very next step"

        # G(p -> (q U r)) — chain precedence
        if isinstance(right, ltlnode.UntilNode):
            trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
            held = _t(right.left, theme)
            goal = _t(right.right, theme)
            return f"whenever {trigger}, it must remain the case that {held} until {goal}"

        # G(p -> (F q & F r)) — chain response
        if (isinstance(right, ltlnode.AndNode)
                and isinstance(right.left, ltlnode.FinallyNode)
                and isinstance(right.right, ltlnode.FinallyNode)):
            trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
            ra = theme.event_on(right.left.operand.value) if isinstance(right.left.operand, ltlnode.LiteralNode) else _t(right.left.operand, theme)
            rb = theme.event_on(right.right.operand.value) if isinstance(right.right.operand, ltlnode.LiteralNode) else _t(right.right.operand, theme)
            return f"whenever {trigger}, two things must eventually happen: {ra}, and {rb}"

        # G(p -> q) — generic
        trigger = theme.event_on(left.value) if isinstance(left, ltlnode.LiteralNode) else _t(left, theme)
        consequence = _t(right, theme)
        return f"whenever {trigger}, it must be the case that {consequence}"

    # G(F p) — recurrence
    if isinstance(inner, ltlnode.FinallyNode):
        fi = inner.operand
        if isinstance(fi, ltlnode.AndNode):
            return f"it must keep being the case, over and over forever, that {_t(fi.left, theme)} and {_t(fi.right, theme)}"
        if isinstance(fi, ltlnode.LiteralNode):
            return f"{theme.event_on(fi.value)} must keep happening over and over, forever"
        target = _t(fi, theme)
        return f"it must keep being the case, over and over forever, that {target}"

    # G(G(...)) — idempotent
    if isinstance(inner, ltlnode.GloballyNode):
        return _t_globally(inner, theme)

    # G(p & q) / G(p | q)
    if isinstance(inner, ltlnode.AndNode):
        return f"at every moment, {_t(inner.left, theme)} and {_t(inner.right, theme)}"
    if isinstance(inner, ltlnode.OrNode):
        return f"at every moment, either {_t(inner.left, theme)} or {_t(inner.right, theme)}"

    # G(literal)
    if isinstance(inner, ltlnode.LiteralNode):
        return f"{theme.positive(inner.value)} at all times"
    return f"at all times, {_t(inner, theme)}"


# --- FINALLY --------------------------------------------------------------

def _t_finally(node: ltlnode.FinallyNode, theme: Theme) -> str:
    inner = node.operand

    # F(F(...)) — idempotent
    if isinstance(inner, ltlnode.FinallyNode):
        return _t_finally(inner, theme)

    # F(G(...)) patterns
    if isinstance(inner, ltlnode.GloballyNode):
        gi = inner.operand

        # F(G(!p))
        if isinstance(gi, ltlnode.NotNode) and isinstance(gi.operand, ltlnode.LiteralNode):
            return _join(
                f"eventually, {theme.event_off(gi.operand.value)}",
                f"and from that point on, {theme.event_on(gi.operand.value)} never happens again",
            )

        # F(G(p -> F q))
        if isinstance(gi, ltlnode.ImpliesNode) and isinstance(gi.right, ltlnode.FinallyNode):
            trigger = theme.event_on(gi.left.value) if isinstance(gi.left, ltlnode.LiteralNode) else _t(gi.left, theme)
            response = theme.positive(gi.right.operand.value) if isinstance(gi.right.operand, ltlnode.LiteralNode) else _t(gi.right.operand, theme)
            return _join(
                "eventually, the system stabilizes",
                f"from that point on, whenever {trigger}, then eventually {response}",
            )

        # F(G(p & q))
        if isinstance(gi, ltlnode.AndNode):
            return f"eventually, {_t(gi.left, theme)} and {_t(gi.right, theme)}, and they stay that way forever"

        # F(G p) — generic persistence
        target = _t(gi, theme)
        return f"eventually, {target}, and it stays that way forever"

    # F(!p)
    if isinstance(inner, ltlnode.NotNode) and isinstance(inner.operand, ltlnode.LiteralNode):
        return f"eventually, {theme.event_off(inner.operand.value)}"

    # F(p & G q) / F(G q & p) — persistence after trigger
    if isinstance(inner, ltlnode.AndNode):
        l, r = inner.left, inner.right
        if isinstance(r, ltlnode.GloballyNode):
            trigger = _t(l, theme)
            persist = _t(r.operand, theme)
            return _join(f"eventually, {trigger}", f"from that point on, {persist} forever")
        if isinstance(l, ltlnode.GloballyNode):
            trigger = _t(r, theme)
            persist = _t(l.operand, theme)
            return _join(f"eventually, {trigger}", f"from that point on, {persist} forever")
        return f"eventually, {_t(l, theme)} and {_t(r, theme)} at the same time"

    # F(p -> G q) — trigger to permanence
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.GloballyNode):
        trigger = theme.event_on(inner.left.value) if isinstance(inner.left, ltlnode.LiteralNode) else _t(inner.left, theme)
        result = _t(inner.right.operand, theme)
        return f"eventually, once {trigger}, then {result} forever after"

    # F(literal)
    if isinstance(inner, ltlnode.LiteralNode):
        return f"eventually, {theme.event_on(inner.value)}"

    return f"eventually, {_t(inner, theme)}"


# --- NEXT -----------------------------------------------------------------

def _t_next(node: ltlnode.NextNode, theme: Theme) -> str:
    steps, core = _count_next(node)

    if steps == 1 and isinstance(core, ltlnode.UntilNode):
        l = _t(core.left, theme)
        r = _t(core.right, theme)
        return f"starting from the next step, {l} until {r}"

    if steps == 1 and isinstance(core, ltlnode.FinallyNode):
        target = _t(core.operand, theme)
        return f"starting from the next step, {target} must eventually happen"

    target = _t(core, theme)
    return f"in {_steps(steps)}, {target}"


# --- UNTIL ----------------------------------------------------------------

def _t_until(node: ltlnode.UntilNode, theme: Theme) -> str:
    l_node, r_node = node.left, node.right

    # (G p) U (F q)
    if isinstance(l_node, ltlnode.GloballyNode) and isinstance(r_node, ltlnode.FinallyNode):
        l = _t(l_node.operand, theme)
        r_event = theme.event_on(r_node.operand.value) if isinstance(r_node.operand, ltlnode.LiteralNode) else _t(r_node.operand, theme)
        return _join(
            f"it must stay the case that {l}",
            f"this continues until eventually {r_event}",
        )

    # (p U q) U r
    if isinstance(l_node, ltlnode.UntilNode):
        p = _t(l_node.left, theme)
        q = _t(l_node.right, theme)
        r = _t(r_node, theme)
        return _join(
            f"first, {p} continues until {q}",
            f"that whole phase lasts until {r}",
        )

    l = _t(l_node, theme)
    r = _t(r_node, theme)
    return f"{l} must continue until {r}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(node: ltlnode.LTLNode, theme: Optional[Theme] = None) -> str:
    """Translate an LTL AST node into contextualized English.

    Args:
        node:  LTL formula AST node.
        theme: A Theme mapping literals to concrete descriptions.
               Defaults to the "lights" theme (red/green/blue lights).

    Returns:
        A capitalized, period-terminated English paragraph.
    """
    if theme is None:
        theme = THEMES["lights"]

    raw = _t(node, theme)
    raw = raw.strip()
    result = _capitalize(raw)
    if result and result[-1] not in ".!?":
        result += "."
    return result
