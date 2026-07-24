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

A theme may also be *deontic*: the formula is phrased as a rule someone could
violate ("the VPN must be connected") rather than a description, and a
preamble puts the student in the role of policing it.  The Wason literature
locates the facilitation effect in exactly this framing — violation-checkable
rules — not in concrete content per se (Griggs & Cox 1982; Cheng & Holyoak
1985; Cosmides 1989).  The built-in deontic theme, "abac", audits access to a
confidential document.  Its four attributes are deliberately independent in
the student's mental model: nothing physical forces any combination of them,
so every state assignment is conceivable and only the policy under test rules
combinations out.  Themes whose atoms are coupled by physics (doors, rooms,
occupancy) would smuggle constraints into the trace semantics.

Public API
----------
    translate(node, theme=None) -> str
    legend(node, theme=None) -> [(literal, state phrase)]
    remap_to_theme(node, theme=None) -> node or None
    THEMES: dict of built-in theme names -> Theme objects

All phrasing is strictly state-based ("the blue light is on"), never
event-based ("the blue light turns on"): a bare LTL literal holds in every
state where it is true, not only on a false->true transition, so edge
phrasing would describe a different formula than the one being asked.

The sentence itself never mentions the letters, but the answer options are
written in them, so a themed question must be posed together with its key
(`legend()`): otherwise the exercise also tests whether the student can guess
that `d` names "the document is open" -- and not, say, the document, which has
more than one state -- which is a guessing game about naming, not about LTL.
A key entry names a whole state, never a subject, because that is what a
literal denotes.

Example:
    node = parse_ltl_string("G(b -> F a)")
    translate(node, theme=THEMES["lights"])
    # => "Whenever the blue light is on, then eventually the amber light is on."
    legend(node, theme=THEMES["lights"])
    # => [("b", "the blue light is on"), ("a", "the amber light is on")]
"""

from __future__ import annotations
from dataclasses import dataclass
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
                     The positive phrase doubles as the literal's key entry
                     (see legend), so it must name the state the letter stands
                     for on its own, out of sentence context.
        deontic:     Phrase the formula as an enforceable rule ("must") rather
                     than a description.  Requires copular literal phrases
                     ("the X is Y") so the modal transform stays grammatical.
        preamble:    Stance-setting sentence putting the student in the role of
                     enforcing the rule (only meaningful for deontic themes).
                     Empty = no preamble.
        rule_noun:   What the sentence *is*, as a noun phrase, completing
                     "...best represents ___?".  Empty falls back to the
                     generic "this English sentence".  Pairs with preamble:
                     both belong to the question being asked, not to the
                     property, so the UI puts them in the question prompt.
    """
    name: str
    description: str
    literals: Dict[str, tuple[str, str]]  # lit -> (positive, negative)
    deontic: bool = False
    preamble: str = ""
    rule_noun: str = ""

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

# Deontic theme: an ABAC-style policy on one confidential document.  The four
# attributes are independent — no combination is physically impossible, only
# policy-forbidden — and each positive/negative pair is a natural antonym so
# negated literals read cleanly.  First-letter convention and the operator-safe
# letter pool (d, c, v, s) are preserved.
THEMES["abac"] = Theme(
    name="Document Access Audit",
    description="Auditing access to a confidential document.",
    deontic=True,
    # Both of these ride in the question prompt ("You are auditing access to a
    # confidential document. Which of the following LTL formulae best
    # represents this policy?") rather than above the sentence: the stance is
    # part of what is being asked, and hoisting it keeps the formalizable rule
    # the single prominent line in the card body.
    preamble="You are auditing access to a confidential document.",
    rule_noun="this policy",
    literals={
        "d": ("the document is open",            "the document is closed"),
        "c": ("the user's clearance is active",  "the user's clearance is revoked"),
        "v": ("the VPN is connected",            "the VPN is disconnected"),
        "s": ("the screen is shared",            "the screen is not shared"),
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


def _lit_phrase(node: ltlnode.LTLNode, theme: Theme) -> Optional[str]:
    """The state phrase for a literal or negated literal, else None."""
    if isinstance(node, ltlnode.LiteralNode):
        return theme.positive(node.value)
    if isinstance(node, ltlnode.NotNode) and isinstance(node.operand, ltlnode.LiteralNode):
        return theme.negative(node.operand.value)
    return None


def _modal(phrase: str, adverb: str = "") -> str:
    """Rewrite a copular state phrase as an obligation.

    "the VPN is connected"      -> "the VPN must be connected"
    "the screen is not shared"  -> "the screen must not be shared"
    With an adverb it slots in after "must":
    _modal("the VPN is connected", "eventually")
                                -> "the VPN must eventually be connected"
    Non-copular phrases fall back to a generic "it must be the case that"
    wrapper, so the transform is safe on any recursive translation.
    """
    must = f"must {adverb}".strip()
    if " is not " in phrase:
        return phrase.replace(" is not ", f" {must} not be ", 1)
    if " is " in phrase:
        return phrase.replace(" is ", f" {must} be ", 1)
    if " are " in phrase:
        return phrase.replace(" are ", f" {must} be ", 1)
    return f"it {must} be the case that {phrase}"


def _obligation(node: ltlnode.LTLNode, theme: Theme, adverb: str = "") -> str:
    """Deontic rendering of a rule's consequent/scope."""
    phrase = _lit_phrase(node, theme)
    if phrase is not None:
        return _modal(phrase, adverb)
    return _modal(_t(node, theme), adverb)


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
        if theme.deontic:
            return _modal(theme.positive(inner.operand.value), "never")
        return f"it is never the case that {theme.positive(inner.operand.value)}"

    # !!p
    if isinstance(inner, ltlnode.NotNode):
        return _t(inner.operand, theme)

    # !(p & q) -> not both
    if isinstance(inner, ltlnode.AndNode):
        if theme.deontic:
            return f"it must not be the case that both {_t(inner.left, theme)} and {_t(inner.right, theme)}"
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
    # Deontic themes place the obligation on the consequent; the trigger
    # stays indicative ("if the document is open, the VPN must be connected").
    if theme.deontic:
        r = _obligation(node.right, theme)
    else:
        r = _t(node.right, theme)

    # (p & q) -> r
    if isinstance(node.left, ltlnode.AndNode):
        return f"if both {_t(node.left.left, theme)} and {_t(node.left.right, theme)}, then {r}"

    # (p | q) -> r
    if isinstance(node.left, ltlnode.OrNode):
        return f"if either {_t(node.left.left, theme)} or {_t(node.left.right, theme)}, then {r}"

    return f"if {_t(node.left, theme)}, then {r}"


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
            if theme.deontic:
                return _modal(theme.positive(negated.value), "never")
            return f"it is never the case that {theme.positive(negated.value)}"
        # G(!(p & q)) -> "P must never hold while Q holds"
        if theme.deontic and isinstance(negated, ltlnode.AndNode):
            lp = _lit_phrase(negated.left, theme)
            rp = _lit_phrase(negated.right, theme)
            if lp is not None and rp is not None:
                return f"{_modal(lp, 'never')} while {rp}"
        return f"at no point may it be the case that {_t(negated, theme)}"

    # G(p -> ...) patterns
    if isinstance(inner, ltlnode.ImpliesNode):
        left = inner.left
        right = inner.right

        # G(p -> X p) or G(p -> G p) — persistence
        if isinstance(right, (ltlnode.NextNode, ltlnode.GloballyNode)):
            if _same_literal(left, right.operand):
                lit = left.value
                if theme.deontic:
                    return f"once {theme.positive(lit)}, it must stay that way forever"
                return f"once {theme.positive(lit)}, it stays that way forever"

        # G(p -> F q) — response
        if isinstance(right, ltlnode.FinallyNode):
            if isinstance(left, ltlnode.UntilNode):
                p = _t(left.left, theme)
                q = _t(left.right, theme)
                if theme.deontic:
                    r = _obligation(right.operand, theme, "eventually")
                    return _join(
                        f"suppose {p} continues until {q}",
                        f"then {r}",
                        "this rule applies every time",
                    )
                r = _t(right.operand, theme)
                return _join(
                    f"suppose {p} continues until {q}",
                    f"then eventually, {r}",
                    "this rule applies every time",
                )
            trigger = _t(left, theme)
            if theme.deontic:
                return f"whenever {trigger}, {_obligation(right.operand, theme, 'eventually')}"
            response = _t(right.operand, theme)
            return f"whenever {trigger}, then eventually {response}"

        # G(p -> X(F q)) — bounded response
        if isinstance(right, ltlnode.NextNode) and isinstance(right.operand, ltlnode.FinallyNode):
            trigger = _t(left, theme)
            if theme.deontic:
                response = _obligation(right.operand.operand, theme, "eventually")
                return f"whenever {trigger}, starting from the very next step, {response}"
            response = _t(right.operand.operand, theme)
            return f"whenever {trigger}, starting from the very next step, eventually {response}"

        # G(p -> X q) — immediate response
        if isinstance(right, ltlnode.NextNode):
            trigger = _t(left, theme)
            if theme.deontic:
                return f"whenever {trigger}, {_obligation(right.operand, theme)} in the very next step"
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
        if theme.deontic:
            return f"whenever {trigger}, {_obligation(right, theme)}"
        consequence = _t(right, theme)
        return f"whenever {trigger}, it must be the case that {consequence}"

    # G(F p) — recurrence.  The G and the F must be carried by separate
    # phrases ("no matter how much time passes" / "eventually"): a single
    # continuity idiom like "keeps being the case" reads as plain G and
    # collides with the G(p) distractor.
    if isinstance(inner, ltlnode.FinallyNode):
        fi = inner.operand
        if theme.deontic:
            return f"no matter how much time passes, {_obligation(fi, theme, 'eventually')}"
        if isinstance(fi, ltlnode.AndNode):
            return f"no matter how much time passes, eventually {_t(fi.left, theme)} and {_t(fi.right, theme)} at the same time"
        target = _t(fi, theme)
        return f"no matter how much time passes, eventually {target}"

    # G(G(...)) — idempotent
    if isinstance(inner, ltlnode.GloballyNode):
        return _t_globally(inner, theme)

    # G(p & q) / G(p | q)
    if isinstance(inner, ltlnode.AndNode):
        if theme.deontic:
            return f"at every moment, it must be the case that {_t(inner.left, theme)} and {_t(inner.right, theme)}"
        return f"at every moment, {_t(inner.left, theme)} and {_t(inner.right, theme)}"
    if isinstance(inner, ltlnode.OrNode):
        if theme.deontic:
            return f"at every moment, it must be the case that either {_t(inner.left, theme)} or {_t(inner.right, theme)}"
        return f"at every moment, either {_t(inner.left, theme)} or {_t(inner.right, theme)}"

    # G(literal)
    if isinstance(inner, ltlnode.LiteralNode):
        if theme.deontic:
            return _modal(theme.positive(inner.value), "always")
        return f"{theme.positive(inner.value)} at all times"
    if theme.deontic:
        # Next/Until renderings already carry their own "must"; wrapping
        # them in _modal would produce a double modal.
        if isinstance(inner, (ltlnode.NextNode, ltlnode.UntilNode)):
            return f"at every point, {_t(inner, theme)}"
        return _modal(_t(inner, theme), "always")
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
            if theme.deontic:
                response = _obligation(gi.right.operand, theme, "eventually")
                return _join(
                    "eventually, the system stabilizes",
                    f"from that point on, whenever {trigger}, {response}",
                )
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

    if theme.deontic:
        return _obligation(inner, theme, "eventually")
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

    if theme.deontic:
        phrase = _lit_phrase(core, theme)
        if phrase is not None:
            return f"{_modal(phrase)} in {_steps(steps)}"

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
    if theme.deontic:
        # "the document is closed" -> "the document must remain closed"
        lp = _lit_phrase(l_node, theme)
        if lp is not None and " is not " not in lp and " is " in lp:
            return f"{lp.replace(' is ', ' must remain ', 1)} until {r}"
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


def legend(node: ltlnode.LTLNode, theme: Optional[Theme] = None) -> list[tuple[str, str]]:
    """The key for *node*: (letter, state it stands for) pairs, theme order.

    The sentence is in words and the answer options are in letters, so the
    student needs the correspondence stated rather than inferred from initials
    ("d" is the document being *open*, not the document).  Only literals the
    formula actually uses are listed, so the key never hints at attributes the
    question does not involve.

    Entries are the plain *state* phrases even for a deontic theme: a letter
    denotes a state of the world, and the obligation belongs to the policy
    being asked about, not to the letter.
    """
    if theme is None:
        theme = THEMES["lights"]
    used = collect_literals(node)
    return [(lit, theme.literals[lit][0]) for lit in theme.literals if lit in used]


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
