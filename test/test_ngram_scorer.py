import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ngram_scorer import (
    tokenize,
    get_bigrams,
    get_trigrams,
    score_translation,
    select_best_translation,
    get_all_scores,
)


class TestTokenize(unittest.TestCase):
    """Test the tokenize function"""
    
    def test_simple_tokenize(self):
        """Simple text should tokenize into words"""
        tokens = tokenize("hello world")
        self.assertEqual(tokens, ["hello", "world"])
    
    def test_tokenize_preserves_quoted(self):
        """Quoted content should be preserved"""
        tokens = tokenize("if 'p', then 'q'")
        self.assertIn("'p'", tokens)
        self.assertIn("'q'", tokens)
    
    def test_tokenize_lowercase(self):
        """Non-quoted text should be lowercased"""
        tokens = tokenize("It Is ALWAYS the case")
        self.assertIn("it", tokens)
        self.assertIn("is", tokens)
        self.assertIn("always", tokens)
    
    def test_tokenize_empty_string(self):
        """Empty string should return empty list"""
        tokens = tokenize("")
        self.assertEqual(tokens, [])
    
    def test_tokenize_multiple_quoted(self):
        """Multiple quoted literals should all be preserved"""
        tokens = tokenize("'p' if and only if 'q'")
        self.assertEqual(tokens.count("'p'"), 1)
        self.assertEqual(tokens.count("'q'"), 1)


class TestNgrams(unittest.TestCase):
    """Test n-gram extraction functions"""
    
    def test_bigrams(self):
        """Bigrams should extract consecutive pairs"""
        tokens = ["a", "b", "c"]
        bigrams = get_bigrams(tokens)
        self.assertEqual(bigrams, [("a", "b"), ("b", "c")])
    
    def test_trigrams(self):
        """Trigrams should extract consecutive triples"""
        tokens = ["a", "b", "c", "d"]
        trigrams = get_trigrams(tokens)
        self.assertEqual(trigrams, [("a", "b", "c"), ("b", "c", "d")])
    
    def test_bigrams_short_input(self):
        """Single token should return empty bigrams"""
        tokens = ["a"]
        bigrams = get_bigrams(tokens)
        self.assertEqual(bigrams, [])


class TestScoreTranslation(unittest.TestCase):
    """Test the score_translation function"""
    
    def test_common_phrase_scores_higher(self):
        """Common phrases should score higher"""
        # "at all times" is a common phrase
        score1 = score_translation("at all times, 'p'")
        # Single token should score lower
        score2 = score_translation("'p'")
        
        self.assertGreater(score1, score2)
    
    def test_if_and_only_if_scores_high(self):
        """'if and only if' is a common phrase and should score high"""
        score = score_translation("'p' if and only if 'q'")
        self.assertGreater(score, 0)
    
    def test_penalty_for_whenever_then(self):
        """'whenever X, then Y' should score lower than 'if X, then Y'"""
        score_whenever = score_translation("whenever 'p', then 'q'")
        score_if = score_translation("if 'p', then 'q'")
        
        self.assertLess(score_whenever, score_if)


class TestSelectBestTranslation(unittest.TestCase):
    """Test the select_best_translation function"""
    
    def test_empty_list_returns_none(self):
        """Empty list should return None"""
        result = select_best_translation([])
        self.assertIsNone(result)
    
    def test_single_item_returns_it(self):
        """Single item list should return that item"""
        result = select_best_translation(["hello"])
        self.assertEqual(result, "hello")
    
    def test_selects_highest_scored(self):
        """Should select the highest-scored translation"""
        candidates = [
            "'p' if and only if 'q'",  # Should be highest due to common phrase
            "'p' exactly when 'q'",
            "'p' is equivalent to 'q'"
        ]
        result = select_best_translation(candidates)
        self.assertEqual(result, "'p' if and only if 'q'")
    
    def test_globally_pattern_selection(self):
        """Should prefer 'It is always the case that' pattern"""
        candidates = [
            "It is always the case that 'p'",
            "At all times, 'p'",
            "'p' is always true"
        ]
        result = select_best_translation(candidates)
        # This should be the highest scored
        self.assertEqual(result, "It is always the case that 'p'")
    
    def test_implication_pattern_selection(self):
        """Should prefer 'If X, then Y' over 'Whenever X, then Y'"""
        candidates = [
            "If 'p', then 'q'",
            "'p' implies 'q'",
            "Whenever 'p', then 'q'"
        ]
        result = select_best_translation(candidates)
        # 'Whenever X, then Y' is penalized, so either of the first two should be selected
        self.assertNotEqual(result, "Whenever 'p', then 'q'")


class TestGetAllScores(unittest.TestCase):
    """Test the get_all_scores function"""
    
    def test_returns_sorted_scores(self):
        """Should return scores sorted by descending order"""
        candidates = ["'p'", "at all times, 'p'"]
        scores = get_all_scores(candidates)
        
        # First item should have higher score
        self.assertGreaterEqual(scores[0][1], scores[1][1])
    
    def test_all_candidates_included(self):
        """All candidates should be in the result"""
        candidates = ["a", "b", "c"]
        scores = get_all_scores(candidates)
        
        result_texts = [s[0] for s in scores]
        for c in candidates:
            self.assertIn(c, result_texts)


if __name__ == "__main__":
    unittest.main()
