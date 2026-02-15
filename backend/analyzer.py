"""
Enhanced Parity Analyzer Module
Provides fast, token-based analysis for C/C++/Python parity detection
"""

import re
from typing import Tuple, List, Dict

# Size threshold for fallback to simpler analysis (10KB)
LARGE_INPUT_THRESHOLD = 10 * 1024

# ===== ENHANCED PATTERNS =====
# Token-based patterns for more accurate detection

class ParityPattern:
    """Represents a parity detection pattern with its XP reward"""
    def __init__(self, name: str, pattern: str, xp: int, lang: str = "any"):
        self.name = name
        self.pattern = pattern
        self.xp = xp
        self.lang = lang  # "python", "c/c++", or "any"
    
    def matches(self, code: str) -> bool:
        """Check if pattern matches in code"""
        return re.search(self.pattern, code, re.MULTILINE | re.DOTALL) is not None


# Enhanced pattern database
ENHANCED_PATTERNS = [
    # ===== CLASSIC MODULO PATTERNS =====
    ParityPattern(
        "modulo_check",
        r"(?:num|n|x|val|value|number)\s*%\s*2\s*(?:==|!=)\s*[01]",
        10,
        "any"
    ),
    
    # ===== BITWISE PATTERNS =====
    ParityPattern(
        "bitwise_and",
        r"(?:num|n|x|val|value|number)\s*&\s*1\s*(?:==|!=)\s*[01]|\(\s*(?:num|n|x|val|value|number)\s*&\s*1\s*\)\s*(?:==|!=)\s*[01]",
        20,
        "any"
    ),
    ParityPattern(
        "bitwise_not_python",
        r"not\s+(?:\()?(?:num|n|x|val|value|number)\s*&\s*1",
        30,
        "python"
    ),
    
    # ===== PYTHON-SPECIFIC PATTERNS =====
    ParityPattern(
        "string_slice_check",
        r"str\s*\(\s*(?:num|n|x|val|value|number)\s*\)\s*\[\s*-1\s*\]\s+in\s+['\"][02468]+['\"]",
        50,
        "python"
    ),
    ParityPattern(
        "lambda_parity",
        r"lambda\s+(?:num|n|x):\s*(?:num|n|x)\s*%\s*2\s*(?:==|!=)\s*[01]",
        35,
        "python"
    ),
    ParityPattern(
        "list_comprehension_parity",
        r"\[.*for.*if.*%\s*2\s*(?:==|!=)\s*[01].*\]",
        40,
        "python"
    ),
    
    # ===== C/C++ SPECIFIC PATTERNS =====
    ParityPattern(
        "function_with_modulo",
        r"(?:bool|int)\s+(?:is_?)?(?:even|odd)\s*\([^)]*\)\s*{[^}]*%\s*2",
        45,
        "c/c++"
    ),
    ParityPattern(
        "ternary_parity",
        r"\?\s*[^:]+:\s*[^;]+\s*(?:%\s*2|&\s*1)",
        25,
        "c/c++"
    ),
    ParityPattern(
        "macro_parity",
        r"#define\s+(?:IS_)?(?:EVEN|ODD)\s*\([^)]*\).*(?:%\s*2|&\s*1)",
        55,
        "c/c++"
    ),
    
    # ===== ADVANCED PATTERNS =====
    ParityPattern(
        "loop_decrement",
        r"while\s*\([^)]*>\s*0\)[^}]*(?:-=\s*2|n\s*-\s*2)",
        100,
        "any"
    ),
    ParityPattern(
        "recursion_parity",
        r"def\s+(?:is_?)?(?:even|odd)[^:]*:\s*(?:.*\n)*.*return.*(?:is_?)?(?:even|odd)\([^)]*-\s*2",
        80,
        "python"
    ),
]

# Simplified regex patterns for large inputs (fallback)
SIMPLE_PATTERNS: List[Tuple[str, int]] = [
    (r"%\s*2\s*==\s*0", 10),  # Classic modulo
    (r"&\s*1\s*==\s*0", 20),  # Bitwise
    (r"not\s*\(.*\s*&\s*1\)", 30),  # Pythonic bitwise
]


class ParityAnalyzer:
    """Enhanced parity detection analyzer"""
    
    def __init__(self):
        self.patterns = ENHANCED_PATTERNS
        self.simple_patterns = SIMPLE_PATTERNS
    
    def detect_language(self, code: str) -> str:
        """
        Detect programming language from code content
        Returns: "python", "c/c++", or "unknown"
        """
        # Python indicators
        python_indicators = [
            r"\bdef\s+",
            r"\bimport\s+",
            r"\bfrom\s+\w+\s+import\b",
            r"\bprint\s*\(",
            r":\s*$",  # Colon at end of line (common in Python)
        ]
        
        # C/C++ indicators
        cpp_indicators = [
            r"#include\s*<",
            r"\bint\s+main\s*\(",
            r"\b(?:void|int|char|float|double)\s+\w+\s*\(",
            r"#define\s+",
            r"\bstd::",
            r"cout\s*<<",
        ]
        
        python_score = sum(1 for pattern in python_indicators if re.search(pattern, code, re.MULTILINE))
        cpp_score = sum(1 for pattern in cpp_indicators if re.search(pattern, code, re.MULTILINE))
        
        if python_score > cpp_score and python_score > 0:
            return "python"
        elif cpp_score > 0:
            return "c/c++"
        return "unknown"
    
    def analyze_enhanced(self, code: str) -> Tuple[bool, int, List[str]]:
        """
        Enhanced analysis using token-based patterns
        Returns: (found_pattern, total_xp, matched_pattern_names)
        """
        total_xp = 0
        found_pattern = False
        matched_names = []
        
        # Detect language for better pattern matching
        lang = self.detect_language(code)
        
        for pattern in self.patterns:
            # Skip language-specific patterns if they don't match
            if pattern.lang != "any" and pattern.lang != lang and lang != "unknown":
                continue
            
            if pattern.matches(code):
                total_xp += pattern.xp
                found_pattern = True
                matched_names.append(pattern.name)
        
        return found_pattern, total_xp, matched_names
    
    def analyze_simple(self, code: str) -> Tuple[bool, int]:
        """
        Simple regex-based analysis for large inputs
        Returns: (found_pattern, total_xp)
        """
        total_xp = 0
        found_pattern = False
        
        for pattern, xp_reward in self.simple_patterns:
            if re.search(pattern, code):
                total_xp += xp_reward
                found_pattern = True
        
        return found_pattern, total_xp
    
    def analyze(self, code: str) -> Tuple[bool, int, Dict[str, any]]:
        """
        Main analysis entry point with automatic fallback
        Returns: (found_pattern, total_xp, metadata)
        """
        code_size = len(code)
        
        # Use simple analysis for large inputs
        if code_size > LARGE_INPUT_THRESHOLD:
            found, xp = self.analyze_simple(code)
            return found, xp, {
                "method": "simple",
                "reason": "large_input",
                "size": code_size,
                "patterns": []
            }
        
        # Use enhanced analysis for normal inputs
        found, xp, patterns = self.analyze_enhanced(code)
        lang = self.detect_language(code)
        
        return found, xp, {
            "method": "enhanced",
            "language": lang,
            "size": code_size,
            "patterns": patterns
        }


# Global analyzer instance
analyzer = ParityAnalyzer()
