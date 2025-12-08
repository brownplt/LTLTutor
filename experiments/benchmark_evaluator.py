"""
LLM Benchmark Evaluator for English-to-LTL Translation

Evaluates LLMs (GPT-4, Claude, etc.) on English→LTL translation benchmarks.
Computes standard metrics: exact match, semantic equivalence, syntax validity.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

# Add src to path for LTL parsing and equivalence checking
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ltlnode import parse_ltl_string
from spotutils import areEquivalent
import spot


@dataclass
class EvaluationResult:
    """Results for a single benchmark item."""
    index: int
    english_input: str
    ground_truth_ltl: str
    predicted_ltl: Optional[str]
    raw_response: str
    
    # Metrics
    is_valid_syntax: bool
    is_exact_match: bool
    is_semantically_equivalent: bool
    
    # Error info
    parse_error: Optional[str] = None
    equivalence_error: Optional[str] = None


class LLMEvaluator:
    """Evaluates LLM performance on English→LTL translation."""
    
    def __init__(self, model_name: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize evaluator with specific LLM.
        
        Args:
            model_name: Model identifier (e.g., "gpt-4", "gpt-4-turbo", "claude-3-opus")
            api_key: API key (if None, reads from environment)
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key and "gpt" in model_name.lower():
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize API client
        if "gpt" in model_name.lower():
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        else:
            raise NotImplementedError(f"Model {model_name} not yet supported")
    
    def create_prompt(self, english: str, include_examples: bool = True) -> str:
        """
        Create prompt for English→LTL translation.
        
        Args:
            english: English specification to translate
            include_examples: Whether to include few-shot examples
            
        Returns:
            Formatted prompt string
        """
        system_msg = """You are an expert in Linear Temporal Logic (LTL). 
Your task is to translate English specifications into LTL formulas.

LTL Operators:
- G p: "always p" / "at all times p"
- F p: "eventually p" / "sometime in the future p"
- X p: "in the next step p" / "next p"
- p U q: "p until q"
- p & q: "both p and q"
- p | q: "either p or q"
- ! p: "not p"
- p -> q: "if p then q" / "p implies q"

Return ONLY the LTL formula, nothing else. Use the exact syntax above."""

        if include_examples:
            examples = """
Examples:
English: "Always 'p0'"
LTL: G p0

English: "Eventually, 'p1'"
LTL: F p1

English: "In the next step, 'p2'"
LTL: X p2

English: "Both 'p0' and 'p1'"
LTL: p0 & p1

English: "'p0' until 'p1'"
LTL: p0 U p1

English: "At all times, either 'p0' or eventually, 'p1'"
LTL: G (p0 | F p1)
"""
            system_msg += "\n" + examples
        
        user_msg = f"""Translate this English specification to LTL:

English: "{english}"

LTL:"""
        
        return system_msg, user_msg
    
    def query_llm(self, english: str, temperature: float = 0.0, max_tokens: int = 150) -> str:
        """
        Query LLM for English→LTL translation.
        
        Args:
            english: English specification
            temperature: Sampling temperature (0 = deterministic)
            max_tokens: Maximum response length
            
        Returns:
            Raw LLM response
        """
        system_msg, user_msg = self.create_prompt(english)
        
        if "gpt" in self.model_name.lower():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        
        raise NotImplementedError(f"Model {self.model_name} not supported")
    
    def extract_ltl_formula(self, response: str) -> str:
        """
        Extract LTL formula from LLM response.
        
        Handles cases where LLM adds extra text like "LTL: ..." or explanations.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned LTL formula
        """
        # Remove common prefixes
        response = response.strip()
        prefixes = ["LTL:", "ltl:", "Formula:", "formula:", "Answer:", "answer:"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Take first line if multiline
        lines = response.split('\n')
        formula = lines[0].strip()
        
        # Remove quotes if present
        if formula.startswith('"') and formula.endswith('"'):
            formula = formula[1:-1]
        if formula.startswith("'") and formula.endswith("'"):
            formula = formula[1:-1]
        
        return formula
    
    def evaluate_single(self, english: str, ground_truth: str, index: int) -> EvaluationResult:
        """
        Evaluate LLM on a single benchmark item.
        
        Args:
            english: English input specification
            ground_truth: Ground truth LTL formula
            index: Benchmark item index
            
        Returns:
            EvaluationResult with all metrics
        """
        # Query LLM
        try:
            raw_response = self.query_llm(english)
            predicted = self.extract_ltl_formula(raw_response)
        except Exception as e:
            return EvaluationResult(
                index=index,
                english_input=english,
                ground_truth_ltl=ground_truth,
                predicted_ltl=None,
                raw_response=str(e),
                is_valid_syntax=False,
                is_exact_match=False,
                is_semantically_equivalent=False,
                parse_error=str(e)
            )
        
        # Check syntax validity
        is_valid = False
        parse_error = None
        try:
            parse_ltl_string(predicted)
            is_valid = True
        except Exception as e:
            parse_error = str(e)
        
        # Check exact match
        is_exact = (predicted == ground_truth)
        
        # Check semantic equivalence
        is_equivalent = False
        equiv_error = None
        if is_valid:
            try:
                is_equivalent = areEquivalent(predicted, ground_truth)
            except Exception as e:
                equiv_error = str(e)
        
        return EvaluationResult(
            index=index,
            english_input=english,
            ground_truth_ltl=ground_truth,
            predicted_ltl=predicted,
            raw_response=raw_response,
            is_valid_syntax=is_valid,
            is_exact_match=is_exact,
            is_semantically_equivalent=is_equivalent,
            parse_error=parse_error,
            equivalence_error=equiv_error
        )
    
    def evaluate_benchmark(self, 
                          benchmark_path: str, 
                          output_path: Optional[str] = None,
                          limit: Optional[int] = None) -> pd.DataFrame:
        """
        Evaluate LLM on entire benchmark.
        
        Args:
            benchmark_path: Path to benchmark CSV file
            output_path: Path to save results (optional)
            limit: Maximum number of items to evaluate (for testing)
            
        Returns:
            DataFrame with detailed results
        """
        # Load benchmark
        df = pd.read_csv(benchmark_path)
        
        if limit:
            df = df.head(limit)
        
        print(f"Evaluating {self.model_name} on {len(df)} items from {Path(benchmark_path).name}")
        print(f"{'='*80}")
        
        results = []
        
        for idx, row in df.iterrows():
            english = row['english_translation']
            ground_truth = row['ltl_formula']
            
            print(f"\n[{idx+1}/{len(df)}] Evaluating...")
            print(f"English: {english[:80]}...")
            
            result = self.evaluate_single(english, ground_truth, idx)
            
            print(f"Ground Truth: {ground_truth}")
            print(f"Predicted:    {result.predicted_ltl}")
            print(f"Valid: {result.is_valid_syntax} | Exact: {result.is_exact_match} | Equivalent: {result.is_semantically_equivalent}")
            
            results.append(result)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Convert to DataFrame
        results_df = pd.DataFrame([
            {
                'index': r.index,
                'english_input': r.english_input,
                'ground_truth_ltl': r.ground_truth_ltl,
                'predicted_ltl': r.predicted_ltl,
                'raw_response': r.raw_response,
                'is_valid_syntax': r.is_valid_syntax,
                'is_exact_match': r.is_exact_match,
                'is_semantically_equivalent': r.is_semantically_equivalent,
                'parse_error': r.parse_error,
                'equivalence_error': r.equivalence_error
            }
            for r in results
        ])
        
        # Compute aggregate metrics
        self.print_summary(results_df)
        
        # Save results
        if output_path:
            results_df.to_csv(output_path, index=False)
            print(f"\nResults saved to {output_path}")
        
        return results_df
    
    def print_summary(self, results_df: pd.DataFrame):
        """Print summary statistics."""
        total = len(results_df)
        valid = results_df['is_valid_syntax'].sum()
        exact = results_df['is_exact_match'].sum()
        equivalent = results_df['is_semantically_equivalent'].sum()
        
        print(f"\n{'='*80}")
        print(f"EVALUATION SUMMARY - {self.model_name}")
        print(f"{'='*80}")
        print(f"Total items:              {total}")
        print(f"Valid syntax:             {valid}/{total} ({100*valid/total:.1f}%)")
        print(f"Exact match:              {exact}/{total} ({100*exact/total:.1f}%)")
        print(f"Semantically equivalent:  {equivalent}/{total} ({100*equivalent/total:.1f}%)")
        print(f"{'='*80}")


def main():
    """Run benchmark evaluation from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate LLM on English→LTL benchmark")
    parser.add_argument("benchmark", help="Path to benchmark CSV file")
    parser.add_argument("--model", default="gpt-4", help="Model name (default: gpt-4)")
    parser.add_argument("--output", help="Path to save results CSV")
    parser.add_argument("--limit", type=int, help="Limit number of items (for testing)")
    parser.add_argument("--api-key", help="API key (or set OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Create evaluator
    evaluator = LLMEvaluator(model_name=args.model, api_key=args.api_key)
    
    # Run evaluation
    results = evaluator.evaluate_benchmark(
        benchmark_path=args.benchmark,
        output_path=args.output,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
