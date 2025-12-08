from enum import Enum
import random
from ltlnode import *
import copy

class MisconceptionCode(Enum):
    Precedence = "Precedence"
    BadStateIndex = "BadStateIndex"
    BadStateQuantification = "BadStateQuantification"
    ExclusiveU = "ExclusiveU"
    ImplicitF = "ImplicitF"
    ImplicitG = "ImplicitG"
    OtherImplicit = "OtherImplicit"
    WeakU = "WeakU"

    ## THIS IS A NON-MISCONCEPTION CODE USED AS A CONTROL ##
    Syntactic = "RandomSyntactic"  ### Should this be here??? Does adding this break anything?

    #### Ignoring these codes since they have no relevance here ###
    #Unlabeled = "Unlabeled"
    #BadProp = "BadProp"
    #ReasonableVariant = "ReasonableVariant"

    @classmethod
    def from_string(cls, code_str):
        if "MisconceptionCode" in code_str:
            code_str = code_str.split(".")[-1]
        try:
            return cls(code_str)
        except ValueError:
            return None

    def needsTemplateGeneration(self):
        """
        Returns True if this misconception benefits from template-based formula generation
        rather than purely random generation, because it requires specific structural patterns.
        """
        return self in [
            MisconceptionCode.ExclusiveU,
            MisconceptionCode.BadStateIndex
        ]

    def generateTemplateFormula(self, atomic_props=None):
        """
        Generate a formula from a template that guarantees this misconception can be applied.
        Returns an LTLNode, or None if template generation is not applicable.
        
        Args:
            atomic_props: List of atomic proposition strings to use. If None, uses ['p', 'q', 'r']
        """
        if atomic_props is None:
            atomic_props = ['p', 'q', 'r']
        
        if not self.needsTemplateGeneration():
            return None
        
        # Helper to get random distinct props
        def get_props(n):
            return random.sample(atomic_props, min(n, len(atomic_props)))

        def build_subformula():
            """
            Build a small subformula to increase structural variety beyond literals.
            Combines a randomly chosen atom with a light unary or binary decoration.
            """
            chosen = get_props(2)
            base = parse_ltl_string(chosen[0])

            if random.random() < 0.55:
                unary_ctor = random.choice([NotNode, FinallyNode, GloballyNode, NextNode])
                base = unary_ctor(base)

            if len(chosen) > 1 and random.random() < 0.55:
                rhs = parse_ltl_string(chosen[1])
                bin_ctor = random.choice([AndNode, OrNode, ImpliesNode])
                base = bin_ctor(base, rhs)

            return base

        if self == MisconceptionCode.ExclusiveU:
            # Generate patterns that ExclusiveU can mutate
            x = build_subformula()
            y = build_subformula()
            
            patterns = [
                # x U (!x & y) - explicit disjointness
                UntilNode(x, AndNode(NotNode(x), y)),
                # x U (x -> y) - implication pattern
                UntilNode(x, ImpliesNode(x, y)),
                # x U (!x | y) - or pattern with negation
                UntilNode(x, OrNode(NotNode(x), y)),
                # (x U y) & G(x -> !y) - global exclusivity constraint
                AndNode(UntilNode(x, y), GloballyNode(ImpliesNode(x, NotNode(y)))),
                # (x U y) & G!(x & y) - globally not both
                AndNode(UntilNode(x, y), GloballyNode(NotNode(AndNode(x, y)))),
            ]
            return random.choice(patterns)
        
        elif self == MisconceptionCode.BadStateIndex:
            # Generate Until/Next patterns with complex RHS
            x = build_subformula()
            y = build_subformula()
            z = build_subformula()
            
            patterns = [
                # x U (y & Fz) - Until with conjunction including Finally
                UntilNode(x, AndNode(y, FinallyNode(z))),
                # x U (y & Gz) - Until with conjunction including Globally
                UntilNode(x, AndNode(y, GloballyNode(z))),
                # X(y & z) - Next with conjunction
                NextNode(AndNode(y, z)),
            ]
            return random.choice(patterns)
        
        return None

    def associatedOperators(self):

        TEMPORAL_OPERATORS = [FinallyNode.symbol, GloballyNode.symbol, UntilNode.symbol, NextNode.symbol]
        k = random.randint(1, len(TEMPORAL_OPERATORS))
        TEMPORAL_SUBSET = random.choices(TEMPORAL_OPERATORS, k=k)

        if self == MisconceptionCode.Precedence:
            ### All binary operators (ie operator.value for every class that inherits from BinaryOperatorNode) ###
            return [cls.symbol for cls in BinaryOperatorNode.__subclasses__()]
        elif self == MisconceptionCode.BadStateIndex:
            ## Tricky -- default to a subset of temporally meaningful operators (U, X, G, F) ##
            return TEMPORAL_SUBSET
        elif self == MisconceptionCode.BadStateQuantification:
            # Applies to responses that mis-use or swap a fan-out operator (F, G, U).
            return [FinallyNode.symbol, GloballyNode.symbol, UntilNode.symbol]
        elif self == MisconceptionCode.ExclusiveU:
            # Boost Until AND the boolean operators that create the patterns we need
            # (e.g., x U (!x & y), x U (x -> y), etc.)
            return [UntilNode.symbol, AndNode.symbol, OrNode.symbol, ImpliesNode.symbol, NotNode.symbol]
        elif self == MisconceptionCode.ImplicitF:
            return [FinallyNode.symbol]
        elif self == MisconceptionCode.ImplicitG:
            return [GloballyNode.symbol]
        elif self == MisconceptionCode.WeakU:
            return [UntilNode.symbol]
        elif self == MisconceptionCode.OtherImplicit:
            ### TODO: This one is tricky, less meaningful...
            ## But ensure that Next and Until are present ##
            return list(set([UntilNode.symbol, NextNode.symbol] + TEMPORAL_SUBSET))
        #### Ignoring these codes since they have no relevance here ###
        else:
            return []



class MutationResult:
    def __init__(self, node, misconception=None):
        self.node = node
        self.misconception = misconception


def applyMisconception(node_orig, misconception):

    ## First copy everything so we don't mess up the original node.
    node = copy.deepcopy(node_orig)


    if misconception == MisconceptionCode.Precedence:
        return applyTilFirst(node, applyPrecedence)
    elif misconception == MisconceptionCode.BadStateIndex:
        return applyTilFirst(node, applyBadStateIndex)
    elif misconception == MisconceptionCode.BadStateQuantification:
        return applyTilFirst(node, applyBadStateQuantification)
    elif misconception == MisconceptionCode.ExclusiveU:
        return applyTilFirst(node, applyExclusiveU)
    elif misconception == MisconceptionCode.ImplicitF:
        return applyTilFirstRandom(node, applyImplicitF)
    elif misconception == MisconceptionCode.ImplicitG:
        return applyTilFirstRandom(node, applyImplicitG)
    elif misconception == MisconceptionCode.WeakU:
        return applyTilFirst(node, applyWeakU)
    elif misconception == MisconceptionCode.OtherImplicit:
        res = applyTilFirst(node, applyImplicitPrefix)
        if not res.misconception:
            return applyTilFirst(node, applyUnderconstraint)
        return res
    # elif misconception in [MisconceptionCode.BadProp, MisconceptionCode.Unlabeled, MisconceptionCode.ReasonableVariant]:
    #     return MutationResult(node)
    else:
        return MutationResult(node)


def getAllApplicableMisconceptions(node):

    formula = str(node)
    def equivalentToOriginal(n) -> bool:
        as_str = str(n)
        return LTLNode.equiv(formula, as_str)

    xs = [        applyMisconception(node, misconception)    for misconception in MisconceptionCode]
    xs = [ x  for x in xs if (x is not None and x.misconception is not None) ]
    
    xs = [ x  for x in xs if not equivalentToOriginal(x.node) ]
    return xs
    


def collectAllMutationLocations(node, f, path=None):
    """
    Collect all locations in the tree where mutation f can be applied.
    Returns a list of path lists where each path is a list of directions
    to reach that node from the root.
    
    Each returned path is an independent copy to avoid aliasing issues.
    """
    if path is None:
        path = []
    
    locations = []
    
    # Try applying the mutation at current node
    res = f(node)
    if res.misconception:
        # Store just the path, we'll apply the mutation later
        locations.append(list(path))
    
    # Recurse into children
    if isinstance(node, UnaryOperatorNode):
        locations.extend(collectAllMutationLocations(node.operand, f, path + ['operand']))
    elif isinstance(node, BinaryOperatorNode):
        locations.extend(collectAllMutationLocations(node.left, f, path + ['left']))
        locations.extend(collectAllMutationLocations(node.right, f, path + ['right']))
    
    return locations


def applyMutationAtPath(node, f, path):
    """
    Apply a mutation function f at a specific path in the tree.
    Path is a list of 'left', 'right', or 'operand' directions.
    
    Note: This function modifies the node tree in-place and uses a pattern
    where child_result.node is reassigned to point to the parent node.
    This is intentional and matches the pattern used in applyTilFirst.
    The caller should pass a deep copy if the original needs to be preserved.
    """
    if not path:
        # We're at the target node, apply the mutation
        return f(node)
    
    # Navigate to the target location
    direction = path[0]
    remaining_path = path[1:]
    
    if isinstance(node, UnaryOperatorNode) and direction == 'operand':
        child_result = applyMutationAtPath(node.operand, f, remaining_path)
        # Thread the result back through the parent: replace child with mutated version,
        # then update result to point to the whole subtree
        node.operand = child_result.node
        child_result.node = node
        return child_result
    elif isinstance(node, BinaryOperatorNode) and direction == 'left':
        child_result = applyMutationAtPath(node.left, f, remaining_path)
        node.left = child_result.node
        child_result.node = node
        return child_result
    elif isinstance(node, BinaryOperatorNode) and direction == 'right':
        child_result = applyMutationAtPath(node.right, f, remaining_path)
        node.right = child_result.node
        child_result.node = node
        return child_result
    
    # Invalid path - this indicates a bug in path generation
    raise ValueError(f"Invalid path: cannot apply direction '{direction}' to node of type {type(node).__name__}")


def applyTilFirstRandom(node, f):
    """
    Apply mutation f to a randomly selected location in the tree where it's applicable.
    This ensures diverse mutations when multiple locations are possible.
    Use this for simple mutations like ImplicitG/ImplicitF where we want to randomly
    select from all possible application sites.
    """
    # Collect all possible mutation locations
    locations = collectAllMutationLocations(node, f)
    
    if not locations:
        return MutationResult(node)
    
    # Randomly select one location
    path = random.choice(locations)
    
    # Apply the mutation at the selected location
    return applyMutationAtPath(node, f, path)


def applyTilFirst(node, f):
    """
    Apply mutation f at the first applicable location found (depth-first search).
    This is the original behavior, used for complex mutations that should be applied
    as a unit at the first matching location.
    """
    res = f(node)
    if res.misconception:
        return res

    if isinstance(node, UnaryOperatorNode):
        res = applyTilFirst(node.operand, f)
        node.operand = res.node
        res.node = node
        return res

    if isinstance(node, BinaryOperatorNode):
        res_left = applyTilFirst(node.left, f)
        res_right = applyTilFirst(node.right, f)

        random_index = random.randint(0, 1)
        choose_left = res_left.misconception and (not res_right.misconception or random_index == 0)
        choose_right = res_right.misconception and (not res_left.misconception or random_index == 1)

        if choose_left:
            node.left = res_left.node
            res_left.node = node
            return res_left
        elif choose_right:
            node.right = res_right.node
            res_right.node = node
            return res_right

    return MutationResult(node)


def applyPrecedence(node):
    if isinstance(node, BinaryOperatorNode):
        if isinstance(node.right, BinaryOperatorNode):
            new_top = node.right
            node.right = new_top.left
            new_top.left = node
            return MutationResult(new_top, MisconceptionCode.Precedence)

    return MutationResult(node)


def applyExclusiveU(node):
    """
    Detect patterns where Until is used with explicit disjointness/exclusivity.
    ExclusiveU misconception: treating "x U y" as if x and y cannot both be true.
    """
    if isinstance(node, BinaryOperatorNode) and node.operator == UntilNode.symbol:
        x = node.left
        rhs = node.right

        # Pattern 1: x U (!x & y) → x U y
        # Student explicitly enforces disjointness
        if isinstance(rhs, BinaryOperatorNode) and rhs.operator == AndNode.symbol:
            y = rhs.right

            if isinstance(rhs.left, UnaryOperatorNode) and rhs.left.operator == NotNode.symbol and LTLNode.equiv(rhs.left.operand, x):
                return MutationResult(UntilNode(x, y), MisconceptionCode.ExclusiveU)
            
            # Pattern 1b: x U (y & !x) → x U y (order swapped)
            if isinstance(rhs.right, UnaryOperatorNode) and rhs.right.operator == NotNode.symbol and LTLNode.equiv(rhs.right.operand, x):
                return MutationResult(UntilNode(x, rhs.left), MisconceptionCode.ExclusiveU)

        # Pattern 2: x U (x -> y) → x U y
        # Student thinks "x U (x implies y)" enforces that y happens after x stops
        if isinstance(rhs, ImpliesNode) and LTLNode.equiv(rhs.left, x):
            return MutationResult(UntilNode(x, rhs.right), MisconceptionCode.ExclusiveU)
        
        # Pattern 3: x U (!x | y) → x U y
        # Student thinks "x U (!x or y)" ensures exclusivity
        if isinstance(rhs, OrNode):
            if isinstance(rhs.left, NotNode) and LTLNode.equiv(rhs.left.operand, x):
                return MutationResult(UntilNode(x, rhs.right), MisconceptionCode.ExclusiveU)
            if isinstance(rhs.right, NotNode) and LTLNode.equiv(rhs.right.operand, x):
                return MutationResult(UntilNode(x, rhs.left), MisconceptionCode.ExclusiveU)

    # Pattern 4: (x U y) & G(x -> !y) → x U y
    # Student adds a global constraint that x and y are mutually exclusive
    if isinstance(node, AndNode):
        left = node.left
        right = node.right
        
        # Check if one side is Until and other is G(x -> !y)
        until_node = None
        constraint_node = None
        
        if isinstance(left, UntilNode) and isinstance(right, GloballyNode):
            until_node = left
            constraint_node = right.operand
        elif isinstance(right, UntilNode) and isinstance(left, GloballyNode):
            until_node = right
            constraint_node = left.operand
        
        if until_node and constraint_node and isinstance(constraint_node, ImpliesNode):
            x = until_node.left
            y = until_node.right
            
            # Check if constraint is x -> !y
            if LTLNode.equiv(constraint_node.left, x):
                if isinstance(constraint_node.right, NotNode) and LTLNode.equiv(constraint_node.right.operand, y):
                    return MutationResult(until_node, MisconceptionCode.ExclusiveU)
            
            # Check if constraint is y -> !x
            if LTLNode.equiv(constraint_node.left, y):
                if isinstance(constraint_node.right, NotNode) and LTLNode.equiv(constraint_node.right.operand, x):
                    return MutationResult(until_node, MisconceptionCode.ExclusiveU)

    # Pattern 5: (x U y) & G!(x & y) → x U y
    # Student adds "globally not both" constraint
    if isinstance(node, AndNode):
        left = node.left
        right = node.right
        
        until_node = None
        constraint_node = None
        
        if isinstance(left, UntilNode) and isinstance(right, GloballyNode):
            until_node = left
            constraint_node = right.operand
        elif isinstance(right, UntilNode) and isinstance(left, GloballyNode):
            until_node = right
            constraint_node = left.operand
        
        if until_node and constraint_node:
            if isinstance(constraint_node, NotNode) and isinstance(constraint_node.operand, AndNode):
                and_node = constraint_node.operand
                x = until_node.left
                y = until_node.right
                
                # Check if it's !(x & y)
                if (LTLNode.equiv(and_node.left, x) and LTLNode.equiv(and_node.right, y)) or \
                   (LTLNode.equiv(and_node.right, x) and LTLNode.equiv(and_node.left, y)):
                    return MutationResult(until_node, MisconceptionCode.ExclusiveU)

    return MutationResult(node)


def applyImplicitG(node):
    if isinstance(node, UnaryOperatorNode) and node.operator == GloballyNode.symbol:
        return MutationResult(node.operand, MisconceptionCode.ImplicitG)

    return MutationResult(node)


def applyImplicitF(node):
    if isinstance(node, UnaryOperatorNode) and node.operator == FinallyNode.symbol:
        return MutationResult(node.operand, MisconceptionCode.ImplicitF)

    return MutationResult(node)


def applyImplicitPrefix(node):
    if isinstance(node, UntilNode):
        lhs = node.left
        rhs = node.right

        if isinstance(lhs, NotNode) and LTLNode.equiv(lhs.operand, rhs):
            return MutationResult(FinallyNode(rhs), MisconceptionCode.OtherImplicit)

        if isinstance(rhs, GloballyNode) and LTLNode.equiv(lhs, rhs.operand):
            return MutationResult(AndNode(lhs, FinallyNode(rhs)), MisconceptionCode.OtherImplicit)

    if isinstance(node, AndNode):
        lhs = node.left
        rhs = node.right

        if isinstance(lhs, FinallyNode) and isinstance(rhs, GloballyNode):
            rhs_operand = rhs.operand
            if isinstance(rhs_operand, ImpliesNode):
                rhs_operand_lhs = rhs_operand.left
                rhs_operand_rhs = rhs_operand.right

                if LTLNode.equiv(lhs.operand, rhs_operand_lhs) and isinstance(rhs_operand_rhs, NextNode) and isinstance(rhs_operand_rhs.operand, GloballyNode) and LTLNode.equiv(rhs_operand_lhs, rhs_operand_rhs.operand.operand):
                    return MutationResult(AndNode(lhs.operand, NextNode(rhs)), MisconceptionCode.OtherImplicit)

    if isinstance(node, NextNode):
        return MutationResult(FinallyNode(node.operand), MisconceptionCode.OtherImplicit)

    return MutationResult(node)




def applyUnderconstraint(node):
    if isinstance(node, BinaryOperatorNode):
        n = random.choice([node.left, node.right])
        return MutationResult(n, MisconceptionCode.OtherImplicit)
    ## TODO: Yes, but this shouldn't remove F / G constraints (these aren't covered by the other code)
    elif isinstance(node, UnaryOperatorNode):
        return MutationResult(node.operand, MisconceptionCode.OtherImplicit)
    else:
        return MutationResult(node)


def applyWeakU(node):
    if isinstance(node, UntilNode):
        lhs = node.left
        # Interpret until as weak-until: RHS may never happen if LHS stays true
        new_node = OrNode(node, GloballyNode(lhs))
        return MutationResult(new_node, MisconceptionCode.WeakU)

    return MutationResult(node)


def applyBadStateQuantification(node):
    if isinstance(node, GloballyNode):
        op = node.operand
        return MutationResult(FinallyNode(op), MisconceptionCode.BadStateQuantification)

    if isinstance(node, FinallyNode):
        op = node.operand
        return MutationResult(GloballyNode(op), MisconceptionCode.BadStateQuantification)

    if isinstance(node, UntilNode):
        lhs = node.left
        rhs = node.right

        new_node = random.choice([
            UntilNode(FinallyNode(lhs), rhs),
            UntilNode(GloballyNode(lhs), rhs),
            UntilNode(lhs, FinallyNode(rhs)),
            UntilNode(lhs, GloballyNode(rhs)),
            UntilNode(rhs, lhs)
        ])
        return MutationResult(new_node, MisconceptionCode.BadStateQuantification)

    return MutationResult(node)


def applyBadStateIndex(node):
    if isinstance(node, UntilNode):
        lhs = node.left
        rhs = node.right

        if isinstance(rhs, AndNode) and isinstance(rhs.right, FinallyNode):
            new_node = AndNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(rhs, AndNode) and isinstance(rhs.right, GloballyNode):
            new_node = AndNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(rhs, OrNode) and isinstance(rhs.right, FinallyNode):
            new_node = OrNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(rhs, OrNode) and isinstance(rhs.right, GloballyNode):
            new_node = OrNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(rhs, ImpliesNode) and isinstance(rhs.right, FinallyNode):
            new_node = ImpliesNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(rhs, ImpliesNode) and isinstance(rhs.right, GloballyNode):
            new_node = ImpliesNode(UntilNode(lhs, rhs.left), rhs.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

    if isinstance(node, NextNode):
        op = node.operand

        if isinstance(op, AndNode):
            new_node = AndNode(NextNode(op.left), op.right)
            return MutationResult(new_node, MisconceptionCode.BadStateIndex)

        if isinstance(op, NextNode):
            x = op.operand
            while isinstance(x, NextNode):
                x = x.operand

            return MutationResult(NextNode(x), MisconceptionCode.BadStateIndex)

    return MutationResult(node)
