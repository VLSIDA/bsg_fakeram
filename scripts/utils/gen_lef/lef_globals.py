from decimal import Decimal, ROUND_HALF_UP 

def snap_to_grid(value, grid):
    """ snap to grid using decimal """
    d_value = Decimal(str(value))
    d_grid = Decimal(str(grid))
    grids = d_value / d_grid
    rounded_grids = grids.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return float(rounded_grids * d_grid)
