"""
Tiered LTL Benchmark Builder with Misconception Distribution Control

Generates LTL-English benchmarks using SPOT's randltl and misconception-based mutants.
Supports controlled distribution over misconception types.
"""

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
import ltltoeng
import spot
import codebook

from sentence_transformers import SentenceTransformer

# Load SBERT model for semantic similarity
print("Loading SBERT model...")
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!")

# LTL formula generation parameters
DEFAULT_WEIGHT = 5
DEFAULT_WEIGHT_TEMPORAL = 7
DEFAULT_LTL_PRIORITIES = {
    "ap": DEFAULT_WEIGHT,
    "F": DEFAULT_WEIGHT_TEMPORAL,
    "G": DEFAULT_WEIGHT_TEMPORAL,
    "X": DEFAULT_WEIGHT_TEMPORAL,
    "U": DEFAULT_WEIGHT_TEMPORAL+3,
    "and": DEFAULT_WEIGHT,
    "or": DEFAULT_WEIGHT,
    "equiv": DEFAULT_WEIGHT,
    "implies": DEFAULT_WEIGHT,
    "not": DEFAULT_WEIGHT,
    "false": 1,
    "true": 1,
    "W": 0,
    "M": 0,
    "xor": 0,
    "R": 0,
}

MIN_FORMULA_TREE_SIZE = 5
MAX_FORMULA_TREE_SIZE = 10


def to_priority_string(d):
    """Convert priority dictionary to SPOT priority string format."""
    return ','.join(f'{k}={v}' for k, v in d.items())


def generate_semantic_mutants(formula_str, max_mutants=10):
    """
    Generate semantic mutants of an LTL formula using misconception-based mutations.
    
    Args:
        formula_str: Original LTL formula string
        max_mutants: Maximum number of mutants to generate
        
    Returns:
        List of tuples: (mutant_formula_string, misconception_code)
    """
    try:
        original_node = parse_ltl_string(formula_str)
    except Exception as e:
        print(f"Error parsing formula '{formula_str}': {e}")
        return []
    
    mutation_results = codebook.getAllApplicableMisconceptions(original_node)
    
    mutants = []
    for result in mutation_results[:max_mutants]:
        try:
            mutant_str = str(result.node)
            misconception_name = result.misconception.name if result.misconception else "Unknown"
            mutants.append((mutant_str, misconception_name))
        except Exception:
            continue
    
    return mutants


def ltl_to_english(formula_str):
    """
    Translate an LTL formula to English using LTL Tutor's translator.
    
    Args:
        formula_str: LTL formula string
        
    Returns:
        English translation string, or None if translation fails
    """
    try:
        node = parse_ltl_string(formula_str)
        raw_english = node.__to_english__()
        english = ltltoeng.finalize_sentence(raw_english)
        return english
    except Exception as e:
        print(f"Error translating '{formula_str}': {e}")
        return None


def compute_sbert_distance(text1, text2, model):
    """
    Compute SBERT Euclidean distance between two texts.
    
    Args:
        text1, text2: Text strings
        model: SentenceTransformer model
        
    Returns:
        Distance score (0 = identical, higher = more different)
    """
    emb1 = model.encode([text1])
    emb2 = model.encode([text2])
    distance = np.linalg.norm(emb1[0] - emb2[0])
    return float(distance)


# Misconception distribution control
def get_all_misconception_types():
    """Get all misconception types from the codebook."""
    from codebook import MisconceptionCode
    return [m.value for m in MisconceptionCode if m != MisconceptionCode.Syntactic]


ALL_MISCONCEPTIONS = get_all_misconception_types()
DEFAULT_MISCONCEPTION_WEIGHTS = {m: 1.0 for m in ALL_MISCONCEPTIONS}


def normalize_weights(weights: dict) -> dict:
    """Normalize weights to sum to 1.0."""
    total = sum(weights.values())
    if total == 0:
        return {k: 1.0/len(weights) for k in weights}
    return {k: v/total for k, v in weights.items()}


def check_misconception_coverage(results_df: pd.DataFrame, target_weights: dict = None):
    """
    Analyze misconception distribution in benchmark results.
    
    Args:
        results_df: DataFrame with 'closest_mutant_misconception' column
        target_weights: Desired distribution (normalized to 1.0)
        
    Returns:
        DataFrame with actual vs target distribution
    """
    misconception_counts = Counter(results_df['closest_mutant_misconception'])
    total = len(results_df)
    
    actual_dist = {m: misconception_counts.get(m, 0) / total for m in ALL_MISCONCEPTIONS}
    
    if target_weights:
        target_dist = normalize_weights(target_weights)
    else:
        target_dist = {m: 1.0/len(ALL_MISCONCEPTIONS) for m in ALL_MISCONCEPTIONS}
    
    comparison = pd.DataFrame({
        'Misconception': ALL_MISCONCEPTIONS,
        'Count': [misconception_counts.get(m, 0) for m in ALL_MISCONCEPTIONS],
        'Actual %': [100 * actual_dist[m] for m in ALL_MISCONCEPTIONS],
        'Target %': [100 * target_dist[m] for m in ALL_MISCONCEPTIONS],
        'Deviation': [100 * (actual_dist[m] - target_dist[m]) for m in ALL_MISCONCEPTIONS]
    })
    
    return comparison.sort_values('Count', ascending=False)


def build_tiered_benchmark(n_formulas_per_tier,
                           max_atomic_props=4,
                           max_mutants_per_formula=15,
                           near_eng_threshold=0.2,
                           far_eng_threshold=0.45,
                           min_similarity_threshold=1e-4,
                           misconception_weights=None,
                           seed=42,
                           max_candidates=10000,
                           verbose=True):
    """
    Build benchmarks by collecting candidates with dynamic priority adjustment.
    
    Strategy:
    1. Continuously generate candidate formulas, tracking misconception distribution
    2. Every n_formulas_per_tier candidates, check which misconceptions are under-represented
    3. Boost LTL operator priorities for under-represented misconceptions using associatedOperators()
    4. Stop when either: (a) hit max_candidates, or (b) have enough of each misconception
    5. Select best subset to meet exact target distribution

    Args:
        n_formulas_per_tier: Target number of formulas for EACH tier
        max_atomic_props: Maximum number of atomic propositions
        max_mutants_per_formula: Maximum mutants per formula
        near_eng_threshold: Max distance for closest mutant (paraphrases)
        far_eng_threshold: Min distance for closest mutant (very different)
        min_similarity_threshold: Min distance for closest mutant (reject if below, default 1e-4)
        misconception_weights: Dict mapping misconception names to weights (0-1).
                              Default is uniform distribution. Higher weight = more samples.
                              Set to None to disable distribution control.
        seed: Random seed
        max_candidates: Maximum candidates to try when building pool
        verbose: Print progress messages
        
    Returns:
        Tuple of (near_eng_df, far_eng_df)
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Set up misconception tracking
    use_distribution_control = misconception_weights is not None
    
    if misconception_weights is None:
        misconception_weights = DEFAULT_MISCONCEPTION_WEIGHTS
    
    target_dist = normalize_weights(misconception_weights)
    
    if verbose:
        print(f"Building tiered benchmark:")
        print(f"  Target per tier: {n_formulas_per_tier} formulas")
        print(f"  Near-English: closest mutant distance < {near_eng_threshold}")
        print(f"  Far-English: closest mutant distance > {far_eng_threshold}")
        print(f"  Min similarity: closest mutant distance >= {min_similarity_threshold}")
        print(f"  Misconception distribution: {'uniform' if misconception_weights == DEFAULT_MISCONCEPTION_WEIGHTS else 'custom'}")
        print(f"  Max candidates to try: {max_candidates}\n")
    
    # Phase 1: Generate pool with dynamic priority adjustment
    near_eng_pool = []
    far_eng_pool = []
    seen_formulas = set()
    candidates_tried = 0
    
    current_priorities = DEFAULT_LTL_PRIORITIES.copy()
    next_adjustment_at = n_formulas_per_tier
    
    def get_missing_misconceptions(pool, tier_name):
        """Identify misconceptions that are under-represented in the pool."""
        if not pool:
            return []
        
        misconception_counts = Counter(r['closest_mutant_misconception'] for r in pool)
        missing = []
        
        for misconception in ALL_MISCONCEPTIONS:
            target_count = target_dist[misconception] * n_formulas_per_tier
            actual_count = misconception_counts.get(misconception, 0)
            
            # Consider it missing if we have less than 70% of target
            if actual_count < 0.7 * target_count:
                deficit = target_count - actual_count
                missing.append((misconception, deficit))
        
        # Sort by deficit (most missing first)
        missing.sort(key=lambda x: -x[1])
        return missing
    
    def generate_template_formulas_for_misconceptions(misconceptions_needed, num_templates=5):
        """
        Generate template-based formulas for pattern-specific misconceptions that are missing.
        Similar to ExerciseBuilder.generate_template_formulas but for benchmark building.
        """
        template_formulas = []
        
        # Only generate templates for misconceptions that need them
        from codebook import MisconceptionCode
        
        for misconception_name, deficit in misconceptions_needed:
            # Skip if no deficit (already have enough)
            if deficit <= 0:
                continue
                
            try:
                misconception_enum = MisconceptionCode(misconception_name)
                
                # Only generate if this misconception benefits from templates
                if not misconception_enum.needsTemplateGeneration():
                    continue
                
                # Generate templates proportional to deficit, but cap it
                templates_to_generate = min(num_templates, int(deficit) + 1)
                
                for _ in range(templates_to_generate):
                    node = misconception_enum.generateTemplateFormula(atomic_props=atoms)
                    if node:
                        template_str = str(node)
                        template_formulas.append(template_str)
                        if verbose:
                            print(f"    Generated template for {misconception_name}: {template_str}")
            except Exception as e:
                if verbose:
                    print(f"    Error generating template for {misconception_name}: {e}")
                continue
        
        return template_formulas
    
    def adjust_priorities_for_misconceptions(misconceptions_needed):
        """Boost operator priorities for misconceptions that are needed."""
        if not misconceptions_needed:
            return current_priorities.copy()
        
        new_priorities = DEFAULT_LTL_PRIORITIES.copy()
        
        # For each missing misconception, boost its associated operators
        for misconception_name, _ in misconceptions_needed[:3]:  # Top 3 most needed
            try:
                from codebook import MisconceptionCode
                misconception_enum = MisconceptionCode(misconception_name)
                operators = misconception_enum.associatedOperators()
                
                boost_factor = 3
                for op in operators:
                    if op in new_priorities:
                        new_priorities[op] = new_priorities[op] * boost_factor
                
                if verbose:
                    print(f"    Boosting operators {operators} for {misconception_name}")
            except:
                pass
        
        return new_priorities
    
    def has_enough_for_distribution(pool):
        """Check if pool has enough of each misconception (70% of target)."""
        if len(pool) < n_formulas_per_tier:
            return False
        
        misconception_counts = Counter(r['closest_mutant_misconception'] for r in pool)
        
        for misconception in ALL_MISCONCEPTIONS:
            target_count = target_dist[misconception] * n_formulas_per_tier
            actual_count = misconception_counts.get(misconception, 0)
            if actual_count < 0.7 * target_count:
                return False
        
        return True
    
    atoms = [f'p{i}' for i in range(max_atomic_props)]
    
    if verbose:
        print("Collecting candidates with dynamic priority adjustment...\n")
    
    # Create initial formula iterator
    ltl_priorities_str = to_priority_string(current_priorities)
    formula_iter = spot.randltl(
        atoms,
        seed=seed + candidates_tried,
        tree_size=randint(MIN_FORMULA_TREE_SIZE, MAX_FORMULA_TREE_SIZE),
        ltl_priorities=ltl_priorities_str,
        simplify=3
    )
    
    while candidates_tried < max_candidates:
        # Check if both tiers have enough for distribution
        if use_distribution_control:
            near_enough = has_enough_for_distribution(near_eng_pool)
            far_enough = has_enough_for_distribution(far_eng_pool)
            if near_enough and far_enough:
                if verbose:
                    print(f"\n✓ Both tiers have sufficient distribution. Stopping collection.")
                break
        else:
            # Without distribution control, stop when we have enough candidates
            if len(near_eng_pool) >= n_formulas_per_tier * 2 and len(far_eng_pool) >= n_formulas_per_tier * 2:
                break
        
        # Periodically adjust priorities based on missing misconceptions
        if candidates_tried >= next_adjustment_at and use_distribution_control:
            if verbose:
                print(f"\n--- Checkpoint at {candidates_tried} candidates ---")
                print(f"  Near-English pool: {len(near_eng_pool)} formulas")
                print(f"  Far-English pool: {len(far_eng_pool)} formulas")
            
            # Check what's missing in each tier
            near_missing = get_missing_misconceptions(near_eng_pool, "Near-English")
            far_missing = get_missing_misconceptions(far_eng_pool, "Far-English")
            
            if near_missing or far_missing:
                if verbose:
                    print(f"  Adjusting priorities for missing misconceptions:")
                    if near_missing:
                        print(f"    Near-English needs: {[m for m, _ in near_missing[:3]]}")
                    if far_missing:
                        print(f"    Far-English needs: {[m for m, _ in far_missing[:3]]}")
                
                # Combine missing from both tiers
                all_missing = near_missing + far_missing
                
                # Generate template formulas for pattern-specific misconceptions
                template_formulas = generate_template_formulas_for_misconceptions(all_missing, num_templates=5)
                
                # Process template formulas immediately as candidates
                for template_formula in template_formulas:
                    if template_formula not in seen_formulas:
                        seen_formulas.add(template_formula)
                        # Process this template formula just like regular candidates below
                        # We'll add it to a queue to be processed
                        mutants = generate_semantic_mutants(template_formula, max_mutants=max_mutants_per_formula)
                        if mutants:
                            candidate_english = ltl_to_english(template_formula)
                            if candidate_english:
                                mutant_data = []
                                all_translated = True
                                
                                for mutant_formula, misconception in mutants:
                                    mutant_english = ltl_to_english(mutant_formula)
                                    if not mutant_english:
                                        all_translated = False
                                        break
                                    
                                    distance = compute_sbert_distance(candidate_english, mutant_english, sbert_model)
                                    mutant_data.append({
                                        'formula': mutant_formula,
                                        'misconception': misconception,
                                        'english': mutant_english,
                                        'distance': distance
                                    })
                                
                                if all_translated and mutant_data:
                                    # Find closest mutant
                                    closest = min(mutant_data, key=lambda x: x['distance'])
                                    
                                    # Calculate distances like regular candidates
                                    distances = [m['distance'] for m in mutant_data]
                                    min_distance = min(distances)
                                    max_distance = max(distances)
                                    avg_distance = np.mean(distances)
                                    
                                    # Skip templates where the closest mutant is too similar (nearly identical English)
                                    if min_distance < min_similarity_threshold:
                                        if verbose:
                                            print(f"    Skipping template '{template_formula}' due to too-similar mutant (distance {min_distance:.6f})")
                                        continue
                                    
                                    record = {
                                        'ltl_formula': template_formula,
                                        'english_translation': candidate_english,
                                        'closest_mutant_formula': closest['formula'],
                                        'closest_mutant_english': closest['english'],
                                        'closest_mutant_misconception': closest['misconception'],
                                        'closest_distance': min_distance,
                                        'max_distance': max_distance,
                                        'avg_distance': avg_distance,
                                        'num_mutants': len(mutant_data),
                                        'all_mutants': mutant_data
                                    }
                                    
                                    # Assign to appropriate tier
                                    if min_distance < near_eng_threshold:
                                        near_eng_pool.append(record)
                                    elif min_distance > far_eng_threshold:
                                        far_eng_pool.append(record)
                
                # Also adjust priorities for random generation
                current_priorities = adjust_priorities_for_misconceptions(all_missing)
                
                # Restart formula iterator with new priorities
                ltl_priorities_str = to_priority_string(current_priorities)
                formula_iter = spot.randltl(
                    atoms,
                    seed=seed + candidates_tried,
                    tree_size=randint(MIN_FORMULA_TREE_SIZE, MAX_FORMULA_TREE_SIZE),
                    ltl_priorities=ltl_priorities_str,
                    simplify=3
                )
            
            next_adjustment_at += n_formulas_per_tier
        
        candidate_formula = str(next(formula_iter))
        candidates_tried += 1

        # Filter out formulas with R (Release) or M (Strong Release) operators
        if re.search(r'\bR\b|\bM\b|\bW\b', candidate_formula):
            continue
        
        if candidate_formula in seen_formulas:
            continue
        seen_formulas.add(candidate_formula)
        
        if verbose and candidates_tried % 100 == 0:
            near_coverage = sum(1 for m in ALL_MISCONCEPTIONS 
                               if any(r['closest_mutant_misconception'] == m for r in near_eng_pool))
            far_coverage = sum(1 for m in ALL_MISCONCEPTIONS 
                              if any(r['closest_mutant_misconception'] == m for r in far_eng_pool))
            print(f"  [Near={len(near_eng_pool)} ({near_coverage}/{len(ALL_MISCONCEPTIONS)} types), "
                  f"Far={len(far_eng_pool)} ({far_coverage}/{len(ALL_MISCONCEPTIONS)} types)] "
                  f"Tried {candidates_tried} candidates...")
        
        mutants = generate_semantic_mutants(candidate_formula, max_mutants=max_mutants_per_formula)
        
        if not mutants:
            continue
        
        candidate_english = ltl_to_english(candidate_formula)
        if not candidate_english:
            continue
        
        mutant_data = []
        all_translated = True
        
        for mutant_formula, misconception in mutants:
            mutant_english = ltl_to_english(mutant_formula)
            if not mutant_english:
                all_translated = False
                break
            
            distance = compute_sbert_distance(candidate_english, mutant_english, sbert_model)
            
            mutant_data.append({
                'formula': mutant_formula,
                'misconception': misconception,
                'english': mutant_english,
                'distance': distance
            })
        
        if not all_translated or not mutant_data:
            continue
        
        distances = [m['distance'] for m in mutant_data]
        min_distance = min(distances)
        max_distance = max(distances)
        avg_distance = np.mean(distances)
        
        # Skip formulas where the closest mutant is too similar (nearly identical English)
        if min_distance < min_similarity_threshold:
            print(f"    Skipping formula '{candidate_formula}' due to too-similar mutant (distance {min_distance:.6f})")
            continue
        
        # Determine tier based on closest mutant distance
        is_near_eng = min_distance < near_eng_threshold
        is_far_eng = min_distance > far_eng_threshold
        
        # Skip if in the gap between tiers
        if not is_near_eng and not is_far_eng:
            continue
        
        # Find closest mutants and all qualifying mutants for each tier
        closest_mutants = [m for m in mutant_data if m['distance'] == min_distance]
        
        # Pick one closest mutant (prefer non-OtherImplicit on ties)
        if len(closest_mutants) > 1:
            non_other = [m for m in closest_mutants if m['misconception'] != 'OtherImplicit']
            closest_mutant = non_other[0] if non_other else closest_mutants[0]
        else:
            closest_mutant = closest_mutants[0]
        
        # Create formula record
        formula_record = {
            'ltl_formula': candidate_formula,
            'english_translation': candidate_english,
            'closest_mutant_formula': closest_mutant['formula'],
            'closest_mutant_english': closest_mutant['english'],
            'closest_mutant_misconception': closest_mutant['misconception'],
            'closest_distance': min_distance,
            'max_distance': max_distance,
            'avg_distance': avg_distance,
            'num_mutants': len(mutant_data),
            'all_mutants': mutant_data  # Keep for Phase 2 selection
        }
        
        # Add to appropriate pool (no size limit - collect until distribution is good)
        if is_near_eng:
            near_eng_pool.append(formula_record)
        elif is_far_eng:
            far_eng_pool.append(formula_record)
    
    if verbose:
        print(f"\nCollection Complete:")
        print(f"  Near-English pool: {len(near_eng_pool)} candidates")
        print(f"  Far-English pool: {len(far_eng_pool)} candidates")
        print(f"  Candidates tried: {candidates_tried}\n")
    
    # Phase 2: Select best subset from pool to meet distribution
    if verbose:
        print("Phase 2: Selecting formulas to meet target distribution...")
    
    def select_from_pool(pool, target_count, tier_name):
        """Select formulas from pool to meet target distribution."""
        if not use_distribution_control:
            # Without distribution control, just take the closest ones
            pool_sorted = sorted(pool, key=lambda x: x['closest_distance'])
            selected = pool_sorted[:target_count]
            return selected
        
        # With distribution control, use greedy selection
        selected = []
        remaining = pool.copy()
        misconception_counts = Counter()
        
        for _ in range(target_count):
            if not remaining:
                break
            
            best_candidate = None
            best_score = -float('inf')
            
            for candidate in remaining:
                misconception = candidate['closest_mutant_misconception']
                
                # Calculate how under-represented this misconception currently is
                current_prop = misconception_counts[misconception] / len(selected) if len(selected) > 0 else 0
                target_prop = target_dist.get(misconception, 0)
                under_represented = target_prop - current_prop
                
                # Score = how much this helps distribution - distance penalty
                # Prefer under-represented misconceptions, but also prefer closer distances
                score = under_represented * 10 - candidate['closest_distance']
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                misconception_counts[best_candidate['closest_mutant_misconception']] += 1
                remaining.remove(best_candidate)
        
        if verbose:
            print(f"  {tier_name}: Selected {len(selected)}/{target_count} formulas")
            coverage = sum(1 for m in ALL_MISCONCEPTIONS if misconception_counts[m] > 0)
            print(f"    Misconception coverage: {coverage}/{len(ALL_MISCONCEPTIONS)}")
        
        return selected
    
    near_eng_selected = select_from_pool(near_eng_pool, n_formulas_per_tier, "Near-English")
    far_eng_selected = select_from_pool(far_eng_pool, n_formulas_per_tier, "Far-English")
    
    # Remove the all_mutants field before creating DataFrame
    for record in near_eng_selected:
        del record['all_mutants']
    for record in far_eng_selected:
        del record['all_mutants']
    
    near_eng_df = pd.DataFrame(near_eng_selected)
    far_eng_df = pd.DataFrame(far_eng_selected)
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Tiered Benchmark Complete!")
        print(f"  Near-English: {len(near_eng_df)}/{n_formulas_per_tier} formulas")
        print(f"  Far-English: {len(far_eng_df)}/{n_formulas_per_tier} formulas")
        print(f"  Candidates tried: {candidates_tried}")
        
        if len(near_eng_df) < n_formulas_per_tier:
            print(f"  WARNING: Near-English only has {len(near_eng_df)}/{n_formulas_per_tier} formulas")
        if len(far_eng_df) < n_formulas_per_tier:
            print(f"  WARNING: Far-English only has {len(far_eng_df)}/{n_formulas_per_tier} formulas")
        
        # Print misconception distribution
        print(f"\n{'='*80}")
        print("MISCONCEPTION DISTRIBUTION")
        print(f"{'='*80}")
        if len(near_eng_df) > 0:
            print("\nNear-English:")
            print(check_misconception_coverage(near_eng_df, misconception_weights))
        if len(far_eng_df) > 0:
            print("\nFar-English:")
            print(check_misconception_coverage(far_eng_df, misconception_weights))
        print(f"{'='*80}")
    
    return near_eng_df, far_eng_df


def main():
    """Command-line interface for benchmark generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate tiered LTL-English benchmark")
    parser.add_argument("--n-per-tier", type=int, default=100, help="Target formulas per tier")
    parser.add_argument("--near-eng-threshold", type=float, default=0.2, help="Near-English distance threshold")
    parser.add_argument("--far-eng-threshold", type=float, default=0.45, help="Far-English distance threshold")
    parser.add_argument("--min-similarity-threshold", type=float, default=1e-4, help="Minimum similarity threshold (reject if below)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-candidates", type=int, default=5000, help="Max candidates to try")
    parser.add_argument("--output-prefix", default="ltl_benchmark", help="Output file prefix")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--max-atomic-props", type=int, default=3, help="Maximum number of atomic propositions")
    
    args = parser.parse_args()
    
    near_eng, far_eng = build_tiered_benchmark(
        n_formulas_per_tier=args.n_per_tier,
        near_eng_threshold=args.near_eng_threshold,
        far_eng_threshold=args.far_eng_threshold,
        min_similarity_threshold=args.min_similarity_threshold,
        seed=args.seed,
        max_atomic_props=args.max_atomic_props,
        max_candidates=args.max_candidates,
        verbose=not args.quiet,
        misconception_weights=DEFAULT_MISCONCEPTION_WEIGHTS
    )
    
    # Save results
    near_eng_path = f"{args.output_prefix}_near_eng.csv"
    far_eng_path = f"{args.output_prefix}_far_eng.csv"
    
    near_eng.to_csv(near_eng_path, index=False)
    far_eng.to_csv(far_eng_path, index=False)
    
    print(f"\nSaved:")
    print(f"  Near-English: {near_eng_path}")
    print(f"  Far-English: {far_eng_path}")


if __name__ == "__main__":
    main()
