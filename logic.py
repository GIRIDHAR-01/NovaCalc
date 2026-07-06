"""
NovaCalc Ultimate - Unified Advanced Math, Matrix, Stats, & Conversion Engine
File Path: logic.py
"""
import math
import re

class CalculatorLogic:
    @staticmethod
    def evaluate_expression(expression: str) -> str:
        try:
            cleaned = expression.strip()
            if not cleaned: 
                return "0"

            # 1. STATISTICS MODE RADAR
            if any(keyword in cleaned.lower() for keyword in ["mean", "median", "variance", "stddev"]):
                return CalculatorLogic._process_statistics(cleaned)

            # 2. MATRIX MODE RADAR
            if "[" in cleaned and any(keyword in cleaned.lower() for keyword in ["det", "trans"]):
                return CalculatorLogic._process_matrix(cleaned)

            # 3. CONVERTER UNIT RADAR
            if "→" in cleaned or "to" in cleaned.lower():
                return CalculatorLogic._process_conversions(cleaned)

            # 4. PROGRAMMER BASE BITWISE ENGINE
            processed = cleaned.replace('AND', '&').replace('OR', '|').replace('XOR', '^').replace('NOT', '~')
            processed = processed.replace('<<', '<<').replace('>>', '>>')

            # Clean Standard Tokens
            processed = processed.replace('×', '*').replace('÷', '/').replace('π', str(math.pi)).replace('e', str(math.e))
            processed = processed.replace('²', '**2').replace('³', '**3').replace('^', '**')
            
            # Safe Function Tracing Matchers
            processed = re.sub(r'sin\(([^)]+)\)', r'math.sin(math.radians(\1))', processed)
            processed = re.sub(r'cos\(([^)]+)\)', r'math.cos(math.radians(\1))', processed)
            processed = re.sub(r'tan\(([^)]+)\)', r'math.tan(math.radians(\1))', processed)
            processed = re.sub(r'asin\(([^)]+)\)', r'math.degrees(math.asin(\1))', processed)
            processed = re.sub(r'acos\(([^)]+)\)', r'math.degrees(math.acos(\1))', processed)
            processed = re.sub(r'atan\(([^)]+)\)', r'math.degrees(math.atan(\1))', processed)
            processed = re.sub(r'log\(([^)]+)\)', r'math.log10(\1)', processed)
            processed = re.sub(r'ln\(([^)]+)\)', r'math.log(\1)', processed)
            processed = re.sub(r'√\(([^)]+)\)', r'math.sqrt(\1)', processed)

            result = eval(processed, {"math": math}, {})
            
            if isinstance(result, float):
                if result.is_integer(): return str(int(result))
                return f"{result:.8f}".rstrip('0').rstrip('.')
            return str(result)
        except Exception:
            return "Syntax Error"

    @staticmethod
    def _process_statistics(target: str) -> str:
        try:
            match = re.match(r'(\w+)\(([^)]+)\)', target.lower())
            if not match: return "Format Error"
            func, data_str = match.groups()
            nums = [float(x.strip()) for x in data_str.split(",") if x.strip()]
            if not nums: return "0"

            if func == "mean":
                return str(sum(nums) / len(nums))
            elif func == "median":
                s = sorted(nums)
                n = len(s)
                return str(s[n//2] if n % 2 != 0 else (s[n//2 - 1] + s[n//2]) / 2)
            elif func == "variance":
                m = sum(nums) / len(nums)
                return str(sum((x - m) ** 2 for x in nums) / len(nums))
            elif func == "stddev":
                m = sum(nums) / len(nums)
                var = sum((x - m) ** 2 for x in nums) / len(nums)
                return f"{math.sqrt(var):.4f}".rstrip('0').rstrip('.')
            return "Unknown Stat Op"
        except Exception:
            return "Stat Error"

    @staticmethod
    def _process_matrix(target: str) -> str:
        try:
            array_match = re.search(r'(\[\[.*\]\])', target)
            if not array_match: return "Matrix Format Error"
            matrix = eval(array_match.group(1))
            
            if "trans" in target.lower():
                return str([list(x) for x in zip(*matrix)])
            elif "det" in target.lower():
                if len(matrix) == 2 and len(matrix[0]) == 2:
                    return str((matrix[0][0] * matrix[1][1]) - (matrix[0][1] * matrix[1][0]))
                return "Supports 2x2 Matrix Det"
            return "Unsupported Matrix Op"
        except Exception:
            return "Matrix Error"

    @staticmethod
    def _process_conversions(target: str) -> str:
        """Parses inputs like '100 m to km' or '25 c to f'."""
        try:
            parts = target.lower().split()
            val = float(parts[0])
            # Temperature conversions
            if "c" in parts[1] and "f" in parts[-1]:
                return str((val * 9/5) + 32)
            if "f" in parts[1] and "c" in parts[-1]:
                return str((val - 32) * 5/9)
            # Length conversions
            if "m" == parts[1] and "km" == parts[-1]:
                return str(val / 1000)
            if "km" == parts[1] and "m" == parts[-1]:
                return str(val * 1000)
            return "Conversion Not Supported Yet"
        except Exception:
            return "Conversion Error"