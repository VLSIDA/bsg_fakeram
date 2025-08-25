from decimal import Decimal, ROUND_HALF_UP
from utils.init_mem.modules import Memory as mem

def to_grids(val_um, grid_um):
    g = Decimal(str(grid_um))
    return int((Decimal(str(val_um)) / g).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def from_grids(n, grid_um):
    return float(Decimal(n) * Decimal(str(grid_um)))

def snap_to_grid(value, grid):
    """ snap to grid using decimal """
    d_value = Decimal(str(value))
    d_grid = Decimal(str(grid))
    grids = d_value / d_grid
    rounded_grids = grids.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return float(rounded_grids * d_grid)

def get_quantized_value(value1, value2, rounding):
     """ returns the value multiplied by pitch_factor, rounded to the nearest 0.001 (three decimal places), as a float."""
     return float((Decimal(str(value1)) * Decimal(str(value2))).quantize(Decimal(str(rounding)), rounding=ROUND_HALF_UP))

def is_dataPin(mem, pin_name) -> int:
    """ return if is data pin"""
    return mem.process.metLayerHorizontalPin if (("rd" in pin_name or "wd" in pin_name) and mem.process.verticalPinsOnly == True) else mem.process.metLayerVerticalPin