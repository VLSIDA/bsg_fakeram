import sys

from decimal import Decimal, ROUND_UP
from utils.gen_lef.lef_globals import *
from utils.gen_lef.coordinates.__init__ import *

"""
R / RW Pins
Data pins are on the top

Left:
- read_addr_in, ce_in, read_clock

W / RW Pins
Data pins are on the bottom

Bottom:
- write_data_in
"""

def lef_add_tb_pin(LEF_file, mem, pin_name, is_input, x_center_um, y_pitch_um, x_pitch_um, side) -> float:
    """ add top/bot pin """
    LEF_file = open(LEF_file, 'a')
    track_pitch_x = x_pitch_um
    track_offset_x = float(mem.process.x_offset_um)
    track_pitch_y = y_pitch_um
    track_offset_y = float(mem.process.y_offset_um)
    
    if mem.process.heightSnaptoTrack == True:
        # Align X to tracks
        n = round((x_center_um - track_offset_x) / track_pitch_x)
        x_center_um = track_offset_x + n * track_pitch_x
        
    elif mem.process.heightSnaptoTrack == False:
        pin_index_x = int(round((x_center_um - track_offset_x) / track_pitch_x))
        x_center_um = track_offset_x + pin_index_x * track_pitch_x
        
    
    grid = float(mem.process.manufacturing_grid_um)
    flip = mem.process.flipPins
    layer = (mem.process.metalPrefix + '3') if flip else mem.process.metalLayerPins

    x_c_gr = to_grids(x_center_um, grid)
    pw_um = float(mem.process.pinWidth_um)
    hpw_gr = max(1, int((Decimal(str(pw_um)) / (2 * Decimal(str(grid)))).quantize(Decimal('1'), rounding=ROUND_UP)))
    x_left = from_grids(x_c_gr - hpw_gr, grid)
    x_right = from_grids(x_c_gr + hpw_gr, grid)

    if x_right > mem.width_um:
        print(f"ERROR: Pin {pin_name} exceeds macro width!")
        sys.exit(1)

    ph = snap_to_grid(float(mem.process.pinHeight_um), grid)

    LEF_file.write(f'  PIN {pin_name}\n')
    LEF_file.write(f'    DIRECTION {"INPUT" if is_input else "OUTPUT"} ;\n')
    LEF_file.write('    USE SIGNAL ;\n')
    LEF_file.write('    SHAPE ABUTMENT ;\n')
    LEF_file.write('    PORT\n')
    LEF_file.write(f'      LAYER {layer} ;\n')

    if side == 'top':
        start_edge = mem.height_um
        y_bottom, y_top = align_track_tb_pin(mem, start_edge, ph, track_offset_y, track_pitch_y, pin_name, 'top')
        LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_left, y_bottom, x_right, y_top))
    elif side == 'bottom':
        start_edge = 0.0
        y_bottom, y_top = align_track_tb_pin(mem, start_edge, ph, track_offset_y, track_pitch_y, pin_name, 'bottom')
        LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_left, y_bottom, x_right, y_top))
            
    LEF_file.write('    END\n')
    LEF_file.write(f'  END {pin_name}\n')
    LEF_file.close()

    return x_center_um + x_pitch_um