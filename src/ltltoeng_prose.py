"""
Clause-chaining prose translator for LTL formulas.

Produces flowing, natural prose that reads like a paragraph from a
requirements document.  A single LTL formula may become multiple short
sentences connected by discourse connectives ("After that point, ...",
"Suppose that ...", "This applies every time ...").

Composition discipline
----------------------
Only literals translate to noun-like fragments (``'p'``); every other node
translates to a full clause with its own verb.  Templates therefore only
append verbs ("holds", "occurs", "must eventually follow") to literal
operands, and embed anything else via ``_clause`` inside a clause-safe
frame ("it must eventually be the case that ...").

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
    return _inner(node, _Ctx(inline=True))


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


def _clause(node: ltlnode.LTLNode, ctx: _Ctx) -> str:
    """Return a full clause (subject + verb) for *node*.

    Literals get an explicit verb; negated literals get "does not hold";
    everything else already translates to a clause.
    """
    if _is_lit(node):
        return f"{_lit(node)} holds"
    if isinstance(node, ltlnode.NotNode) and _is_lit(node.operand):
        return f"{_lit(node.operand)} does not hold"
    # Embedded clauses drop the deontic "must" that top-level templates use:
    # "'p' holds at all times", not "'p' must hold at all times".
    if isinstance(node, ltlnode.GloballyNode) and _is_lit(node.operand):
        return f"{_lit(node.operand)} holds at all times"
    if isinstance(node, ltlnode.FinallyNode) and _is_lit(node.operand):
        return f"{_lit(node.operand)} eventually occurs"
    return _inner(node, ctx.child(inline=True))


def _occurs(node: ltlnode.LTLNode, ctx: _Ctx) -> str:
    """Like _clause, but with event phrasing for literals ("'p' occurs")."""
    if _is_lit(node):
        return f"{_lit(node)} occurs"
    return _clause(node, ctx)


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
        if ctx.inline:
            return f"'{node.value}'"
        return f"'{node.value}' holds"

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
        if _is_lit(inner.operand):
            return f"{_lit(inner.operand)} never occurs"
        return f"it is never the case that {_clause(inner.operand, ctx)}"

    # !(G p) => "it is not always the case that 'p' holds"
    if isinstance(inner, ltlnode.GloballyNode):
        return f"it is not always the case that {_clause(inner.operand, ctx)}"

    # !!p => p  (double negation)
    if isinstance(inner, ltlnode.NotNode):
        return _inner(inner.operand, ctx)

    # !(p & q) => De Morgan
    if isinstance(inner, ltlnode.AndNode):
        if _is_lit(inner.left) and _is_lit(inner.right):
            return f"not both {_lit(inner.left)} and {_lit(inner.right)}"
        l = _clause(inner.left, ctx)
        r = _clause(inner.right, ctx)
        return f"it is not the case that both of the following hold: {l}, and {r}"

    # !(p | q) => De Morgan
    if isinstance(inner, ltlnode.OrNode):
        if _is_lit(inner.left) and _is_lit(inner.right):
            return f"neither {_lit(inner.left)} nor {_lit(inner.right)}"
        l = _clause(inner.left, ctx)
        r = _clause(inner.right, ctx)
        return f"neither of the following holds: {l}, nor {r}"

    # !(p -> q)
    if isinstance(inner, ltlnode.ImpliesNode):
        l = _clause(inner.left, ctx)
        if _is_lit(inner.right):
            return f"{l}, but {_lit(inner.right)} does not hold"
        return f"{l}, but it is not the case that {_clause(inner.right, ctx)}"

    # Generic negation
    if _is_lit(inner):
        return f"'{inner.value}' does not hold"
    return f"it is not the case that {_clause(inner, ctx)}"


# --- AND ------------------------------------------------------------------

def _translate_and(node: ltlnode.AndNode, ctx: _Ctx) -> str:
    # !p & !q  => neither ... nor
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        if _is_lit(node.left.operand) and _is_lit(node.right.operand):
            l = _lit(node.left.operand)
            r = _lit(node.right.operand)
            return f"neither {l} nor {r}" + (" holds" if not ctx.inline else "")

    if _is_lit(node.left) and _is_lit(node.right):
        l = _lit(node.left)
        r = _lit(node.right)
        return f"both {l} and {r}" + (" hold" if not ctx.inline else "")

    l = _clause(node.left, ctx)
    r = _clause(node.right, ctx)
    return f"both of the following hold: {l}, and {r}"


# --- OR -------------------------------------------------------------------

def _translate_or(node: ltlnode.OrNode, ctx: _Ctx) -> str:
    # !p | !q  => not both ... and
    if isinstance(node.left, ltlnode.NotNode) and isinstance(node.right, ltlnode.NotNode):
        if _is_lit(node.left.operand) and _is_lit(node.right.operand):
            ll = _lit(node.left.operand)
            rr = _lit(node.right.operand)
            return f"not both {ll} and {rr}" + (" hold" if not ctx.inline else "")

    if _is_lit(node.left) and _is_lit(node.right):
        l = _lit(node.left)
        r = _lit(node.right)
        return f"either {l} or {r}" + (" holds" if not ctx.inline else "")

    l = _clause(node.left, ctx)
    r = _clause(node.right, ctx)
    return f"at least one of the following holds: {l}, or {r}"


# --- IMPLIES --------------------------------------------------------------

def _translate_implies(node: ltlnode.ImpliesNode, ctx: _Ctx) -> str:
    # p -> !q  (exclusion)
    if isinstance(node.right, ltlnode.NotNode):
        if _is_lit(node.left) and _is_lit(node.right.operand):
            return f"{_lit(node.left)} excludes {_lit(node.right.operand)}"
        l = _clause(node.left, ctx)
        rr = node.right.operand
        if _is_lit(rr):
            return f"if {l}, then {_lit(rr)} does not hold"
        return f"if {l}, then it is not the case that {_clause(rr, ctx)}"

    # !p -> q  (unless)
    if isinstance(node.left, ltlnode.NotNode):
        ll = _clause(node.left.operand, ctx)
        r = _clause(node.right, ctx)
        return f"{r}, unless {ll}"

    # (p & q) -> r
    if isinstance(node.left, ltlnode.AndNode):
        pl = _clause(node.left.left, ctx)
        pr = _clause(node.left.right, ctx)
        r = _clause(node.right, ctx)
        return f"if both {pl} and {pr}, then {r}"

    # (p | q) -> r
    if isinstance(node.left, ltlnode.OrNode):
        pl = _clause(node.left.left, ctx)
        pr = _clause(node.left.right, ctx)
        r = _clause(node.right, ctx)
        return f"if either {pl} or {pr}, then {r}"

    # p -> (q & r)
    if isinstance(node.right, ltlnode.AndNode):
        l = _clause(node.left, ctx)
        rl = _clause(node.right.left, ctx)
        rr = _clause(node.right.right, ctx)
        return f"if {l}, then both {rl} and {rr}"

    # p -> (q | r)
    if isinstance(node.right, ltlnode.OrNode):
        l = _clause(node.left, ctx)
        rl = _clause(node.right.left, ctx)
        rr = _clause(node.right.right, ctx)
        return f"if {l}, then either {rl} or {rr}"

    l = _clause(node.left, ctx)
    r = _clause(node.right, ctx)
    return f"if {l}, then {r}"


# --- EQUIVALENCE ----------------------------------------------------------

def _translate_equivalence(node: ltlnode.EquivalenceNode, ctx: _Ctx) -> str:
    l = _clause(node.left, ctx)
    r = _clause(node.right, ctx)
    return f"{l} exactly when {r}"


# --- GLOBALLY -------------------------------------------------------------

def _translate_globally(node: ltlnode.GloballyNode, ctx: _Ctx) -> str:
    inner = node.operand

    # G(!p)  => "'p' never holds."
    if isinstance(inner, ltlnode.NotNode):
        if _is_lit(inner.operand):
            return f"{_lit(inner.operand)} never holds"
        return f"at no point is it the case that {_clause(inner.operand, ctx)}"

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

        whenever = _clause(left, ctx.child("globally"))

        # -- G(p -> F q):  response pattern
        if isinstance(right, ltlnode.FinallyNode):
            # G((p U q) -> F r)
            if isinstance(left, ltlnode.UntilNode):
                p = _clause(left.left, ctx.child("globally"))
                q = _occurs(left.right, ctx.child("globally"))
                r = _clause(right.operand, ctx.child("globally"))
                return _join_sentences(
                    f"suppose {p} continuously, until {q}",
                    f"then it must eventually be the case that {r}",
                    "this applies every time such a situation arises",
                )

            if _is_lit(right.operand):
                return f"whenever {whenever}, {_lit(right.operand)} must eventually follow"
            rhs = _clause(right.operand, ctx.child("globally"))
            return f"whenever {whenever}, it must eventually be the case that {rhs}"

        # -- G(p -> X(F q)):  bounded response
        if isinstance(right, ltlnode.NextNode) and isinstance(right.operand, ltlnode.FinallyNode):
            target = right.operand.operand
            if _is_lit(target):
                return f"whenever {whenever}, starting from the very next step, {_lit(target)} is guaranteed to eventually occur"
            rhs = _clause(target, ctx.child("globally"))
            return f"whenever {whenever}, starting from the very next step, it is guaranteed that eventually, {rhs}"

        # -- G(p -> X q):  immediate response (not same literal)
        if isinstance(right, ltlnode.NextNode):
            target = right.operand
            if _is_lit(target):
                return f"whenever {whenever}, {_lit(target)} must hold in the very next step"
            rhs = _clause(target, ctx.child("globally"))
            return f"whenever {whenever}, then in the very next step, {rhs}"

        # -- G(p -> (q U r)):  chain precedence
        if isinstance(right, ltlnode.UntilNode):
            ul = _clause(right.left, ctx.child("globally"))
            ur = _occurs(right.right, ctx.child("globally"))
            return f"whenever {whenever}, it must remain the case that {ul} until {ur}"

        # -- G(p -> (F q & F r)):  chain response
        if isinstance(right, ltlnode.AndNode):
            if isinstance(right.left, ltlnode.FinallyNode) and isinstance(right.right, ltlnode.FinallyNode):
                rl = _occurs(right.left.operand, ctx.child("globally"))
                rr = _occurs(right.right.operand, ctx.child("globally"))
                return f"whenever {whenever}, two things are guaranteed to eventually happen (though not necessarily at the same time): {rl}, and {rr}"

        # -- G(p -> q):  generic rule
        if _is_lit(right):
            return f"whenever {whenever}, {_lit(right)} must also hold"
        rhs = _clause(right, ctx.child("globally"))
        return f"whenever {whenever}, it must also be the case that {rhs}"

    # G(F p)  => recurrence / infinitely often
    if isinstance(inner, ltlnode.FinallyNode):
        fi = inner.operand
        # G(F(p & q))
        if isinstance(fi, ltlnode.AndNode) and _is_lit(fi.left) and _is_lit(fi.right):
            return f"both {_lit(fi.left)} and {_lit(fi.right)} must occur together infinitely often"
        if _is_lit(fi):
            return f"{_lit(fi)} must occur infinitely often"
        target = _clause(fi, ctx.child("globally"))
        return f"it must be the case infinitely often that {target}"

    # G(G(...)) => idempotent
    if isinstance(inner, ltlnode.GloballyNode):
        return _translate_globally(inner, ctx)

    # G(p & q) / G(p | q) - simple
    if isinstance(inner, ltlnode.AndNode):
        if _is_lit(inner.left) and _is_lit(inner.right):
            return f"at all times, both {_lit(inner.left)} and {_lit(inner.right)} must hold"
        l = _clause(inner.left, ctx.child("globally"))
        r = _clause(inner.right, ctx.child("globally"))
        return f"at all times, both of the following must hold: {l}, and {r}"

    if isinstance(inner, ltlnode.OrNode):
        if _is_lit(inner.left) and _is_lit(inner.right):
            return f"at all times, either {_lit(inner.left)} or {_lit(inner.right)} must hold"
        l = _clause(inner.left, ctx.child("globally"))
        r = _clause(inner.right, ctx.child("globally"))
        return f"at all times, at least one of the following must hold: {l}, or {r}"

    # G(literal) or G(complex)
    if _is_lit(inner):
        return f"{_lit(inner)} must hold at all times"
    target = _clause(inner, ctx.child("globally"))
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
            if _is_lit(gi.operand):
                return f"eventually, a point is reached after which {_lit(gi.operand)} never holds again"
            target = _clause(gi.operand, ctx.child("finally"))
            return f"eventually, a point is reached after which it is never again the case that {target}"

        # F(G(p -> F q))
        if isinstance(gi, ltlnode.ImpliesNode) and isinstance(gi.right, ltlnode.FinallyNode):
            lhs = _clause(gi.left, ctx.child("finally"))
            if _is_lit(gi.right.operand):
                follow = f"{_lit(gi.right.operand)} must eventually follow"
            else:
                follow = f"it must eventually be the case that {_clause(gi.right.operand, ctx.child('finally'))}"
            return _join_sentences(
                "eventually, a stable regime is reached",
                f"after that point, whenever {lhs}, {follow}",
            )

        # F(G(p -> q))  generic stable rule
        if isinstance(gi, ltlnode.ImpliesNode):
            lhs = _clause(gi.left, ctx.child("finally"))
            if _is_lit(gi.right):
                also = f"{_lit(gi.right)} must also hold"
            else:
                also = f"it must also be the case that {_clause(gi.right, ctx.child('finally'))}"
            return _join_sentences(
                "eventually, a stable regime is reached",
                f"after that point, whenever {lhs}, {also}",
            )

        # F(G(p & q))
        if isinstance(gi, ltlnode.AndNode) and _is_lit(gi.left) and _is_lit(gi.right):
            return f"eventually, both {_lit(gi.left)} and {_lit(gi.right)} become true and remain true forever"

        # F(G p) generic persistence / stability
        if _is_lit(gi):
            return f"eventually, {_lit(gi)} becomes true and remains true forever"
        target = _clause(gi, ctx.child("finally"))
        return f"eventually, it permanently becomes the case that {target}"

    # F(!p)
    if isinstance(inner, ltlnode.NotNode):
        if _is_lit(inner.operand):
            return f"eventually, {_lit(inner.operand)} will cease to hold"
        return f"eventually, {_clause(inner, ctx.child('finally'))}"

    # F(p & G q)  or  F(G q & p)  -  persistence after trigger
    if isinstance(inner, ltlnode.AndNode):
        l, r = inner.left, inner.right
        if isinstance(r, ltlnode.GloballyNode) or isinstance(l, ltlnode.GloballyNode):
            g_node, trigger_node = (r, l) if isinstance(r, ltlnode.GloballyNode) else (l, r)
            trigger = _occurs(trigger_node, ctx.child("finally"))
            if _is_lit(g_node.operand):
                persist = f"{_lit(g_node.operand)} holds forever"
            else:
                persist = f"it is always the case that {_clause(g_node.operand, ctx.child('finally'))}"
            return _join_sentences(
                f"eventually, {trigger}",
                f"from that point on, {persist}",
            )
        # F(p & q) simple simultaneity
        if _is_lit(l) and _is_lit(r):
            return f"eventually, both {_lit(l)} and {_lit(r)} will be true at the same time"
        ll = _clause(l, ctx.child("finally"))
        rr = _clause(r, ctx.child("finally"))
        return f"eventually, both of the following hold at the same time: {ll}, and {rr}"

    # F(p -> G q)  trigger-to-permanence
    if isinstance(inner, ltlnode.ImpliesNode) and isinstance(inner.right, ltlnode.GloballyNode):
        trigger = _clause(inner.left, ctx.child("finally"))
        if _is_lit(inner.right.operand):
            result = f"{_lit(inner.right.operand)} will hold forever after"
        else:
            result = f"it will forever after be the case that {_clause(inner.right.operand, ctx.child('finally'))}"
        return f"eventually, once {trigger}, {result}"

    # F(literal)
    if _is_lit(inner):
        return f"{_lit(inner)} must eventually occur"

    # Generic F(...)
    target = _clause(inner, ctx.child("finally"))
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
        l = _clause(core.left, ctx.child("next"))
        r = _occurs(core.right, ctx.child("next"))
        return f"starting from the next step, it must remain the case that {l} until {r}"

    # X(F q) => "starting from the next step, q must eventually occur"
    if steps == 1 and isinstance(core, ltlnode.FinallyNode):
        if _is_lit(core.operand):
            return f"starting from the next step, {_lit(core.operand)} must eventually occur"
        target = _clause(core.operand, ctx.child("next"))
        return f"starting from the next step, it must eventually be the case that {target}"

    target = _clause(core, ctx.child("next"))

    if steps == 1:
        return f"in the very next step, {target}"
    return f"in {steps} steps, {target}"


# --- UNTIL ----------------------------------------------------------------

def _translate_until(node: ltlnode.UntilNode, ctx: _Ctx) -> str:
    l_node, r_node = node.left, node.right

    # (G p) U (F q) => obligation until release
    if isinstance(l_node, ltlnode.GloballyNode) and isinstance(r_node, ltlnode.FinallyNode):
        if _is_lit(l_node.operand):
            obligation = f"{_lit(l_node.operand)} must hold continuously at all times"
        else:
            obligation = f"it must continuously be the case that {_clause(l_node.operand, ctx.child('until'))}"
        release = _occurs(r_node.operand, ctx.child("until"))
        return _join_sentences(
            obligation,
            f"this obligation persists until eventually, {release}",
        )

    # (p U q) U r => nested until
    if isinstance(l_node, ltlnode.UntilNode):
        p = _clause(l_node.left, ctx.child("until"))
        q = _occurs(l_node.right, ctx.child("until"))
        r = _occurs(r_node, ctx.child("until"))
        return _join_sentences(
            f"first, it must remain the case that {p} until {q}",
            f"that whole phase lasts until {r}",
        )

    if _is_lit(l_node) and _is_lit(r_node):
        return f"{_lit(l_node)} must hold until {_lit(r_node)} occurs"
    l = _clause(l_node, ctx.child("until"))
    r = _occurs(r_node, ctx.child("until"))
    return f"it must remain the case that {l} until {r}"


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
