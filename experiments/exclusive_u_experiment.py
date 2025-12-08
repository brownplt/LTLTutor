"""Simple experiment to estimate how often random seed formulas contain
ExclusiveU or WeakU misconceptions.

The generator intentionally keeps the grammar lightweight: literals plus a
mix of unary and binary temporal operators. We rely on the existing
`codebook.getAllApplicableMisconceptions` helper to detect whether a formula
contains a site where the ExclusiveU or WeakU mutations can apply.
"""
from __future__ import annotations


import sys
import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
from random import randint
import random

# Add src to path for LTL Tutor imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ltlnode import parse_ltl_string


import os
import random
import sys
from typing import List
import spot


# Local imports
from ltlnode import (
    LiteralNode,
    NotNode,
    FinallyNode,
    GloballyNode,
    NextNode,
    UntilNode,
    AndNode,
    OrNode,
    ImpliesNode,
    LTLNode,
)
import codebook

ATOMS = ["a", "b", "c", "p", "q", "r", "x", "y", "z"]


def random_literal() -> LiteralNode:
    return LiteralNode(random.choice(ATOMS))


def random_formula(depth: int, max_depth: int) -> LTLNode:
    """Generate a random LTL formula as an AST.

    The generator balances literals, unary operators, and binary operators.
    Depth is capped to avoid runaway recursion.
    """
    if depth >= max_depth:
        return random_literal()

    roll = random.random()
    if roll < 0.25:
        return random_literal()
    if roll < 0.50:
        op = random.choice([NotNode, FinallyNode, GloballyNode, NextNode])
        return op(random_formula(depth + 1, max_depth))

    op = random.choice([AndNode, OrNode, ImpliesNode, UntilNode])
    return op(random_formula(depth + 1, max_depth), random_formula(depth + 1, max_depth))


def has_misconception(node: LTLNode, code: codebook.MisconceptionCode) -> bool:
    mutations = codebook.getAllApplicableMisconceptions(node)
    return any(m.misconception == code for m in mutations)


def run_experiment(num_formulas: int = 100, seed: int = 42, max_depth: int = 3) -> None:
    random.seed(seed)
    formulas: List[LTLNode] = [random_formula(0, max_depth) for _ in range(num_formulas)]

    exclusive_hits = []
    weak_hits = []

    for formula in formulas:

        formula = parse_ltl_string("x U (!x & y)")

        if has_misconception(formula, codebook.MisconceptionCode.ExclusiveU):
            exclusive_hits.append(str(formula))
        if has_misconception(formula, codebook.MisconceptionCode.WeakU):
            weak_hits.append(str(formula))



    print(f"Generated {num_formulas} formulas (seed={seed}, max_depth={max_depth})")
    print(f"ExclusiveU-applicable: {len(exclusive_hits)}")
    for i, formula in enumerate(exclusive_hits, 1):
        print(f"  Exclusive example {i}: {formula}")

    print(f"WeakU-applicable: {len(weak_hits)}")
    for i, formula in enumerate(weak_hits, 1):
        print(f"  WeakU example {i}: {formula}")


if __name__ == "__main__":
    run_experiment()
