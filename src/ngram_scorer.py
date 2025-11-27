"""
N-gram scoring module for selecting the most natural English translations.

This module provides functionality to score candidate English translations
using n-gram language models to select the most natural-sounding option.
The approach is based on common English n-gram patterns to evaluate fluency.
"""

import re
from collections import defaultdict
from functools import lru_cache


# Common English bigrams and trigrams with relative frequencies
# These are curated for temporal/conditional language patterns
# Higher scores indicate more common/natural phrases
BIGRAM_SCORES = {
    # Common temporal phrases
    ('at', 'all'): 10,
    ('all', 'times'): 10,
    ('it', 'is'): 10,
    ('is', 'always'): 9,
    ('always', 'the'): 8,
    ('the', 'case'): 8,
    ('case', 'that'): 8,
    ('is', 'always'): 9,
    ('always', 'true'): 9,
    
    # Eventually phrases
    ('will', 'eventually'): 9,
    ('eventually', 'be'): 8,
    ('be', 'true'): 8,
    
    # Conditional phrases
    ('if', 'then'): 6,  # Less preferred due to redundancy
    ('implies', 'that'): 7,
    
    # "whenever" patterns
    ('whenever', 'then'): 3,  # "whenever X, then Y" is less natural than "whenever X, Y"
    
    # Equivalence phrases
    ('if', 'and'): 8,
    ('and', 'only'): 8,
    ('only', 'if'): 8,
    ('exactly', 'when'): 9,
    ('is', 'equivalent'): 7,
    ('equivalent', 'to'): 7,
    
    # Common verb phrases
    ('will', 'be'): 8,
    ('will', 'hold'): 8,
    ('will', 'occur'): 8,
    ('will', 'happen'): 8,
    ('will', 'always'): 9,
    ('will', 'never'): 9,
    
    # Determiner phrases
    ('the', 'next'): 9,
    ('next', 'step'): 9,
    ('in', 'the'): 9,
    
    # Negation phrases
    ('is', 'not'): 8,
    ('not', 'the'): 7,
    ('never', 'occur'): 8,
    ('never', 'be'): 8,
    
    # Conjunction phrases
    ('both', 'and'): 8,
    ('either', 'or'): 8,
    
    # Until phrases
    ('until', 'eventually'): 7,
    ('continues', 'until'): 8,
}

TRIGRAM_SCORES = {
    # Temporal phrases
    ('at', 'all', 'times'): 15,
    ('it', 'is', 'always'): 12,
    ('is', 'always', 'the'): 11,
    ('always', 'the', 'case'): 11,
    ('the', 'case', 'that'): 11,
    ('is', 'always', 'true'): 13,
    
    # Eventually phrases
    ('will', 'eventually', 'be'): 12,
    ('eventually', 'be', 'true'): 11,
    ('will', 'always', 'be'): 12,
    ('will', 'always', 'hold'): 11,
    
    # Conditional phrases - prefer cleaner forms
    ('if', 'then', 'the'): 4,  # Awkward
    ('whenever', 'then', 'the'): 2,  # Very awkward
    
    # Equivalence phrases
    ('if', 'and', 'only'): 14,
    ('and', 'only', 'if'): 14,
    
    # Next step phrases
    ('in', 'the', 'next'): 13,
    ('the', 'next', 'step'): 13,
    
    # Never phrases
    ('will', 'never', 'occur'): 12,
    ('will', 'never', 'be'): 12,
    
    # Simultaneity phrases
    ('at', 'the', 'same'): 12,
    ('the', 'same', 'time'): 12,
    ('be', 'true', 'simultaneously'): 10,
}


def tokenize(text):
    """
    Tokenize text into lowercase words, preserving quoted literals.
    
    Args:
        text: The text to tokenize
        
    Returns:
        List of tokens (words in lowercase, quoted content preserved)
    """
    # Replace quoted content temporarily
    quoted_pattern = r"'[^']+'"
    quoted_items = re.findall(quoted_pattern, text)
    
    # Replace quoted content with placeholders
    placeholder = "QUOTED_LITERAL"
    text_without_quotes = re.sub(quoted_pattern, placeholder, text)
    
    # Tokenize
    words = re.findall(r'\b\w+\b', text_without_quotes.lower())
    
    # Restore quoted items
    result = []
    quote_idx = 0
    for word in words:
        if word == placeholder.lower():
            result.append(quoted_items[quote_idx] if quote_idx < len(quoted_items) else word)
            quote_idx += 1
        else:
            result.append(word)
    
    return result


def get_bigrams(tokens):
    """Extract bigrams from a list of tokens."""
    return [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]


def get_trigrams(tokens):
    """Extract trigrams from a list of tokens."""
    return [(tokens[i], tokens[i + 1], tokens[i + 2]) for i in range(len(tokens) - 2)]


@lru_cache(maxsize=256)
def score_translation(text):
    """
    Score a translation based on n-gram frequencies.
    
    Higher scores indicate more natural-sounding translations.
    
    Args:
        text: The English translation to score
        
    Returns:
        A numeric score (higher is better)
    """
    tokens = tokenize(text)
    
    if len(tokens) < 2:
        return 0
    
    score = 0
    
    # Score bigrams
    bigrams = get_bigrams(tokens)
    for bigram in bigrams:
        score += BIGRAM_SCORES.get(bigram, 1)  # Default score of 1 for unknown bigrams
    
    # Score trigrams (weighted higher)
    if len(tokens) >= 3:
        trigrams = get_trigrams(tokens)
        for trigram in trigrams:
            score += TRIGRAM_SCORES.get(trigram, 0)  # No default for trigrams
    
    # Normalize by length to avoid favoring longer sentences
    # but give slight preference to moderate length translations
    length_factor = len(tokens)
    if length_factor > 0:
        # Normalize but don't over-penalize longer translations
        score = score / (length_factor ** 0.5)
    
    # Penalize certain patterns that are less natural
    text_lower = text.lower()
    
    # Penalize "whenever X, then Y" pattern (redundant)
    if 'whenever' in text_lower and ', then ' in text_lower:
        score -= 2
    
    # Penalize double commas or awkward punctuation
    if ',,' in text or '. .' in text:
        score -= 5
    
    return score


def select_best_translation(candidates):
    """
    Select the best translation from a list of candidates using n-gram scoring.
    
    Args:
        candidates: List of candidate English translations
        
    Returns:
        The translation with the highest n-gram score
    """
    if not candidates:
        return None
    
    if len(candidates) == 1:
        return candidates[0]
    
    # Score each candidate
    scored = [(candidate, score_translation(candidate)) for candidate in candidates]
    
    # Sort by score (descending) and return the best one
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[0][0]


def get_all_scores(candidates):
    """
    Get scores for all candidates (useful for debugging/testing).
    
    Args:
        candidates: List of candidate English translations
        
    Returns:
        List of (candidate, score) tuples sorted by score descending
    """
    scored = [(candidate, score_translation(candidate)) for candidate in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
