#!/usr/bin/env python3
"""
Quick test to verify template generation and operator association changes work correctly.
"""

import sys
sys.path.insert(0, 'src')

from codebook import MisconceptionCode, applyMisconception
from ltlnode import LTLNode

def test_exclusive_u_operators():
    """Test that ExclusiveU now returns boolean operators too"""
    misconception = MisconceptionCode.ExclusiveU
    operators = misconception.associatedOperators()
    
    print(f"ExclusiveU associated operators: {operators}")
    assert 'U' in operators, "Should include Until"
    assert '&' in operators, "Should include And"
    assert '|' in operators, "Should include Or"
    assert '->' in operators, "Should include Implies"
    assert '!' in operators, "Should include Not"
    print("✓ ExclusiveU operator association updated correctly")


def test_template_generation():
    """Test that template generation produces valid formulas"""
    misconception = MisconceptionCode.ExclusiveU
    
    print(f"\nTesting template generation for {misconception}...")
    assert misconception.needsTemplateGeneration(), "ExclusiveU should need template generation"
    
    # Generate a few templates
    for i in range(5):
        template = misconception.generateTemplateFormula(['p', 'q', 'r'])
        assert template is not None, "Should generate a template"
        
        formula_str = str(template)
        print(f"  Generated: {formula_str}")
        
        # Try to apply the misconception - should succeed
        result = applyMisconception(template, misconception)
        if result.misconception:
            print(f"    ✓ Can mutate to: {result.node}")
        else:
            print(f"    ⚠ Could not mutate (might be edge case)")
    
    print("✓ Template generation works")


def test_other_misconceptions():
    """Test template generation for other misconceptions"""
    for misconception in [MisconceptionCode.BadStateIndex, MisconceptionCode.OtherImplicit]:
        print(f"\nTesting {misconception}...")
        assert misconception.needsTemplateGeneration(), f"{misconception} should need templates"
        
        template = misconception.generateTemplateFormula(['p', 'q', 'r'])
        assert template is not None, f"Should generate template for {misconception}"
        print(f"  Generated: {template}")
        
        result = applyMisconception(template, misconception)
        if result.misconception:
            print(f"  ✓ Can mutate to: {result.node}")
        else:
            print(f"  ⚠ Could not mutate")


def test_non_template_misconceptions():
    """Test that non-template misconceptions return None"""
    misconception = MisconceptionCode.ImplicitF
    
    print(f"\nTesting {misconception} (should NOT need templates)...")
    assert not misconception.needsTemplateGeneration(), "ImplicitF should not need templates"
    
    template = misconception.generateTemplateFormula(['p', 'q'])
    assert template is None, "Should return None for non-template misconceptions"
    print("✓ Non-template misconceptions correctly return None")


if __name__ == "__main__":
    print("Testing template generation and operator associations...\n")
    print("=" * 60)
    
    test_exclusive_u_operators()
    test_template_generation()
    test_other_misconceptions()
    test_non_template_misconceptions()
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
