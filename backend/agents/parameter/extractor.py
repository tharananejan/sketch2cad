import re
from typing import Optional, Dict, Tuple, List
from .checker import load_shapes

def extract_shape(text: str) -> Optional[str]:
    """
    Identifies the shape from natural language text.
    Returns the shape name (e.g., 'cube', 'sphere') if found, else None.
    """
    shapes_db = load_shapes()
    text_lower = text.lower()
    
    for shape in shapes_db.keys():
        # Look for the shape name as a whole word
        if re.search(r'\b' + re.escape(shape) + r'\b', text_lower):
            return shape
            
    return None

def normalize_english_parameters(text: str) -> str:
    """
    Converts English number words and unit misspellings to digits and standard abbreviations.
    Example: 'twenty five milimeters' -> '25 mm'
    """
    valid_number_words = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "million": 1000000, "billion": 1000000000
    }
    unit_map = {
        "milimeters": "mm",
        "millimeters": "mm",
        "milimeter": "mm",
        "millimeter": "mm",
        "centimeters": "cm",
        "centimeter": "cm",
        "meters": "m",
        "meter": "m",
        "inches": "in",
        "inch": "in"
    }
    
    words = text.replace(",", "").replace(".", " . ").split()
    words = [unit_map.get(w.lower(), w) for w in words]
    
    processed_words = []
    current_number_words = []
    
    def convert_words_to_num(word_list):
        try:
            from word2number import w2n
            return str(w2n.word_to_num(" ".join(word_list)))
        except (ImportError, ValueError):
            # Fallback simple converter
            total = 0
            current = 0
            for w in word_list:
                if w == "point":
                    continue
                val = valid_number_words.get(w.lower())
                if val is not None:
                    if val >= 100:
                        if current == 0: current = 1
                        current *= val
                        if val >= 1000:
                            total += current
                            current = 0
                    else:
                        current += val
            final_val = total + current
            if final_val > 0 or (final_val == 0 and "zero" in word_list):
                return str(final_val)
            return " ".join(word_list)
            
    for word in words:
        if word.lower() in valid_number_words or word.lower() == "point":
            current_number_words.append(word)
        else:
            if current_number_words:
                processed_words.append(convert_words_to_num(current_number_words))
                current_number_words = []
            processed_words.append(word)
            
    if current_number_words:
        processed_words.append(convert_words_to_num(current_number_words))
            
    return " ".join(processed_words).replace(" . ", ".")

def extract_parameters(text: str, missing_params: List[str]) -> Dict[str, str]:
    """
    Extracts parameter values (like '20 mm' or '15.5cm') from text
    and maps them to the missing parameters.
    
    This uses a basic regex strategy, assigning found numeric values
    (with optional units) to the missing parameters in order.
    It also validates that the values are realistic and the units are supported.
    """
    text = normalize_english_parameters(text)
    extracted = {}
    
    # Regex to find numbers optionally followed by any letters
    # Matches: 20, 20.5, 20mm, 20 mm, 20kg
    pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?'
    matches = list(re.finditer(pattern, text.lower()))
    
    valid_units = {"mm", "cm", "m", "in", "inch"}
    
    missing_index = 0
    for match in matches:
        if missing_index < len(missing_params):
            val_str = match.group(1)
            unit_str = match.group(2)
            
            try:
                val_float = float(val_str)
            except ValueError:
                continue
                
            if val_float <= 0:
                raise ValueError("Values must be greater than 0.")
            if val_float > 100000:
                raise ValueError(f"Value {val_float} is too large. Please keep values realistic.")
                
            if unit_str and unit_str not in valid_units:
                raise ValueError(f"Invalid unit '{unit_str}'. Please use mm, cm, or m.")
                
            # Default to mm if unit is not specified
            unit = unit_str if unit_str else "mm" 
            
            param_name = missing_params[missing_index]
            extracted[param_name] = f"{val_str} {unit}"
            missing_index += 1
            
    return extracted
