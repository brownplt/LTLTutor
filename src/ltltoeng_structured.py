"""Structured, hierarchical English translation for LTL formulas.

Instead of forcing every LTL formula into a single flat sentence (as ltltoeng
does), this module produces indented, bullet-point explanations that reveal the
structure of the formula.  Simple formulas still get a single line; complex ones
are broken into labeled components (Condition, Response, Requirement, Rule).

Public API
----------
translate(node) -> str
    Given an LTLNode AST, return a human-readable English string.
    For simple formulas the result is a single line.
    For complex formulas the result is a multi-line, indented explanation.
"""

from __future__ import annotations

import ltlnode


# ---------------------------------------------------------------------------
# Complexity metric
# ---------------------------------------------------------------------------

def _temporal_depth(node: ltlnode.LTLNode) -> int:
    """Return the nesting depth of temporal operators in *node*.

    Temporal operators are G, F, X, and U.  Propositional connectives (&, |,
    ->, <->, !) do *not* increase temporal depth -- they only propagate the
    maximum depth of their children.

    A bare literal has depth 0.
    """
    if isinstance(node, ltlnode.LiteralNode):
        return 0

    if isinstance(node, (ltlnode.GloballyNode, ltlnode.FinallyNode,
                         ltlnode.NextNode)):
        return 1 + _temporal_depth(node.operand)

    if isinstance(node, ltlnode.UntilNode):
        return 1 + max(_temporal_depth(node.left), _temporal_depth(node.right))

    # Propositional connectives: Not, And, Or, Implies, Equivalence
    if isinstance(node, ltlnode.NotNode):
        return _temporal_depth(node.operand)

    if isinstance(node, (ltlnode.AndNode, ltlnode.OrNode,
                         ltlnode.ImpliesNode, ltlnode.EquivalenceNode)):
        return max(_temporal_depth(node.left), _temporal_depth(node.right))

    # Fallback for unknown node types
    return 0


# The threshold at which we switch from single-line to structured output.
_COMPLEXITY_THRESHOLD = 2


def _is_simple(node: ltlnode.LTLNode) -> bool:
    """True when *node* is simple enough for a single-line translation."""
    return _temporal_depth(node) < _COMPLEXITY_THRESHOLD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_INDENT = "  "


def _indent(text: str, level: int) -> str:
    """Indent every line of *text* by *level* levels."""
    prefix = _INDENT * level
    return "\n".join(prefix + line for line in text.splitlines())


def _bullet(text: str, level: int) -> str:
    """Return *text* as a bulleted line at the given indentation level."""
    prefix = _INDENT * level
    return f"{prefix}- {text}"


def _quote(node: ltlnode.LTLNode) -> str:
    """Quote a literal node's value.  Non-literals get their LTL string."""
    if isinstance(node, ltlnode.LiteralNode):
        return f"'{node.value}'"
    return str(node)


def _count_next_chain(node: ltlnode.LTLNode):
    """Count consecutive X (Next) wrappers.  Returns (count, inner_node)."""
    n = 0
    while isinstance(node, ltlnode.NextNode):
        n += 1
        node = node.operand
    return n, node


def _steps_phrase(count: int) -> str:
    """Human-readable phrase like '3 steps from now'."""
    if count == 1:
        return "the next step"
    return f"{count} steps from now"


# ---------------------------------------------------------------------------
# Single-line (flat) translator  -- used for simple sub-formulas
# ---------------------------------------------------------------------------

def _flat(node: ltlnode.LTLNode) -> str:
    """Produce a concise, single-line English translation of *node*.

    This is deliberately kept simple and deterministic (no randomised
    alternatives) so that structured output is reproducible in tests.
    """
    if isinstance(node, ltlnode.LiteralNode):
        return f"'{node.value}'"

    # -- unary temporal --
    if isinstance(node, ltlnode.GloballyNode):
        inner = node.operand
        # G(!p) -> never pattern
        if isinstance(inner, ltlnode.NotNode):
            if isinstance(inner.operand, ltlnode.LiteralNode):
                return f"'{inner.operand.value}' must never hold"
            return f"it is never the case that {_flat(inner.operand)}"
        return f"at all times, {_flat(inner)}"

    if isinstance(node, ltlnode.FinallyNode):
        return f"eventually, {_flat(node.operand)}"

    if isinstance(node, ltlnode.NextNode):
        steps, inner = _count_next_chain(node)
        if steps == 1:
            return f"in the next step, {_flat(inner)}"
        return f"{steps} steps from now, {_flat(inner)}"

    # -- binary temporal --
    if isinstance(node, ltlnode.UntilNode):
        return f"{_flat(node.left)} until {_flat(node.right)}"

    # -- propositional --
    if isinstance(node, ltlnode.NotNode):
        inner = node.operand
        if isinstance(inner, ltlnode.LiteralNode):
            return f"not '{inner.value}'"
        # !(F p) -> never
        if isinstance(inner, ltlnode.FinallyNode):
            return f"{_flat(inner.operand)} never occurs"
        # !!p -> double negation elimination
        if isinstance(inner, ltlnode.NotNode):
            return _flat(inner.operand)
        # !(p & q) -> not both
        if isinstance(inner, ltlnode.AndNode):
            return f"not both {_flat(inner.left)} and {_flat(inner.right)}"
        # !(p | q) -> neither/nor
        if isinstance(inner, ltlnode.OrNode):
            return f"neither {_flat(inner.left)} nor {_flat(inner.right)}"
        # !(p -> q) -> p but not q
        if isinstance(inner, ltlnode.ImpliesNode):
            return f"{_flat(inner.left)}, but not {_flat(inner.right)}"
        return f"it is not the case that {_flat(inner)}"

    if isinstance(node, ltlnode.AndNode):
        # !p & !q -> neither/nor
        if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
            return f"neither {_flat(node.left.operand)} nor {_flat(node.right.operand)}"
        return f"{_flat(node.left)} and {_flat(node.right)}"

    if isinstance(node, ltlnode.OrNode):
        # !p | !q -> not both
        if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
            return f"not both {_flat(node.left.operand)} and {_flat(node.right.operand)}"
        return f"{_flat(node.left)} or {_flat(node.right)}"

    if isinstance(node, ltlnode.ImpliesNode):
        return f"if {_flat(node.left)}, then {_flat(node.right)}"

    if isinstance(node, ltlnode.EquivalenceNode):
        return f"{_flat(node.left)} if and only if {_flat(node.right)}"

    # Fallback
    return str(node)


# ---------------------------------------------------------------------------
# Structured (hierarchical) translator
# ---------------------------------------------------------------------------

def _structured(node: ltlnode.LTLNode, depth: int = 0) -> str:
    """Recursively produce a structured, multi-line translation.

    *depth* tracks the current bullet indentation level.
    When a sub-formula is simple enough it collapses to a single line via
    ``_flat``.
    """

    # ---- Leaf / simple sub-trees -> flat ----
    if _is_simple(node):
        return _flat(node)

    # ---- G(...) ----
    if isinstance(node, ltlnode.GloballyNode):
        inner = node.operand
        return _translate_globally(inner, depth)

    # ---- F(...) ----
    if isinstance(node, ltlnode.FinallyNode):
        inner = node.operand
        return _translate_finally(inner, depth)

    # ---- X(...) ----
    if isinstance(node, ltlnode.NextNode):
        steps, inner = _count_next_chain(node)
        return _translate_next(steps, inner, depth)

    # ---- p U q ----
    if isinstance(node, ltlnode.UntilNode):
        return _translate_until(node, depth)

    # ---- p -> q ----
    if isinstance(node, ltlnode.ImpliesNode):
        return _translate_implies(node, depth)

    # ---- p <-> q ----
    if isinstance(node, ltlnode.EquivalenceNode):
        return _translate_equivalence(node, depth)

    # ---- p & q ----
    if isinstance(node, ltlnode.AndNode):
        return _translate_and(node, depth)

    # ---- p | q ----
    if isinstance(node, ltlnode.OrNode):
        return _translate_or(node, depth)

    # ---- !p ----
    if isinstance(node, ltlnode.NotNode):
        return _translate_not(node, depth)

    return _flat(node)


# ---- Globally ----

def _translate_globally(inner: ltlnode.LTLNode, depth: int) -> str:
    # G(p -> F q)  -- response pattern
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.FinallyNode):
        trigger = inner.left
        response = inner.right.operand
        if _is_simple(trigger) and _is_simple(response):
            return f"Whenever {_flat(trigger)} holds, {_flat(response)} must eventually follow."
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"When {_flat(trigger)} occurs:", depth + 1))
        lines.append(_bullet(f"{_flat(response)} must eventually occur", depth + 2))
        return "\n".join(lines)

    # G(p -> X(F q))  -- bounded response
    if (isinstance(inner, ltlnode.ImpliesNode)
            and isinstance(inner.right, ltlnode.NextNode)
            and isinstance(inner.right.operand, ltlnode.FinallyNode)):
        trigger = inner.left
        response = inner.right.operand.operand
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"When {_flat(trigger)} occurs:", depth + 1))
        lines.append(_bullet(f"Starting from the next step, {_flat(response)} must eventually occur", depth + 2))
        return "\n".join(lines)

    # G(p -> X q)  -- immediate next-step response
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.NextNode):
        trigger = inner.left
        response = inner.right.operand
        if _is_simple(trigger) and _is_simple(response):
            return f"At all times, when {_flat(trigger)} holds, {_flat(response)} must hold in the next step."
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"When {_flat(trigger)} occurs:", depth + 1))
        lines.append(_bullet(f"{_flat(response)} must hold in the next step", depth + 2))
        return "\n".join(lines)

    # G(p -> (q U r))  -- chain precedence
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.UntilNode):
        trigger = inner.left
        held = inner.right.left
        goal = inner.right.right
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"When {_flat(trigger)} occurs:", depth + 1))
        lines.append(_bullet(f"{_flat(held)} must hold until {_flat(goal)} occurs", depth + 2))
        return "\n".join(lines)

    # G(p -> (F q & F r))  -- chain response (conjunction of eventually)
    if (isinstance(inner, ltlnode.ImpliesNode)
            and isinstance(inner.right, ltlnode.AndNode)
            and isinstance(inner.right.left, ltlnode.FinallyNode)
            and isinstance(inner.right.right, ltlnode.FinallyNode)):
        trigger = inner.left
        resp_a = inner.right.left.operand
        resp_b = inner.right.right.operand
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"When {_flat(trigger)} occurs, two responses are required:", depth + 1))
        lines.append(_bullet(f"{_flat(resp_a)} must eventually occur", depth + 2))
        lines.append(_bullet(f"{_flat(resp_b)} must eventually occur", depth + 2))
        return "\n".join(lines)

    # G(p -> q)  -- generic implication under G
    if isinstance(inner, ltlnode.ImpliesNode):
        trigger = inner.left
        consequence = inner.right
        if _is_simple(trigger) and _is_simple(consequence):
            return f"At all times, if {_flat(trigger)}, then {_flat(consequence)}."
        lines = ["At all times, the following rule holds:"]
        lines.append(_bullet(f"Condition: {_structured(trigger, depth + 1)}", depth + 1))
        lines.append(_bullet(f"Response: {_structured(consequence, depth + 1)}", depth + 1))
        return "\n".join(lines)

    # G(F p)  -- recurrence / infinitely often
    if isinstance(inner, ltlnode.FinallyNode):
        return f"{_flat(inner.operand)} must occur infinitely often."

    # G(!p)  -- never
    if isinstance(inner, ltlnode.NotNode):
        negated = inner.operand
        if isinstance(negated, ltlnode.LiteralNode):
            return f"'{negated.value}' must never hold."
        return f"It is never the case that {_flat(negated)}."

    # G(p & q) -- invariant conjunction
    if isinstance(inner, ltlnode.AndNode):
        lines = ["At all times, the following must hold simultaneously:"]
        lines.append(_bullet(_structured(inner.left, depth + 1), depth + 1))
        lines.append(_bullet(_structured(inner.right, depth + 1), depth + 1))
        return "\n".join(lines)

    # G(p | q) -- invariant disjunction
    if isinstance(inner, ltlnode.OrNode):
        lines = ["At all times, at least one of the following must hold:"]
        lines.append(_bullet(_structured(inner.left, depth + 1), depth + 1))
        lines.append(_bullet(_structured(inner.right, depth + 1), depth + 1))
        return "\n".join(lines)

    # Generic G(...)
    inner_text = _structured(inner, depth + 1)
    if "\n" in inner_text:
        lines = ["At all times, the following holds:"]
        for line in inner_text.splitlines():
            lines.append(_bullet(line.lstrip(), depth + 1))
        return "\n".join(lines)
    return f"At all times, {inner_text}."


# ---- Finally ----

def _translate_finally(inner: ltlnode.LTLNode, depth: int) -> str:
    # F(G(p -> F q))  -- eventual permanent rule
    if (isinstance(inner, ltlnode.GloballyNode)
            and isinstance(inner.operand, ltlnode.ImpliesNode)
            and isinstance(inner.operand.right, ltlnode.FinallyNode)):
        trigger = inner.operand.left
        response = inner.operand.right.operand
        lines = ["Eventually, a permanent rule takes effect:"]
        lines.append(_bullet(
            f"From that point on, whenever {_flat(trigger)} holds, "
            f"{_flat(response)} must eventually follow.",
            depth + 1))
        return "\n".join(lines)

    # F(G p)  -- persistence / stability
    if isinstance(inner, ltlnode.GloballyNode):
        g_inner = inner.operand
        if _is_simple(g_inner):
            return f"Eventually, {_flat(g_inner)} becomes permanently true."
        lines = ["Eventually, a permanent state is reached:"]
        for sub in _structured(g_inner, depth + 1).splitlines():
            lines.append(_bullet(sub.lstrip(), depth + 1))
        return "\n".join(lines)

    # F(!p)
    if isinstance(inner, ltlnode.NotNode) and isinstance(inner.operand, ltlnode.LiteralNode):
        return f"Eventually, '{inner.operand.value}' will cease to hold."

    # F(p & q)
    if isinstance(inner, ltlnode.AndNode):
        lines = ["Eventually, the following will all be true simultaneously:"]
        lines.append(_bullet(_structured(inner.left, depth + 1), depth + 1))
        lines.append(_bullet(_structured(inner.right, depth + 1), depth + 1))
        return "\n".join(lines)

    # Generic F(...)
    inner_text = _structured(inner, depth + 1)
    if "\n" in inner_text:
        lines = ["Eventually, the following will hold:"]
        for line in inner_text.splitlines():
            lines.append(_bullet(line.lstrip(), depth + 1))
        return "\n".join(lines)
    return f"Eventually, {inner_text}."


# ---- Next ----

def _translate_next(steps: int, inner: ltlnode.LTLNode, depth: int) -> str:
    timing = _steps_phrase(steps)

    # X(F q) or XX...(F q)
    if isinstance(inner, ltlnode.FinallyNode):
        resp = inner.operand
        return f"Starting from {timing}, {_flat(resp)} must eventually occur."

    inner_text = _structured(inner, depth + 1)
    if "\n" in inner_text:
        lines = [f"In {timing}:"]
        for line in inner_text.splitlines():
            lines.append(_bullet(line.lstrip(), depth + 1))
        return "\n".join(lines)
    return f"In {timing}, {inner_text}."


# ---- Until ----

def _translate_until(node: ltlnode.UntilNode, depth: int) -> str:
    left = node.left
    right = node.right

    # (G p) U (F q)
    if isinstance(left, ltlnode.GloballyNode) and isinstance(right, ltlnode.FinallyNode):
        l_eng = _flat(left.operand)
        r_eng = _flat(right.operand)
        lines = [f"{l_eng} must hold at all times."]
        lines.append(f"This requirement continues until {r_eng} eventually occurs.")
        return "\n".join(lines)

    # (p U q) where both sides are simple
    if _is_simple(left) and _is_simple(right):
        return f"{_flat(left)} holds until {_flat(right)} occurs"

    lines = ["The following 'until' relationship holds:"]
    lines.append(_bullet(f"Maintained: {_structured(left, depth + 1)}", depth + 1))
    lines.append(_bullet(f"Until: {_structured(right, depth + 1)}", depth + 1))
    return "\n".join(lines)


# ---- Implies ----

def _translate_implies(node: ltlnode.ImpliesNode, depth: int) -> str:
    left = node.left
    right = node.right

    # X^n p -> X^m q  -- aligned next chains
    left_steps, left_core = _count_next_chain(left)
    right_steps, right_core = _count_next_chain(right)
    if left_steps >= 1 and right_steps >= 1:
        lines = [f"If {_flat(left_core)} holds in {_steps_phrase(left_steps)}, then:"]
        lines.append(_bullet(
            f"{_flat(right_core)} must hold {_steps_phrase(right_steps)}",
            depth + 1))
        return "\n".join(lines)

    if _is_simple(left) and _is_simple(right):
        return f"If {_flat(left)}, then {_flat(right)}."

    cond_text = _structured(left, depth + 1)
    resp_text = _structured(right, depth + 1)

    lines = []
    if "\n" in cond_text:
        lines.append("If the following condition holds:")
        for l in cond_text.splitlines():
            lines.append(_bullet(l.lstrip(), depth + 1))
    else:
        lines.append(f"If {cond_text}, then:")

    if "\n" in resp_text:
        for l in resp_text.splitlines():
            lines.append(_bullet(l.lstrip(), depth + 1))
    else:
        lines.append(_bullet(resp_text, depth + 1))

    return "\n".join(lines)


# ---- Equivalence ----

def _translate_equivalence(node: ltlnode.EquivalenceNode, depth: int) -> str:
    left = node.left
    right = node.right

    if _is_simple(left) and _is_simple(right):
        return f"{_flat(left)} if and only if {_flat(right)}."

    lines = ["The following two statements are equivalent:"]
    lines.append(_bullet(f"Statement A: {_structured(left, depth + 1)}", depth + 1))
    lines.append(_bullet(f"Statement B: {_structured(right, depth + 1)}", depth + 1))
    return "\n".join(lines)


# ---- And ----

def _translate_and(node: ltlnode.AndNode, depth: int) -> str:
    left = node.left
    right = node.right

    if _is_simple(left) and _is_simple(right):
        return f"{_flat(left)} and {_flat(right)}"

    lines = ["All of the following must hold:"]
    lines.append(_bullet(_structured(left, depth + 1), depth + 1))
    lines.append(_bullet(_structured(right, depth + 1), depth + 1))
    return "\n".join(lines)


# ---- Or ----

def _translate_or(node: ltlnode.OrNode, depth: int) -> str:
    left = node.left
    right = node.right

    if _is_simple(left) and _is_simple(right):
        return f"{_flat(left)} or {_flat(right)}"

    lines = ["At least one of the following must hold:"]
    lines.append(_bullet(_structured(left, depth + 1), depth + 1))
    lines.append(_bullet(_structured(right, depth + 1), depth + 1))
    return "\n".join(lines)


# ---- Not ----

def _translate_not(node: ltlnode.NotNode, depth: int) -> str:
    inner = node.operand

    if isinstance(inner, ltlnode.LiteralNode):
        return f"not '{inner.value}'"

    inner_text = _structured(inner, depth + 1)
    if "\n" in inner_text:
        lines = ["It is NOT the case that:"]
        for line in inner_text.splitlines():
            lines.append(_bullet(line.lstrip(), depth + 1))
        return "\n".join(lines)
    return f"It is not the case that {inner_text}."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(node: ltlnode.LTLNode) -> str:
    """Translate an LTL AST node into structured English.

    Simple formulas (temporal depth < 2) produce a single line.
    Complex formulas produce indented, bullet-point explanations.
    """
    return _structured(node, depth=0)
