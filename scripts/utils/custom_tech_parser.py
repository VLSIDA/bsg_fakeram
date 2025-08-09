"""
 Tech Parser for yaml tech file
"""
def tech_parser(key: str, yaml_file_path: str):
    try:
        with open(yaml_file_path, 'r') as file:
            lines = file.readlines()
    except Exception:
        return "value not found"
    
    # Simple YAML parser for key-value pairs
    for line in lines:
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            # Remove leading spaces and split on first colon
            clean_line = line.lstrip()
            if clean_line.startswith(key + ':'):
                # Extract value after colon
                value_str = clean_line.split(':', 1)[1].strip()
                # Try to convert to number if possible
                try:
                    if '.' in value_str:
                        return float(value_str)
                    elif any(metal in value_str for metal in ['M', 'm', 'Metal', 'metal']):
                        return str(value_str)
                    else:
                        return int(value_str)
                except ValueError:
                    return value_str
    
    return "value not found"