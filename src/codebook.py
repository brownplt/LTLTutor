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
            return [UntilNode.symbol]
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
    


def collectAllMutationLocations(node, f, path=[]):
    """
    Collect all locations in the tree where mutation f can be applied.
    Returns a list of path tuples where path is a list of directions
    to reach that node from the root.
    """
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


def applyMutationAtPath(node, path, f):
    """
    Apply a mutation function f at a specific path in the tree.
    Path is a list of 'left', 'right', or 'operand' directions.
    """
    if not path:
        # We're at the target node, apply the mutation
        return f(node)
    
    # Navigate to the target location
    direction = path[0]
    remaining_path = path[1:]
    
    if isinstance(node, UnaryOperatorNode) and direction == 'operand':
        child_result = applyMutationAtPath(node.operand, remaining_path, f)
        node.operand = child_result.node
        child_result.node = node
        return child_result
    elif isinstance(node, BinaryOperatorNode) and direction == 'left':
        child_result = applyMutationAtPath(node.left, remaining_path, f)
        node.left = child_result.node
        child_result.node = node
        return child_result
    elif isinstance(node, BinaryOperatorNode) and direction == 'right':
        child_result = applyMutationAtPath(node.right, remaining_path, f)
        node.right = child_result.node
        child_result.node = node
        return child_result
    
    # Should not reach here
    return MutationResult(node)


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
    return applyMutationAtPath(node, path, f)


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
    if isinstance(node, BinaryOperatorNode) and node.operator == UntilNode.symbol:
        x = node.left
        rhs = node.right

        if isinstance(rhs, BinaryOperatorNode) and rhs.operator == AndNode.symbol:
            y = rhs.right

            if isinstance(rhs.left, UnaryOperatorNode) and rhs.left.operator == NotNode.symbol and LTLNode.equiv(rhs.left.operand, x):
                return MutationResult(UntilNode(x, y), MisconceptionCode.ExclusiveU)

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
        rhs = node.right
        new_node = AndNode(node, FinallyNode(rhs))
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
