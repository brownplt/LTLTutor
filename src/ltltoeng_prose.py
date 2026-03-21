"""
Clause-chaining prose translator for LTL formulas.

Produces flowing, natural prose that reads like a paragraph from a
requirements document.  A single LTL formula may become multiple short
sentences connected by discourse connectives ("After that point, ...",
"Suppose that ...", "This applies every time ...").

Public API
----------
    translate(node) -> str

``node`` is any ``ltlnode.LTLNode`` produced by ``parse_ltl_string``.
"""

from __future__ import annotations

import ltlnode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lit(node: ltlnode.LTLNode) -> str:
    """Return the quoted literal value, e.g. ``'p'``."""
    if isinstance(node, ltlnode.LiteralNode):
        return f"'{node.value}'"
    # Fallback: translate the subtree inline.
    return _inner(node, _Ctx())


def _is_lit(node: ltlnode.LTLNode) -> bool:
    return isinstance(node, ltlnode.LiteralNode)


def _same_literal(a: ltlnode.LTLNode, b: ltlnode.LTLNode) -> bool:
    """True when *a* and *b* are LiteralNodes with identical value."""
    return (_is_lit(a) and _is_lit(b) and a.value == b.value)


def _capitalize(text: str) -> str:
    """Capitalize the first letter, but leave quoted literals alone."""
    if not text:
        return text
    text = " ".join(text.split())  # collapse whitespace
    if text[0] == "'":
        return text
    return text[0].upper() + text[1:]


def _ensure_period(text: str) -> str:
    """Ensure *text* ends with exactly one period."""
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _join_sentences(*parts: str) -> str:
    """Join sentence fragments, capitalizing and adding periods."""
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        p = _capitalize(p)
        p = _ensure_period(p)
        out.append(p)
    return " ".join(out)


# ---------------------------------------------------------------------------
# Translation context
# ---------------------------------------------------------------------------

class _Ctx:
    """Tracks the temporal frame the translator is currently inside.

    *frame* is one of:
        ``"top"``      -- outermost level, no enclosing temporal operator
        ``"globally"`` -- inside a G(...)
        ``"finally"``  -- inside an F(...)
        ``"next"``     -- inside an X(...)
        ``"until"``    -- inside a U(...)
    """

    __slots__ = ("frame", "inline")

    def __init__(self, frame: str = "top", inline: bool = False):
        self.frame = frame
        # When *inline* is True the caller wants a short fragment that can be
        # embedded inside another sentence (no leading capital, no trailing
        # period, no discourse connectives).
        self.inline = inline

    def child(self, frame: str | None = None, *, inline: bool | None = None) -> "_Ctx":
        return _Ctx(
            frame=frame if frame is not None else self.frame,
            inline=inline if inline is not None else self.inline,
        )


# ---------------------------------------------------------------------------
# Complexity heuristic
# ---------------------------------------------------------------------------

def _depth(node: ltlnode.LTLNode) -> int:
    """Return the AST depth (leaves = 0)."""
    if _is_lit(node):
        return 0
    if isinstance(node, ltlnode.UnaryOperatorNode):
        return 1 + _depth(node.operand)
    if isinstance(node, ltlnode.BinaryOperatorNode):
        return 1 + max(_depth(node.left), _depth(node.right))
    return 0


def _is_simple(node: ltlnode.LTLNode) -> bool:
    """True for nodes simple enough to translate as one inline clause."""
    return _depth(node) <= 1


# ---------------------------------------------------------------------------
# Core recursive translator
# ---------------------------------------------------------------------------

def _inner(node: ltlnode.LTLNode, ctx: _Ctx) -> str:
    """Recursively translate *node* in the given context.

    Returns a **sentence fragment** (lowercase start, no trailing period)
    unless the node is complex enough to warrant its own sentence(s), in
    which case it returns already-joined prose.
    """

    # --- Literal -----------------------------------------------------------
    if isinstance(node, ltlnode.LiteralNode):
        return f"'{node.value}'"

    # --- Not ---------------------------------------------------------------
    if isinstance(node, ltlnode.NotNode):
        return _translate_not(node, ctx)

    # --- And / Or ----------------------------------------------------------
    if isinstance(node, ltlnode.AndNode):
        return _translate_and(node, ctx)
    if isinstance(node, ltlnode.OrNode):
        return _translate_or(node, ctx)

    # --- Implies -----------------------------------------------------------
    if isinstance(node, ltlnode.ImpliesNode):
        return _translate_implies(node, ctx)

    # --- Equivalence -------------------------------------------------------
    if isinstance(node, ltlnode.EquivalenceNode):
        return _translate_equivalence(node, ctx)

    # --- Globally ----------------------------------------------------------
    if isinstance(node, ltlnode.GloballyNode):
        return _translate_globally(node, ctx)

    # --- Finally -----------------------------------------------------------
    if isinstance(node, ltlnode.FinallyNode):
        return _translate_finally(node, ctx)

    # --- Next --------------------------------------------------------------
    if isinstance(node, ltlnode.NextNode):
        return _translate_next(node, ctx)

    # --- Until -------------------------------------------------------------
    if isinstance(node, ltlnode.UntilNode):
        return _translate_until(node, ctx)

    # Fallback: use the node's own __str__
    return str(node)


# ---------------------------------------------------------------------------
# Operator translators
# ---------------------------------------------------------------------------

# --- NOT ------------------------------------------------------------------

def _translate_not(node: ltlnode.NotNode, ctx: _Ctx) -> str:
    inner = node.operand

    # !(F p) => "'p' never occurs."
    if isinstance(inner, ltlnode.FinallyNode):
        target = _inner(inner.operand, ctx.child(inline=True))
        return f"{target} never occurs"

    # !(G p) => "it is not always the case that 'p' holds"
    if isinstance(inner, ltlnode.GloballyNode):
        target = _inner(inner.operand, ctx.child(inline=True))
        return f"it is not always the case that {target} holds"

    # !!p => p  (double negation)
    if isinstance(inner, ltlnode.NotNode):
        return _inner(inner.operand, ctx)

    # !(p & q) => De Morgan
    if isinstance(inner, ltlnode.AndNode):
        l = _inner(inner.left, ctx.child(inline=True))
        r = _inner(inner.right, ctx.child(inline=True))
        return f"not both {l} and {r}"

    # !(p | q) => De Morgan
    if isinstance(inner, ltlnode.OrNode):
        l = _inner(inner.left, ctx.child(inline=True))
        r = _inner(inner.right, ctx.child(inline=True))
        return f"neither {l} nor {r}"

    # !(p -> q)
    if isinstance(inner, ltlnode.ImpliesNode):
        l = _inner(inner.left, ctx.child(inline=True))
        r = _inner(inner.right, ctx.child(inline=True))
        return f"{l} holds, but {r} does not"

    # Generic negation
    if _is_lit(inner):
        return f"'{inner.value}' does not hold"
    target = _inner(inner, ctx.child(inline=True))
    return f"it is not the case that {target}"


# --- AND ------------------------------------------------------------------

def _translate_and(node: ltlnode.AndNode, ctx: _Ctx) -> str:
    # !p & !q  => neither ... nor
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        ll = _inner(node.left.operand, ctx.child(inline=True))
        rr = _inner(node.right.operand, ctx.child(inline=True))
        return f"neither {ll} nor {rr}"

    l = _inner(node.left, ctx.child(inline=True))
    r = _inner(node.right, ctx.child(inline=True))
    return f"both {l} and {r}"


# --- OR -------------------------------------------------------------------

def _translate_or(node: ltlnode.OrNode, ctx: _Ctx) -> str:
    # !p | !q  => not both ... and
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        ll = _inner(node.left.operand, ctx.child(inline=True))
        rr = _inner(node.right.operand, ctx.child(inline=True))
        return f"not both {ll} and {rr}"

    l = _inner(node.left, ctx.child(inline=True))
    r = _inner(node.right, ctx.child(inline=True))
    return f"either {l} or {r}"


# --- IMPLIES --------------------------------------------------------------

def _translate_implies(node: ltlnode.ImpliesNode, ctx: _Ctx) -> str:
    l = _inner(node.left, ctx.child(inline=True))
    r = _inner(node.right, ctx.child(inline=True))

    # p -> !q  (exclusion)
    if isinstance(node.right, ltlnode.NotNode):
        rr = _inner(node.right.operand, ctx.child(inline=True))
        if _is_lit(node.left) and _is_lit(node.right.operand):
            return f"{l} excludes {rr}"
        return f"if {l} holds, then {rr} does not"

    # !p -> q  (unless)
    if isinstance(node.left, ltlnode.NotNode):
        ll = _inner(node.left.operand, ctx.child(inline=True))
        return f"{r} unless {ll}"

    # (p & q) -> r
    if isinstance(node.left, ltlnode.AndNode):
        pl = _inner(node.left.left, ctx.child(inline=True))
        pr = _inner(node.left.right, ctx.child(inline=True))
        return f"if both {pl} and {pr}, then {r}"

    # (p | q) -> r
    if isinstance(node.left, ltlnode.OrNode):
        pl = _inner(node.left.left, ctx.child(inline=True))
        pr = _inner(node.left.right, ctx.child(inline=True))
        return f"if either {pl} or {pr}, then {r}"

    # p -> (q & r)
    if isinstance(node.right, ltlnode.AndNode):
        rl = _inner(node.right.left, ctx.child(inline=True))
        rr = _inner(node.right.right, ctx.child(inline=True))
        return f"if {l} holds, then both {rl} and {rr} follow"

    # p -> (q | r)
    if isinstance(node.right, ltlnode.OrNode):
        rl = _inner(node.right.left, ctx.child(inline=True))
        rr = _inner(node.right.right, ctx.child(inline=True))
        return f"if {l} holds, then either {rl} or {rr}"

    return f"if {l} holds, then {r}"


# --- EQUIVALENCE ----------------------------------------------------------

def _translate_equivalence(node: ltlnode.EquivalenceNode, ctx: _Ctx) -> str:
    l = _inner(node.left, ctx.child(inline=True))
    r = _inner(node.right, ctx.child(inline=True))
    return f"{l} holds exactly when {r} holds"


# --- GLOBALLY -------------------------------------------------------------

def _translate_globally(node: ltlnode.GloballyNode, ctx: _Ctx) -> str:
    inner = node.operand

    # G(!p)  => "'p' never holds."
    if isinstance(inner, ltlnode.NotNode):
        target = _inner(inner.operand, ctx.child("globally", inline=True))
        return f"{target} never holds"

    # G(p -> ...) patterns
    if isinstance(inner, ltlnode.ImpliesNode):
        left = inner.left
        right = inner.right

        # -- G(p -> X p) or G(p -> G p):  persistence
        if isinstance(right, (ltlnode.NextNode, ltlnode.GloballyNode)):
            rhs_inner = right.operand
            if _same_literal(left, rhs_inner):
                lit = _lit(left)
                return f"once {lit} becomes true, it remains true forever"

        # -- G(p -> F q):  response pattern
        if isinstance(right, ltlnode.FinallyNode):
            # G((p U q) -> F r)
            if isinstance(left, ltlnode.UntilNode):
                p = _inner(left.left, ctx.child("globally", inline=True))
                q = _inner(left.right, ctx.child("globally", inline=True))
                r = _inner(right.operand, ctx.child("globally", inline=True))
                return _join_sentences(
                    f"suppose {p} holds continuously until {q} occurs",
                    f"then {r} must eventually follow",
                    "this applies every time such a situation arises",
                )

            lhs = _inner(left, ctx.child("globally", inline=True))
            rhs = _inner(right.operand, ctx.child("globally", inline=True))
            return f"whenever {lhs} holds, {rhs} must eventually follow"

        # -- G(p -> X(F q)):  bounded response
        if isinstance(right, ltlnode.NextNode) and isinstance(right.operand, ltlnode.FinallyNode):
            lhs = _inner(left, ctx.child("globally", inline=True))
            rhs = _inner(right.operand.operand, ctx.child("globally", inline=True))
            return f"whenever {lhs} holds, starting from the very next step, {rhs} is guaranteed to eventually occur"

        # -- G(p -> X q):  immediate response (not same literal)
        if isinstance(right, ltlnode.NextNode):
            lhs = _inner(left, ctx.child("globally", inline=True))
            rhs = _inner(right.operand, ctx.child("globally", inline=True))
            return f"whenever {lhs} holds, {rhs} must hold in the very next step"

        # -- G(p -> (q U r)):  chain precedence
        if isinstance(right, ltlnode.UntilNode):
            lhs = _inner(left, ctx.child("globally", inline=True))
            ul = _inner(right.left, ctx.child("globally", inline=True))
            ur = _inner(right.right, ctx.child("globally", inline=True))
            return f"whenever {lhs} holds, {ul} must hold until {ur} occurs"

        # -- G(p -> (F q & F r)):  chain response
        if isinstance(right, ltlnode.AndNode):
            if isinstance(right.left, ltlnode.FinallyNode) and isinstance(right.right, ltlnode.FinallyNode):
                lhs = _inner(left, ctx.child("globally", inline=True))
                rl = _inner(right.left.operand, ctx.child("globally", inline=True))
                rr = _inner(right.right.operand, ctx.child("globally", inline=True))
                return f"whenever {lhs} holds, both {rl} and {rr} are guaranteed to eventually occur (though not necessarily at the same time)"

        # -- G(p -> q):  generic rule
        lhs = _inner(left, ctx.child("globally", inline=True))
        rhs = _inner(right, ctx.child("globally", inline=True))
        return f"whenever {lhs} holds, {rhs} must also hold"

    # G(F p)  => recurrence / infinitely often
    if isinstance(inner, ltlnode.FinallyNode):
        fi = inner.operand
        # G(F(p & q))
        if isinstance(fi, ltlnode.AndNode):
            l = _inner(fi.left, ctx.child("globally", inline=True))
            r = _inner(fi.right, ctx.child("globally", inline=True))
            return f"both {l} and {r} must occur together infinitely often"
        target = _inner(fi, ctx.child("globally", inline=True))
        return f"{target} must occur infinitely often"

    # G(G(...)) => idempotent
    if isinstance(inner, ltlnode.GloballyNode):
        return _translate_globally(inner, ctx)

    # G(p & q) / G(p | q) - simple
    if isinstance(inner, ltlnode.AndNode):
        l = _inner(inner.left, ctx.child("globally", inline=True))
        r = _inner(inner.right, ctx.child("globally", inline=True))
        return f"at all times, both {l} and {r} must hold"

    if isinstance(inner, ltlnode.OrNode):
        l = _inner(inner.left, ctx.child("globally", inline=True))
        r = _inner(inner.right, ctx.child("globally", inline=True))
        return f"at all times, either {l} or {r} must hold"

    # G(literal) or G(complex)
    target = _inner(inner, ctx.child("globally", inline=True))
    if _is_lit(inner):
        return f"{target} must hold at all times"
    return f"at all times, {target}"


# --- FINALLY --------------------------------------------------------------

def _translate_finally(node: ltlnode.FinallyNode, ctx: _Ctx) -> str:
    inner = node.operand

    # F(F(...)) => idempotent
    if isinstance(inner, ltlnode.FinallyNode):
        return _translate_finally(inner, ctx)

    # F(G(...)) patterns
    if isinstance(inner, ltlnode.GloballyNode):
        gi = inner.operand

        # F(G(!p))
        if isinstance(gi, ltlnode.NotNode):
            target = _inner(gi.operand, ctx.child("finally", inline=True))
            return f"eventually, a point is reached after which {target} never holds again"

        # F(G(p -> F q))
        if isinstance(gi, ltlnode.ImpliesNode) and isinstance(gi.right, ltlnode.FinallyNode):
            lhs = _inner(gi.left, ctx.child("finally", inline=True))
            rhs = _inner(gi.right.operand, ctx.child("finally", inline=True))
            return _join_sentences(
                "eventually, a stable regime is reached",
                f"after that point, whenever {lhs} holds, {rhs} must eventually follow",
            )

        # F(G(p -> q))  generic stable rule
        if isinstance(gi, ltlnode.ImpliesNode):
            lhs = _inner(gi.left, ctx.child("finally", inline=True))
            rhs = _inner(gi.right, ctx.child("finally", inline=True))
            return _join_sentences(
                "eventually, a stable regime is reached",
                f"after that point, whenever {lhs} holds, {rhs} must also hold",
            )

        # F(G(p & q))
        if isinstance(gi, ltlnode.AndNode):
            l = _inner(gi.left, ctx.child("finally", inline=True))
            r = _inner(gi.right, ctx.child("finally", inline=True))
            return f"eventually, both {l} and {r} become true and remain true forever"

        # F(G p) generic persistence / stability
        target = _inner(gi, ctx.child("finally", inline=True))
        return f"eventually, {target} becomes true and remains true forever"

    # F(!p)
    if isinstance(inner, ltlnode.NotNode):
        target = _inner(inner.operand, ctx.child("finally", inline=True))
        return f"eventually, {target} will cease to hold"

    # F(p & G q)  or  F(G q & p)  -  persistence after trigger
    if isinstance(inner, ltlnode.AndNode):
        l, r = inner.left, inner.right
        if isinstance(r, ltlnode.GloballyNode):
            trigger = _inner(l, ctx.child("finally", inline=True))
            persist = _inner(r.operand, ctx.child("finally", inline=True))
            return _join_sentences(
                f"eventually, {trigger} occurs",
                f"from that point on, {persist} holds forever",
            )
        if isinstance(l, ltlnode.GloballyNode):
            trigger = _inner(r, ctx.child("finally", inline=True))
            persist = _inner(l.operand, ctx.child("finally", inline=True))
            return _join_sentences(
                f"eventually, {trigger} occurs",
                f"from that point on, {persist} holds forever",
            )
        # F(p & q) simple simultaneity
        ll = _inner(l, ctx.child("finally", inline=True))
        rr = _inner(r, ctx.child("finally", inline=True))
        return f"eventually, both {ll} and {rr} will be true at the same time"

    # F(p -> G q)  trigger-to-permanence
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.GloballyNode):
        trigger = _inner(inner.left, ctx.child("finally", inline=True))
        result = _inner(inner.right.operand, ctx.child("finally", inline=True))
        return f"eventually, once {trigger} holds, {result} will hold forever after"

    # F(literal)
    if _is_lit(inner):
        return f"{_lit(inner)} must eventually occur"

    # Generic F(...)
    target = _inner(inner, ctx.child("finally", inline=True))
    return f"eventually, {target}"


# --- NEXT -----------------------------------------------------------------

def _count_next_chain(node: ltlnode.LTLNode) -> tuple[int, ltlnode.LTLNode]:
    """Count consecutive X nodes; return (count, innermost operand)."""
    n = 0
    while isinstance(node, ltlnode.NextNode):
        n += 1
        node = node.operand
    return n, node


def _translate_next(node: ltlnode.NextNode, ctx: _Ctx) -> str:
    steps, core = _count_next_chain(node)

    # X(p U q) => "starting from the next step, ..."
    if steps == 1 and isinstance(core, ltlnode.UntilNode):
        l = _inner(core.left, ctx.child("next", inline=True))
        r = _inner(core.right, ctx.child("next", inline=True))
        return f"starting from the next step, {l} holds until {r} occurs"

    # X(F q) => "starting from the next step, q must eventually occur"
    if steps == 1 and isinstance(core, ltlnode.FinallyNode):
        target = _inner(core.operand, ctx.child("next", inline=True))
        return f"starting from the next step, {target} must eventually occur"

    target = _inner(core, ctx.child("next", inline=True))

    if steps == 1:
        return f"in the very next step, {target}"
    return f"in {steps} steps, {target}"


# --- UNTIL ----------------------------------------------------------------

def _translate_until(node: ltlnode.UntilNode, ctx: _Ctx) -> str:
    l_node, r_node = node.left, node.right

    # (G p) U (F q) => obligation until release
    if isinstance(l_node, ltlnode.GloballyNode) and isinstance(r_node, ltlnode.FinallyNode):
        l = _inner(l_node.operand, ctx.child("until", inline=True))
        r = _inner(r_node.operand, ctx.child("until", inline=True))
        return _join_sentences(
            f"{l} must hold continuously at all times",
            f"this obligation persists until {r} eventually occurs",
        )

    # (p U q) U r => nested until
    if isinstance(l_node, ltlnode.UntilNode):
        p = _inner(l_node.left, ctx.child("until", inline=True))
        q = _inner(l_node.right, ctx.child("until", inline=True))
        r = _inner(r_node, ctx.child("until", inline=True))
        return _join_sentences(
            f"first, {p} holds until {q} occurs",
            f"that whole phase lasts until {r} occurs",
        )

    l = _inner(l_node, ctx.child("until", inline=True))
    r = _inner(r_node, ctx.child("until", inline=True))
    return f"{l} must hold until {r} occurs"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(node: ltlnode.LTLNode) -> str:
    """Translate an LTL AST node into requirements-style English prose.

    The returned string is a complete, capitalized, period-terminated
    paragraph (possibly multiple sentences for complex formulas).
    """
    raw = _inner(node, _Ctx())
    # If _inner already produced joined sentences (with periods inside),
    # just ensure it's clean.
    raw = raw.strip()
    # Capitalize and terminate.
    result = _capitalize(raw)
    if result and result[-1] not in ".!?":
        result += "."
    return result
