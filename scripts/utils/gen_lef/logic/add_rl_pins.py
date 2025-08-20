import sys

from decimal import Decimal, ROUND_UP
from utils.gen_lef.lef_globals import *

"""
R / RW PINS:
Address and control pins are on the left

Top:
- read_data_out

W / RW Pins
Address and control pins are on the right

Right:
- write_addr_in, ce_in, write_enable_in, read_clock
"""

def lef_add_rl_pin(LEF_file, mem, pin_name, is_input, y_center_um, pitch_um, side) -> float:
    """ add right/left pin """
    LEF_file = open(LEF_file, 'a')
    track_pitch_y = pitch_um
    track_offset_y = float(mem.process.y_offset_um)
    
    if mem.process.heightSnaptoTrack == True:
        n = round((y_center_um - track_offset_y) / track_pitch_y)
        y_center_um = track_offset_y + n * track_pitch_y
        
    elif mem.process.heightSnaptoTrack == False:
        pin_index = int(round((y_center_um - track_offset_y) / track_pitch_y))
        y_center_um = track_offset_y + pin_index * track_pitch_y
        
    
    grid = float(mem.process.manufacturing_grid_um)
    flip = mem.process.flipPins
    layer = (mem.process.metalPrefix + '3') if flip else mem.process.metalLayerPins

    y_c_gr = to_grids(y_center_um, grid)
    pw_um = float(mem.process.pinWidth_um)
    hpw_gr = max(1, int((Decimal(str(pw_um)) / (2 * Decimal(str(grid)))).quantize(Decimal('1'), rounding=ROUND_UP)))
    y_bot = from_grids(y_c_gr - hpw_gr, grid)
    y_top = from_grids(y_c_gr + hpw_gr, grid)

    if y_top > mem.height_um:
        print(f"ERROR: Pin {pin_name} exceeds macro height!")
        sys.exit(1)

    ph = snap_to_grid(float(mem.process.pinHeight_um), grid)

    LEF_file.write(f'  PIN {pin_name}\n')
    LEF_file.write(f'    DIRECTION {"INPUT" if is_input else "OUTPUT"} ;\n')
    LEF_file.write('    USE SIGNAL ;\n')
    LEF_file.write('    SHAPE ABUTMENT ;\n')
    LEF_file.write('    PORT\n')
    LEF_file.write(f'      LAYER {layer} ;\n')

    if side == 'left':
        LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0.0, y_bot, ph, y_top))
    elif side == 'right':
        LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (mem.width_um - ph, y_bot, mem.width_um, y_top))

    LEF_file.write('    END\n')
    LEF_file.write(f'  END {pin_name}\n')
    LEF_file.close()

    return y_center_um + pitch_um