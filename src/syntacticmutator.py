from ltlnode import *
import copy
import random


def applyRandomMutationNotEquivalentTo(node, notEquivalentToNodes, maxAttempts = 100):
    # Ensures that the mutated node is not equivalent to any of the nodes in the list
    mutated_node = applyRandomMutation(node)

    while isEquivalentToAny(mutated_node, notEquivalentToNodes) and maxAttempts > 0:
        maxAttempts -= 1
        mutated_node = applyRandomMutation(node)


    if isEquivalentToAny(mutated_node, notEquivalentToNodes):
        return None

    return mutated_node


def applyRandomMutation(o_node):

    node = copy.deepcopy(o_node)

    """Apply a random mutation to a random subtree of the tree rooted at `node`."""
    # Choose a random subtree from the tree, and apply a random mutation to it
    # Then replace the subtree with the mutated subtree
    subtree = chooseRandomSubtree(node)

    parent = findParentNode(node, subtree)
    if parent is None:
        return applyRandomMutationAtRoot(node)
    else:
        new_child = applyRandomMutationAtRoot(subtree)

        ## If the parent is a UnaryOperatorNode
        if isinstance(parent, UnaryOperatorNode):
            parent.child = new_child
        elif isinstance(parent, BinaryOperatorNode) and parent.left == subtree:
            parent.left = new_child
        elif isinstance(parent, BinaryOperatorNode) and subtree:
            parent.right = new_child
        else:
            return applyRandomMutationAtRoot(node)
    return node




def findParentNode(root, node):
    if root == node:
        return None

    if isinstance(root, UnaryOperatorNode):
        if root.child == node:
            return root
        else:
            return findParentNode(root.child, node)
    elif isinstance(root, BinaryOperatorNode):
        if root.left == node or root.right == node:
            return root
        else:
            left = findParentNode(root.left, node)
            if left is not None:
                return left
            else:
                return findParentNode(root.right, node)
    return None


def isEquivalentToAny(node, nodes):
        
        # Checks if the node is equivalent to any of the nodes in the list
        # Returns True if it is, False otherwise
    
        for n in nodes:
            if node.isEquivalentTo(n):
                return True
    
        return False



def collectNodes(node):
    """Recursively collect all nodes in the tree."""
    nodes = [node]
    
    if isinstance(node, UnaryOperatorNode):
        nodes.extend(collectNodes(node.child))
    elif isinstance(node, BinaryOperatorNode):
        nodes.extend(collectNodes(node.left))
        nodes.extend(collectNodes(node.right))
    
    return nodes

def chooseRandomSubtree(node):
    """Choose a random subtree from the tree rooted at `node`."""
    all_nodes = collectNodes(node)
    return random.choice(all_nodes)



def applyRandomMutationAtRoot(node):
    """Apply a random mutation to the root of the tree."""
    ## TODO:    ## Replace a Literal with another Literal



    if isinstance(node, BinaryOperatorNode):
        possible_mutations = [changeBinaryOperator, swapOperands]
    elif isinstance(node, UnaryOperatorNode):
        possible_mutations = [changeUnaryOperator]
    else:
        return node
    
    # Choose a random mutation from the list of possible mutations
    mutation = random.choice(possible_mutations)
    return mutation(node)

def swapOperands(node : BinaryOperatorNode):

    ## Ensure that the new class is of the correct typesss

    # Swaps the operands of a Binary Operator Node
    return node.__class__(node.right, node.left)

def changeBinaryOperator(node : BinaryOperatorNode):
        
        # Get the current operator
        currentOperator = node.operator
    
        ## Get all classes that inherit from BinaryOperatorNode
        binopclasses = BinaryOperatorNode.__subclasses__()
        candidatebinops = [c.operator for c in binopclasses if c.operator != currentOperator]
    
        # Choose a random operator from the list of candidate operators
        newOperator = random.choice(candidatebinops)
    
        # Create a new node with the new operator
        newNode = binopclasses[candidatebinops.index(newOperator)](node.left, node.right)
        return newNode


## I think this works right?
def changeUnaryOperator(node : UnaryOperatorNode):
    
    # Get the current operator
    currentOperator = node.operator


    ## Get all classes that inherit from UnaryOperatorNode
    unopclasses = UnaryOperatorNode.__subclasses__()
    candidateunops = [c.operator for c in unopclasses if c.operator != currentOperator]

    # Choose a random operator from the list of candidate operators
    newOperator = random.choice(candidateunops)

    # Create a new node with the new operator
    newNode = unopclasses[candidateunops.index(newOperator)](node.child)
    return newNode




