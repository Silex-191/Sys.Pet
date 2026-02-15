"""
Enhanced Parity Analyzer Module
"""

import re
from typing import Tuple, List, Dict, Any

LARGE_INPUT_THRESHOLD = 10 * 1024

class ParityPattern:
    def __init__(self, name: str, pattern: str, lang: str = "any"):
        self.name = name
        self.pattern = pattern
        self.lang = lang
    
    def matches(self, code: str) -> bool:
        return re.search(self.pattern, code, re.MULTILINE | re.DOTALL) is not None

# Comprehensive parity detection patterns - each found = +20 hunger
ENHANCED_PATTERNS = [
    # 1. Classic modulo checks (any variable name)
    ParityPattern("modulo_even", r"\w+\s*%\s*2\s*==\s*0", "any"),
    ParityPattern("modulo_odd_neq", r"\w+\s*%\s*2\s*!=\s*0", "any"),
    ParityPattern("modulo_odd_eq1", r"\w+\s*%\s*2\s*==\s*1", "any"),
    ParityPattern("modulo_even_neq1", r"\w+\s*%\s*2\s*!=\s*1", "any"),
    ParityPattern("modulo_bare", r"\w+\s*%\s*2(?!\s*[=!])", "any"),  # Just n % 2
    
    # 2. Bitwise AND checks
    ParityPattern("bitwise_and_even", r"\w+\s*&\s*1\s*==\s*0", "any"),
    ParityPattern("bitwise_and_odd", r"\w+\s*&\s*1\s*!=\s*0", "any"),
    ParityPattern("bitwise_and_bare", r"\w+\s*&\s*1(?!\s*[=!])", "any"),  # Just n & 1
    ParityPattern("bitwise_parentheses", r"\(\s*\w+\s*&\s*1\s*\)", "any"),
    ParityPattern("bitwise_not_c", r"!\s*\(\s*\w+\s*&\s*1\s*\)", "c/c++"),
    
    # 3. Python not operator
    ParityPattern("bitwise_not_python", r"not\s+\(\s*\w+\s*&\s*1\s*\)", "python"),
    ParityPattern("bitwise_not_python_bare", r"not\s+\w+\s*&\s*1", "python"),
    
    # 4. String checks (last digit)
    ParityPattern("string_even_check", r"str\s*\(\s*\w+\s*\)\s*\[\s*-1\s*\]\s+in\s+['\"][02468]+['\"]", "python"),
    ParityPattern("string_odd_check", r"str\s*\(\s*\w+\s*\)\s*\[\s*-1\s*\]\s+in\s+['\"][13579]+['\"]", "python"),
    
    # 5. Loop decrement by 2 (cyclic subtraction)
    ParityPattern("loop_decrement_while", r"while\s+\w+\s*>\s*0\s*:?\s*{?\s*\w+\s*-=\s*2", "any"),
    ParityPattern("loop_decrement_alt", r"while\s*\([^)]*>\s*0\)[^}]*-=\s*2", "any"),
    
    # 6. Division checks
    ParityPattern("division_int_check", r"\w+\s*//\s*2\s*\*\s*2\s*==\s*\w+", "any"),
    ParityPattern("division_float_check", r"\w+\s*/\s*2\s*==\s*int\s*\(\s*\w+\s*/\s*2\s*\)", "python"),
    
    # 7. Recursion patterns
    ParityPattern("recursion_parity", r"def\s+(?:is_?)?(?:even|odd)\s*\([^)]*\)\s*:(?:.*\n)*.*return.*(?:is_?)?(?:even|odd)\s*\([^)]*-\s*2", "python"),
    
    # 8. Lambda functions
    ParityPattern("lambda_modulo", r"lambda\s+\w+\s*:\s*\w+\s*%\s*2\s*(?:==|!=)\s*[01]", "python"),
    ParityPattern("lambda_bitwise", r"lambda\s+\w+\s*:\s*\w+\s*&\s*1", "python"),
    
    # 9. C/C++ macros
    ParityPattern("macro_parity", r"#define\s+(?:IS_)?(?:EVEN|ODD)\s*\([^)]*\).*(?:%\s*2|&\s*1)", "c/c++"),
    
    # 10. Ternary operators
    ParityPattern("ternary_modulo", r"\w+\s*%\s*2\s*==\s*0\s*\?", "c/c++"),
    ParityPattern("ternary_bitwise", r"\w+\s*&\s*1\s*\?", "c/c++"),
    
    # 11. List comprehensions with parity
    ParityPattern("list_comp_parity", r"\[.*for.*if.*\w+\s*%\s*2", "python"),
    
    # 12. Function definitions with parity
    ParityPattern("function_parity_c", r"(?:bool|int)\s+(?:is_?)?(?:even|odd)\s*\([^)]*\)\s*{[^}]*%\s*2", "c/c++"),
]

SIMPLE_PATTERNS: List[Tuple[str, int]] = [
    (r"%\s*2\s*==\s*0", 1),
    (r"&\s*1\s*==\s*0", 1),
    (r"not\s*\(.*\s*&\s*1\)", 1),
]

class ParityAnalyzer:
    def __init__(self):
        self.patterns = ENHANCED_PATTERNS
        self.simple_patterns = SIMPLE_PATTERNS
    
    def detect_language(self, code: str) -> str:
        python_indicators = [r"\bdef\s+", r"\bimport\s+", r"\bfrom\s+\w+\s+import\b", r"\bprint\s*\(", r":\s*$"]
        cpp_indicators = [r"#include\s*<", r"\b(?:int|void)\s+main\s*\(", r"\b(?:void|int|char|float|double)\s+\w+\s*\(", r"#define\s+", r"\bstd::", r"cout\s*<<"]
        python_score = sum(1 for pattern in python_indicators if re.search(pattern, code, re.MULTILINE))
        cpp_score = sum(1 for pattern in cpp_indicators if re.search(pattern, code, re.MULTILINE))
        if python_score > cpp_score and python_score > 0:
            return "python"
        elif cpp_score > 0:
            return "c/c++"
        return "unknown"
    
    def analyze_enhanced(self, code: str) -> Tuple[bool, int, List[str]]:
        total_count = 0
        found_pattern = False
        matched_names = []
        lang = self.detect_language(code)
        
        for pattern in self.patterns:
            if pattern.lang != "any" and pattern.lang != lang and lang != "unknown":
                continue
            if pattern.matches(code):
                total_count += 1  # Count each unique pattern once
                found_pattern = True
                matched_names.append(pattern.name)
        
        return found_pattern, total_count, matched_names
    
    def analyze_simple(self, code: str) -> Tuple[bool, int]:
        total_count = 0
        found_pattern = False
        for pattern, _ in self.simple_patterns:
            if re.search(pattern, code):
                total_count += 1  # Count each unique pattern once
                found_pattern = True
        return found_pattern, total_count
    
    def analyze(self, code: str) -> Tuple[bool, int, Dict[str, Any]]:
        code_size = len(code)
        if code_size > LARGE_INPUT_THRESHOLD:
            found, count = self.analyze_simple(code)
            return found, count, {"method": "simple", "reason": "large_input", "size": code_size, "patterns_found": count}
        found, count, patterns = self.analyze_enhanced(code)
        lang = self.detect_language(code)
        return found, count, {"method": "enhanced", "language": lang, "size": code_size, "patterns": patterns, "patterns_found": count}

analyzer = ParityAnalyzer()
