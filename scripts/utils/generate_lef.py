import os
import sys
import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN


################################################################################
# CREATE LEF view for the given SRAM
################################################################################

def generate_lef( mem ):

    # File pointer
    fid = open(os.sep.join([mem.results_dir, mem.name + '.lef']), 'w')

    # Memory parameters
    name                  = mem.name
    depth                 = mem.depth
    bits                  = mem.width_in_bits
    banks                 = mem.num_banks
    w                     = snap_to_grid(mem.width_um, mem.process.manufacturing_grid_um)
    h                     = snap_to_grid(mem.height_um, mem.process.manufacturing_grid_um)
    mem.width_um          = w
    mem.height_um         = h
    flip                  = as_bool(mem.process.flipPins)
    num_rports            = mem.r
    num_wports            = mem.w
    num_rwports           = mem.rw
    num_wmasks            = mem.wmask
    has_wmask             = mem.has_write_mask
    addr_width            = math.ceil(math.log2(mem.depth))

    # Process parameters
    min_pin_width         = float(mem.process.pinWidth_um)
    min_pin_pitch         = float(mem.process.pinPitch_um)
    manufacturing_grid_um = float(mem.process.manufacturing_grid_um)
    metal_prefix          = mem.process.metalPrefix
    metalLayerPins        = mem.process.metalLayerPins
    
    r_portside            = mem.r_portside
    w_portside            = mem.w_portside
    rw_portside           = mem.rw_portside

    x_offset              = min_pin_pitch
    y_offset              = min_pin_pitch

    # Unused
    column_mux_factor = mem.process.column_mux_factor

    #########################################
    # Calculate the pin spacing (pitch)
    #########################################

    """Read ports: each has bits (data in) + addr_width (address in) + 2 control pins    
    Write ports: each has bits (data in) + addr_width (address in) + 3 control pins
    Read/Write ports: each has bits (data out) + bits (data in) + addr_width + 3 control pins

    We calculate number of total of left/right pins 
    then take max(number_of_rpins, number_of_lpins)
    to be equal to number_of_pins"""

    wmask_pins_per_wport = num_wmasks if has_wmask else 0
    wmask_pins_per_rwport = num_wmasks if has_wmask else 0
    
    pins_per_rport = bits + addr_width + 2
    pins_per_wport = bits + addr_width + 3 + wmask_pins_per_wport  
    pins_per_rwport = 2*bits + addr_width + 3 + wmask_pins_per_rwport
    
    # Count pins on each side
    left_pins = (num_rports * pins_per_rport if r_portside == "left" else 0) + \
                (num_wports * pins_per_wport if w_portside == "left" else 0) + \
                (num_rwports * pins_per_rwport if rw_portside == "left" else 0)
    
    right_pins = (num_rports * pins_per_rport if r_portside == "right" else 0) + \
                 (num_wports * pins_per_wport if w_portside == "right" else 0) + \
                 (num_rwports * pins_per_rwport if rw_portside == "right" else 0)
    
    number_of_pins = max(left_pins, right_pins)
    total_groups = (num_rports * 2) + \
                   (num_wports * (3 if has_wmask else 2)) + \
                   (num_rwports * (4 if has_wmask else 3))

    # ports per side (for the inter-port gap your writers add)
    left_ports  = (num_rports if r_portside  == "left"  else 0) \
                + (num_wports if w_portside  == "left"  else 0) \
                + (num_rwports if rw_portside == "left" else 0)
    right_ports = (num_rports if r_portside  == "right" else 0) \
                + (num_wports if w_portside  == "right" else 0) \
                + (num_rwports if rw_portside == "right" else 0)

    items_left  = left_pins  + ((2) * (num_rports if r_portside == "left" else 0) \
                 + (3 if has_wmask else 2) * (num_wports if w_portside == "left" else 0) \
                 + (4 if has_wmask else 3) * (num_rwports if rw_portside == "left" else 0)) \
                 + max(left_ports  - 1, 0)
    items_right = right_pins + ((2) * (num_rports if r_portside == "right" else 0) \
                 + (3 if has_wmask else 2) * (num_wports if w_portside == "right" else 0) \
                 + (4 if has_wmask else 3) * (num_rwports if rw_portside == "right" else 0)) \
                 + max(right_ports - 1, 0)

    total_items = max(items_left, items_right)

    # half pin width “endcaps” (grids -> um)
    pin_half_w_gr = max(1, int((Decimal(str(mem.process.pinWidth_um)) / (2*Decimal(str(manufacturing_grid_um)))).quantize(Decimal('1'), rounding=ROUND_UP)))
    pin_half_w_um = from_grids(pin_half_w_gr, manufacturing_grid_um)

    # required height uses (total_items - 1) center steps + two endcaps
    nsteps = max(total_items - 1, 0)
    min_height_required = 2 * y_offset + (nsteps * min_pin_pitch) + (2 * pin_half_w_um)
    min_height_required = snap_to_grid(min_height_required, manufacturing_grid_um)

    d_pitch = Decimal(str(min_pin_pitch))
    d_grid  = Decimal(str(manufacturing_grid_um))
    if (d_pitch / d_grid) != (d_pitch / d_grid).quantize(Decimal('1')):
        raise RuntimeError(f"pin_pitch {min_pin_pitch} must be an exact multiple of manufacturing grid {manufacturing_grid_um}")

    if float(mem.process.pinWidth_um) > y_offset:
        raise RuntimeError("pinWidth must be <= y_offset to preserve top/bottom clearance.")

    if min_height_required > h:
        h = min_height_required
        h = snap_to_grid(h, manufacturing_grid_um)
        mem.height_um = h
    
    # available center-to-center span (exclude endcaps)
    available_space = h - 2*y_offset - (2 * pin_half_w_um)
    if total_items > 0:
        pin_pitch = min_pin_pitch
        # grow by pitch without exceeding available_space
        while nsteps > 0 and (nsteps * (pin_pitch + min_pin_pitch)) <= available_space:
            pin_pitch += min_pin_pitch
    else:
        pin_pitch = min_pin_pitch
    
    group_pitch = pin_pitch


    #########################################
    # LEF HEADER
    #########################################

    fid.write('# Generated by FakeRAM 2.0\n')
    fid.write('VERSION 5.7 ;\n')
    fid.write('BUSBITCHARS "[]" ;\n')
    fid.write('PROPERTYDEFINITIONS\n')
    fid.write('  MACRO width INTEGER ;\n')
    fid.write('  MACRO depth INTEGER ;\n')
    fid.write('  MACRO banks INTEGER ;\n')
    fid.write('END PROPERTYDEFINITIONS\n')
    fid.write('MACRO %s\n' % (name))
    fid.write(f'  PROPERTY width {bits} ;\n')
    fid.write(f'  PROPERTY depth {depth} ;\n')
    fid.write(f'  PROPERTY banks {banks} ;\n')
    fid.write('  FOREIGN %s 0 0 ;\n' % (name))
    fid.write('  SYMMETRY X Y R90 ;\n')
    fid.write('  SIZE %.3f BY %.3f ;\n' % (w,h))
    fid.write('  CLASS BLOCK ;\n')

    ########################################
    # DYNAMIC LEF SIGNAL PINS
    ########################################

    y_offset_snapped = snap_to_grid(y_offset, manufacturing_grid_um)

    # Caclulates half pin width snapped up to the nearest manufacturing grid unit usind Decimal()
    pin_half_w_gr = max(1, int((Decimal(str(mem.process.pinWidth_um)) / (2*Decimal(str(manufacturing_grid_um)))).quantize(Decimal('1'), rounding=ROUND_UP)))

    y_offset_gr   = to_grids(y_offset_snapped, manufacturing_grid_um)
    initial_y     = from_grids(y_offset_gr + pin_half_w_gr, manufacturing_grid_um)

    left_y_step = initial_y
    right_y_step = initial_y
    
    left_y_step, right_y_step = r_write_lef( fid, mem, num_rports , left_y_step, right_y_step, pin_pitch, bits, addr_width, group_pitch)
    left_y_step, right_y_step = w_write_lef( fid, mem, num_wports , left_y_step, right_y_step, pin_pitch, bits, addr_width, has_wmask, num_wmasks, group_pitch)
    left_y_step, right_y_step = rw_write_lef(fid, mem, num_rwports, left_y_step, right_y_step, pin_pitch, bits, addr_width, has_wmask, num_wmasks, group_pitch)

    ########################################
    # Create VDD/VSS Strapes
    ########################################

    supply_pin_width = min_pin_width*4
    supply_pin_half_width = snap_to_grid(supply_pin_width/2, mem.process.manufacturing_grid_um)
    supply_pin_pitch = snap_to_grid(min_pin_pitch*8, manufacturing_grid_um)

    """Non-fliped assumes metal1 is vertical therefore
        supply pins on metal4 will be horizontal and signal pins will also be on
        metal4. If set to true, supply pins on metal4 will be vertical and signal
        pins will be on metal3."""
    if flip:
        # Prevent overlapped from VDD/VSS by adding pin width + x_offset
        pw_space = snap_to_grid(mem.process.pinWidth_um + x_offset*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space, manufacturing_grid_um)
        fid.write('  PIN VSS\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE GROUND ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % metalLayerPins)
        while x_step <= w - x_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, y_offset, x_step+supply_pin_half_width, h-y_offset))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)
        fid.write('    END\n')
        fid.write('  END VSS\n')

        pw_space = snap_to_grid(mem.process.pinWidth_um + x_offset*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space, manufacturing_grid_um)
        fid.write('  PIN VDD\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE POWER ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % metalLayerPins)
        while x_step <= w - x_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, y_offset, x_step+supply_pin_half_width, h-y_offset))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)
        fid.write('    END\n')
        fid.write('  END VDD\n')

    else:
        y_step = snap_to_grid(y_offset, manufacturing_grid_um)
        fid.write('  PIN VSS\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE GROUND ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % metalLayerPins)
        while y_step <= h - y_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, y_step-supply_pin_half_width, w-x_offset, y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)
        fid.write('    END\n')
        fid.write('  END VSS\n')

        y_step = snap_to_grid(y_offset + supply_pin_pitch, manufacturing_grid_um)
        fid.write('  PIN VDD\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE POWER ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % metalLayerPins)
        while y_step <= h - y_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, y_step-supply_pin_half_width, w-x_offset, y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)
        fid.write('    END\n')
        fid.write('  END VDD\n')

    ########################################
    # Create obstructions
    ########################################

    fid.write('  OBS\n')

    # full rect
    pin_layer_number = metalLayerPins.replace(metal_prefix, "", 1).strip('"')
    for x in range(int(pin_layer_number)) :
      dummy = x + 1
      if (flip and dummy != 3):
        fid.write('    LAYER %s%d ;\n' % (metal_prefix,dummy))
        fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))
    
    # TODO
    if (mem.process.tech_nm != 7):
        fid.write('    LAYER OVERLAP ;\n')
        fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))

    fid.write('  END\n')
    fid.write('END %s\n' % name)
    fid.write('\n')
    fid.write('END LIBRARY\n')
    fid.close()




########################################
# Helper Functions
########################################



def lef_add_pin(fid, mem, pin_name, is_input, y_center_um, pitch_um, right_side) -> float:
    grid = float(mem.process.manufacturing_grid_um)
    flip = as_bool(mem.process.flipPins)
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

    fid.write(f'  PIN {pin_name}\n')
    fid.write(f'    DIRECTION {"INPUT" if is_input else "OUTPUT"} ;\n')
    fid.write('    USE SIGNAL ;\n')
    fid.write('    SHAPE ABUTMENT ;\n')
    fid.write('    PORT\n')
    fid.write(f'      LAYER {layer} ;\n')

    if right_side:
        fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (mem.width_um - ph, y_bot, mem.width_um, y_top))
    else:
        fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0.0, y_bot, ph, y_top))

    fid.write('    END\n')
    fid.write(f'  END {pin_name}\n')

    step_gr = to_grids(pitch_um, grid)
    return from_grids(y_c_gr + step_gr, grid)


def r_write_lef(fid, mem, num_rports, left_y_step, right_y_step, pin_pitch, bits, addr_width, group_pitch) -> float:
    for i in range(num_rports):
        is_right_side = mem.r_portside == 'right'
        current_y = right_y_step if is_right_side else left_y_step
            
        for j in range(int(addr_width)) :
            current_y = lef_add_pin( fid, mem, 'r%d_addr_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)
    
        for j in range(int(bits)) :
            current_y = lef_add_pin( fid, mem, 'r%d_rd_out[%d]'%(i,j), False, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)

        current_y = lef_add_pin( fid, mem, 'r%d_ce_in'%i, True, current_y, pin_pitch, is_right_side )
        current_y = lef_add_pin( fid, mem, 'r%d_clk'%i,   True, current_y, pin_pitch, is_right_side )

        if is_right_side:
            right_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)
        else:
            left_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)

    return left_y_step, right_y_step

def w_write_lef(fid, mem, num_wports, left_y_step, right_y_step, pin_pitch, bits, addr_width, has_wmask, num_wmask, group_pitch) -> float:

    for i in range(num_wports):
        is_right_side = mem.w_portside == 'right'
        current_y = right_y_step if is_right_side else left_y_step

        for j in range(int(addr_width)) :
            current_y = lef_add_pin( fid, mem, 'w%d_addr_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)

        for j in range(int(bits)) :
            current_y = lef_add_pin( fid, mem, 'w%d_wd_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)

        if has_wmask:
            for j in range(int(num_wmask)):
                current_y = lef_add_pin( fid, mem, 'w%d_wmask_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
            current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)           

        current_y = lef_add_pin( fid, mem, 'w%d_we_in'%i, True, current_y, pin_pitch, is_right_side )
        current_y = lef_add_pin( fid, mem, 'w%d_ce_in'%i, True, current_y, pin_pitch, is_right_side )
        current_y = lef_add_pin( fid, mem, 'w%d_clk'%i,   True, current_y, pin_pitch, is_right_side )

        if is_right_side:
            right_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)
        else:
            left_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)

    return left_y_step, right_y_step

def rw_write_lef(fid, mem, num_rwports, left_y_step, right_y_step, pin_pitch, bits, addr_width, has_wmask, num_wmask, group_pitch) -> float:
    for i in range(num_rwports):
        is_right_side = mem.rw_portside == 'right'
        current_y = right_y_step if is_right_side else left_y_step
    
        for j in range(int(addr_width)) :
            current_y = lef_add_pin( fid, mem, 'rw%d_addr_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)
    
        for j in range(int(bits)) :
            current_y = lef_add_pin( fid, mem, 'rw%d_wd_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)
    
        for j in range(int(bits)) :
            current_y = lef_add_pin( fid, mem, 'rw%d_rd_out[%d]'%(i,j), False, current_y, pin_pitch, is_right_side )
        current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)

        if has_wmask:
            for j in range(int(num_wmask)):
                current_y = lef_add_pin( fid, mem, 'rw%d_wmask_in[%d]'%(i,j), True, current_y, pin_pitch, is_right_side )
            current_y = snap_to_grid(current_y + group_pitch, mem.process.manufacturing_grid_um)           

        current_y = lef_add_pin( fid, mem, 'rw%d_we_in'%i, True, current_y, pin_pitch, is_right_side )
        current_y = lef_add_pin( fid, mem, 'rw%d_ce_in'%i, True, current_y, pin_pitch, is_right_side )
        current_y = lef_add_pin( fid, mem, 'rw%d_clk'%i,   True, current_y, pin_pitch, is_right_side )

        if is_right_side:
            right_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)
        else:
            left_y_step = snap_to_grid(current_y + pin_pitch, mem.process.manufacturing_grid_um)

    return left_y_step, right_y_step

def snap_to_grid(value, grid):
    d_value = Decimal(str(value))
    d_grid = Decimal(str(grid))
    grids = d_value / d_grid
    rounded_grids = grids.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return float(rounded_grids * d_grid)

def to_grids(val_um, grid_um):
    g = Decimal(str(grid_um))
    return int((Decimal(str(val_um)) / g).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def from_grids(n, grid_um):
    return float(Decimal(n) * Decimal(str(grid_um)))

def as_bool(x): 
    return str(x).strip().lower() in ('1','true','yes','y')
