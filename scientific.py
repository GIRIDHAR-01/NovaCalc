"""
NovaCalc - Scientific Functions Engine
File Path: scientific.py
"""

import math

class ScientificEngine:
    """Handles advanced scientific mathematical operations safely."""
    
    @staticmethod
    def calculate_square_root(value_str: str) -> str:
        """Computes the square root of a given numeric string input."""
        try:
            val = float(value_str)
            if val < 0:
                return "Invalid Input"
            res = math.sqrt(val)
            return str(int(res)) if res.is_integer() else str(res)
        except Exception:
            return "Error"

    @staticmethod
    def calculate_square(value_str: str) -> str:
        """Computes the square (x^2) of a given numeric string input."""
        try:
            val = float(value_str)
            res = val ** 2
            return str(int(res)) if res.is_integer() else str(res)
        except Exception:
            return "Error"

    @staticmethod
    def get_pi() -> str:
        """Returns the high-precision value constant of Pi."""
        return str(math.pi)