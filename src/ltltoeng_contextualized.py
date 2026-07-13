"""
Contextualized English translation for LTL formulas.

Inspired by the Wason selection task: people reason far better about logical
rules when framed in concrete, familiar terms rather than abstract symbols.

This module translates LTL formulas using a concrete "theme" — a mapping from
abstract proposition letters to real-world descriptions.  The default theme is
a panel of four colored lights (blue, amber, purple, cyan).  The color names
are chosen so that each literal is the color's first letter AND stays inside
the tutor's exercise-literal pool, which deliberately avoids letters that look
like LTL operators (r, g, f, u, x, w, m).

Public API
----------
    translate(node, theme=None) -> str
    remap_to_theme(node, theme=None) -> node or None
    THEMES: dict of built-in theme names -> Theme objects

All phrasing is strictly state-based ("the blue light is on"), never
event-based ("the blue light turns on"): a bare LTL literal holds in every
state where it is true, not only on a false->true transition, so edge
phrasing would describe a different formula than the one being asked.

Example:
    node = parse_ltl_string("G(b -> F a)")
    translate(node, theme=THEMES["lights"])
    # => "Whenever the blue light is on, then eventually the amber light is on."
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

    Phrases must be STATE descriptions ("the blue light is on"), never
    events ("the blue light turns on"): an LTL literal is true in every
    state where it holds, not only on a transition, so event phrasing
    would misstate when rules trigger.

    Attributes:
        name:        Human-readable theme name.
        description: One-line description of the scenario.
        literals:    Maps literal names to (positive_phrase, negative_phrase).
                     e.g. {"b": ("the blue light is on", "the blue light is off")}
    """
    name: str
    description: str
    literals: Dict[str, tuple[str, str]]  # lit -> (positive, negative)

    def positive(self, lit: str) -> str:
        if lit in self.literals:
            return self.literals[lit][0]
        return f"'{lit}'"

    def negative(self, lit: str) -> str:
        if lit in self.literals:
            return self.literals[lit][1]
        return f"'{lit}' does not hold"


# ---------------------------------------------------------------------------
# Built-in themes
# ---------------------------------------------------------------------------

THEMES: Dict[str, Theme] = {}

THEMES["lights"] = Theme(
    name="Light Panel",
    description="A panel with four colored lights: blue, amber, purple, and cyan.",
    literals={
        "b": ("the blue light is on",    "the blue light is off"),
        "a": ("the amber light is on",   "the amber light is off"),
        "p": ("the purple light is on",  "the purple light is off"),
        "c": ("the cyan light is on",    "the cyan light is off"),
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
                return f"once {theme.positive(lit)}, it stays that way forever"

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
            trigger = _t(left, theme)
            response = _t(right.operand, theme)
            return f"whenever {trigger}, then eventually {response}"

        # G(p -> X(F q)) — bounded response
        if isinstance(right, ltlnode.NextNode) and isinstance(right.operand, ltlnode.FinallyNode):
            trigger = _t(left, theme)
            response = _t(right.operand.operand, theme)
            return f"whenever {trigger}, starting from the very next step, eventually {response}"

        # G(p -> X q) — immediate response
        if isinstance(right, ltlnode.NextNode):
            trigger = _t(left, theme)
            response = _t(right.operand, theme)
            return f"whenever {trigger}, then {response} in the very next step"

        # G(p -> (q U r)) — chain precedence
        if isinstance(right, ltlnode.UntilNode):
            trigger = _t(left, theme)
            held = _t(right.left, theme)
            goal = _t(right.right, theme)
            return f"whenever {trigger}, it must remain the case that {held} until {goal}"

        # G(p -> (F q & F r)) — chain response
        if (isinstance(right, ltlnode.AndNode)
                and isinstance(right.left, ltlnode.FinallyNode)
                and isinstance(right.right, ltlnode.FinallyNode)):
            trigger = _t(left, theme)
            ra = _t(right.left.operand, theme)
            rb = _t(right.right.operand, theme)
            return f"whenever {trigger}, two things must eventually be true: {ra}, and {rb}"

        # G(p -> q) — generic
        trigger = _t(left, theme)
        consequence = _t(right, theme)
        return f"whenever {trigger}, it must be the case that {consequence}"

    # G(F p) — recurrence
    if isinstance(inner, ltlnode.FinallyNode):
        fi = inner.operand
        if isinstance(fi, ltlnode.AndNode):
            return f"it must keep being the case, over and over forever, that {_t(fi.left, theme)} and {_t(fi.right, theme)}"
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

        # F(G(p -> F q))
        if isinstance(gi, ltlnode.ImpliesNode) and isinstance(gi.right, ltlnode.FinallyNode):
            trigger = _t(gi.left, theme)
            response = _t(gi.right.operand, theme)
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
        trigger = _t(inner.left, theme)
        result = _t(inner.right.operand, theme)
        return f"eventually, once {trigger}, then {result} forever after"

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
        r = _t(r_node.operand, theme)
        return _join(
            f"it must stay the case that {l}",
            f"this continues until eventually {r}",
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
    return f"it must remain the case that {l} until {r}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(node: ltlnode.LTLNode, theme: Optional[Theme] = None) -> str:
    """Translate an LTL AST node into contextualized English.

    Args:
        node:  LTL formula AST node.
        theme: A Theme mapping literals to concrete descriptions.
               Defaults to the "lights" theme (blue/amber/purple/cyan).

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


def collect_literals(node: ltlnode.LTLNode) -> set:
    """Return the set of literal names appearing in *node*."""
    if isinstance(node, ltlnode.LiteralNode):
        return {node.value}
    if isinstance(node, ltlnode.UnaryOperatorNode):
        return collect_literals(node.operand)
    if isinstance(node, ltlnode.BinaryOperatorNode):
        return collect_literals(node.left) | collect_literals(node.right)
    return set()


def _rename_literals(node: ltlnode.LTLNode, mapping: Dict[str, str]) -> None:
    """Rename literals in *node* in place according to *mapping*."""
    if isinstance(node, ltlnode.LiteralNode):
        node.value = mapping.get(node.value, node.value)
    elif isinstance(node, ltlnode.UnaryOperatorNode):
        _rename_literals(node.operand, mapping)
    elif isinstance(node, ltlnode.BinaryOperatorNode):
        _rename_literals(node.left, mapping)
        _rename_literals(node.right, mapping)


def remap_to_theme(node: ltlnode.LTLNode, theme: Optional[Theme] = None) -> Optional[ltlnode.LTLNode]:
    """Rename *node*'s literals (in place) onto *theme*'s literals.

    This lets the same formula be posed either abstractly or contextualized,
    so an abstract-vs-contextualized comparison varies only the framing.

    Literals already named after a theme literal keep their name; the rest are
    assigned the remaining theme literals deterministically (sorted formula
    literals, theme declaration order).  Returns the node, or None if the
    formula has more distinct literals than the theme can name.
    """
    if theme is None:
        theme = THEMES["lights"]

    lits = collect_literals(node)
    if len(lits) > len(theme.literals):
        return None

    mapping = {lit: lit for lit in lits if lit in theme.literals}
    free_theme_lits = [t for t in theme.literals if t not in mapping.values()]
    unmapped = sorted(lit for lit in lits if lit not in mapping)
    mapping.update(zip(unmapped, free_theme_lits))

    _rename_literals(node, mapping)
    return node
