from decimal import Decimal, ROUND_HALF_DOWN

################################################################################
# DECIMAL HELPERS
#
# Purpose:
#   Float-safe, deterministic arithmetic for layout math (e.g., microns/tracks).
#   Uses Decimal with ROUND_HALF_DOWN to avoid FP drift and produce stable
#   grid/pitch snapping.
#
# Defaults:
#   - Results rounded to 3 decimal places unless noted.
#   - *_round_first_fpoint   -> rounds to 0.1
#   - *_round_second_fpoint  -> rounds to 0.01
#
# Functions:
#   Multiply: d_get_multiple_val()  # round down to nearest multiple
#             d_get_multiply()
#
#   Divide:   d_get_divide()
#   Add:      d_get_add(), d_get_add_round_first_fpoint(), d_get_add_round_second_fpoint()
#
#   Subtract: d_get_subtract(), d_get_subtract_round_first_fpoint(), d_get_subtract_round_second_fpoint()
#
#   Other:    d_get_round_to_int(), d_get_abs(), d_get_min(), d_get_max(),
#             d_get_floor(), d_get_ceil(), d_get_modulo()
################################################################################

### Multiply Functions
def d_get_multiply(val1 : float, val2 : float) -> float:
    """Multiply val1 with val2
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN
    """
    d_mult_val = Decimal(str(val1)) * Decimal(str(val2))
    return float(d_mult_val.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

### Divide Functions
def d_get_divide(val1 : float, val2 : float) -> float:
    """Divide val1 with val2

    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN
    """
    d_div_val = Decimal(str(val1)) / Decimal(str(val2))
    return float(d_div_val.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

### Add Functions
def d_get_add(val1 : float, val2 : float) -> float:
    """Add val1 with val2
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN
    """
    d_add_val = Decimal(str(val1)) + Decimal(str(val2))
    return float(d_add_val.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_add_round_second_fpoint(val1 : float, val2 : float) -> float:
    """Add val1 with val2
    
    :quantize: '0.01'
    :rounds: ROUND_HALF_DOWN
    """
    d_add_val = Decimal(str(val1)) + Decimal(str(val2))
    return float(d_add_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN))

def d_get_add_round_first_fpoint(val1 : float, val2 : float) -> float:
    """Add val1 with val2
    
    :quantize: '0.1'
    :rounds: ROUND_HALF_DOWN
    """
    d_add_val = Decimal(str(val1)) + Decimal(str(val2))
    return float(d_add_val.quantize(Decimal('0.1'), rounding=ROUND_HALF_DOWN))


### Subtract Functions
def d_get_subtract(val1 : float, val2 : float) -> float:
    """Subtract val1 with val2
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN
    """
    d_sub_val = Decimal(str(val1)) - Decimal(str(val2))
    return float(d_sub_val.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_subtract_round_second_fpoint(val1 : float, val2 : float) -> float:
    """Subtract val1 with val2
    
    :quantize: '0.01'
    :rounds: ROUND_HALF_DOWN
    """
    d_add_val = Decimal(str(val1)) - Decimal(str(val2))
    return float(d_add_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN))

def d_get_subtract_round_first_fpoint(val1 : float, val2 : float) -> float:
    """Subtract val1 with val2
    
    :quantize: '0.1'
    :rounds: ROUND_HALF_DOWN
    """
    d_add_val = Decimal(str(val1)) - Decimal(str(val2))
    return float(d_add_val.quantize(Decimal('0.1'), rounding=ROUND_HALF_DOWN))


### Other Functions
def d_get_multiple_val(number : float, multiple : float) -> float:
    """ Round number down to nearest multiple 
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN
    :number: 
    :multiple:

    :description:
        return (number // multiple) * multiple
    """
    d_number = Decimal(str(number))
    d_multiple = Decimal(str(multiple))
    if d_multiple == 0:
        return float(d_number)
    result = (d_number // d_multiple) * d_multiple
    return float(result.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_round_to_int(val : float) -> float:
    d_val = Decimal(str(val))
    return int(d_val.quantize(Decimal('1'), rounding=ROUND_HALF_DOWN))

def d_get_abs(val : float) -> float:
    """Get absolute value using decimal
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN"""
    d_val = Decimal(str(val))
    return float(d_val.__abs__().quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_min(val1 : float, val2 : float) -> float:
    """Get minimum of two values using decimal
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN"""
    d_val1 = Decimal(str(val1))
    d_val2 = Decimal(str(val2))
    return float(min(d_val1, d_val2).quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_max(val1 : float, val2 : float) -> float:
    """Get maximum of two values using decimal
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN"""
    d_val1 = Decimal(str(val1))
    d_val2 = Decimal(str(val2))
    return float(max(d_val1, d_val2).quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))

def d_get_floor(val : float) -> float:
    """Get floor value using decimal
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN"""
    d_val = Decimal(str(val))
    return float(d_val.quantize(Decimal('1'), rounding=ROUND_HALF_DOWN))

def d_get_ceil(val : float) -> float:
    """Get ceiling value using decimal
    
    :quantize: '1'
    :rounds: ROUND_HALF_DOWN"""
    d_val = Decimal(str(val))
    return float((d_val + Decimal('0.999')).quantize(Decimal('1'), rounding=ROUND_HALF_DOWN))

def d_get_modulo(val1 : float, val2 : float) -> float:
    """Get modulo using decimal
    
    :quantize: '0.001'
    :rounds: ROUND_HALF_DOWN"""
    d_val1 = Decimal(str(val1))
    d_val2 = Decimal(str(val2))
    result = d_val1 % d_val2
    return float(result.quantize(Decimal('0.001'), rounding=ROUND_HALF_DOWN))