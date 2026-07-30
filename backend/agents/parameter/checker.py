import json
import os
from typing import Dict, List, Any

def load_shapes() -> Dict[str, Any]:
    """
    Dynamically loads the shapes configuration from shapes.json.
    Returns an empty dict if the file is missing.
    """
    config_path = os.path.join(os.path.dirname(__file__), "config", "shapes.json")
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_missing(shape: str, collected_parameters: Dict[str, str]) -> List[str]:
    """
    Determines which required parameters are still missing for a given shape.
    
    Args:
        shape: The detected shape name.
        collected_parameters: The parameters already provided by the user.
        
    Returns:
        A list of string parameter names that are still required.
    """
    shapes_db = load_shapes()
    if shape not in shapes_db:
        return []
        
    required_params = shapes_db[shape].get("required", [])
    missing = [param for param in required_params if param not in collected_parameters]
    return missing

def validate_complete(shape: str, collected_parameters: Dict[str, str]) -> bool:
    """
    Checks if all required parameters for a shape have been collected.
    
    Args:
        shape: The detected shape name.
        collected_parameters: The parameters already provided by the user.
        
    Returns:
        True if all required parameters are present, False otherwise.
    """
    if not shape:
        return False
    missing = check_missing(shape, collected_parameters)
    return len(missing) == 0
