from utils.gen_lef.coordinates.__init__ import *
from .add_rl_pins import lef_add_rl_pin
from .add_tb_pins import lef_add_tb_pin

is_output = False
is_input = True

def gen_r_port(pin_p) -> float:
    """Read ports - Address and control pins are on the left, data pins are on the top"""
    LEF_file           = pin_p.LEF_file
    mem                = pin_p.mem
    num_rports         = pin_p.num_rports
    y_pin_pitch        = pin_p.y_pin_pitch
    x_pin_pitch        = pin_p.x_pin_pitch
    bits               = pin_p.bits
    addr_width         = pin_p.addr_width
    group_pitch        = pin_p.group_pitch
    left_starts        = pin_p.left_starts
    top_starts         = pin_p.top_starts
    manufacturing_grid = pin_p.manufacturing_grid_um

    for i in range(num_rports):
        # Calculate total pins for left side (addr + control)
        left_pins_per_port = addr_width + 2  # clk + ce_in
        left_center = left_starts[i] if i < len(left_starts) else left_starts[0]
        left_start = calculate_centered_start(left_pins_per_port, y_pin_pitch, group_pitch, left_center, manufacturing_grid)
        
        current_y = left_start

        # Address pins on left
        r_ce_in = f'r{i}_ce_in'
        r_clk = f'r{i}_clk'
        for j in range(int(addr_width)):
            r_addr_in = f'r{i}_addr_in[{j}]'

            current_y = lef_add_rl_pin(LEF_file, mem, r_addr_in, is_input, current_y, y_pin_pitch, 'left')
        current_y = snap_to_grid(current_y + group_pitch, manufacturing_grid)
    
        # Control pins on left
        current_y = lef_add_rl_pin(LEF_file, mem, r_ce_in, is_input, current_y, y_pin_pitch, 'left')
        current_y = lef_add_rl_pin(LEF_file, mem, r_clk, is_input, current_y, y_pin_pitch, 'left')

        if mem.process.verticalPinsOnly == True:
            for j in range(int(bits)):
                r_rd_out = f'r{i}_rd_out[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, r_rd_out, is_output, current_y, y_pin_pitch, 'right')
        else:
            # Data pins on top
            top_pins_per_port = bits
            top_center = top_starts[i] if i < len(top_starts) else top_starts[0]
            # top_start = calculate_centered_start(top_pins_per_port, x_pin_pitch, group_pitch, top_center, manufacturing_grid)
            top_start = calculate_centered_start(
                top_pins_per_port, 
                x_pin_pitch, 
                group_pitch, 
                top_center, 
                manufacturing_grid
                 
            )
            
            current_x = top_start
            for j in range(int(bits)):
                r_rd_out = f'r{i}_rd_out[{j}]'
                current_x = lef_add_tb_pin(LEF_file, mem, r_rd_out , is_output, current_x, y_pin_pitch, x_pin_pitch, 'top')
            current_x += x_pin_pitch

def gen_w_port(pin_p) -> float:
    """ Write ports, address and control pins are on the right, data pins are on the bottom """
    LEF_file           = pin_p.LEF_file
    mem                = pin_p.mem
    num_wports         = pin_p.num_wports
    y_pin_pitch        = pin_p.y_pin_pitch
    x_pin_pitch        = pin_p.x_pin_pitch
    bits               = pin_p.bits
    addr_width         = pin_p.addr_width
    has_wmask          = pin_p.has_wmask
    num_wmask          = pin_p.num_wmask
    group_pitch        = pin_p.group_pitch
    right_starts       = pin_p.right_starts
    bot_starts         = pin_p.bot_starts
    manufacturing_grid = pin_p.manufacturing_grid_um

    for i in range(num_wports):
        wmask_pins = num_wmask if has_wmask else 0
        
        # Calculate total pins for right side (addr + control + wmask)
        right_pins_per_port = addr_width + 3 + wmask_pins  # we_in + ce_in + clk + wmask
        right_center = right_starts[i] if i < len(right_starts) else right_starts[0]
        right_start = calculate_centered_start(right_pins_per_port, y_pin_pitch, group_pitch, right_center, manufacturing_grid)
        
        current_y = right_start
        
        # Address pins on right
        for j in range(int(addr_width)):
            w_addr_in = f'w{i}_addr_in[{j}]'
            current_y = lef_add_rl_pin(LEF_file, mem, w_addr_in, is_input, current_y, y_pin_pitch, 'right')
        current_y = snap_to_grid(current_y + group_pitch, manufacturing_grid)

        # Write mask pins on right
        if has_wmask:
            for j in range(int(num_wmask)):
                w_wmask_in = f'w{i}_wmask_in[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, w_wmask_in, is_input, current_y, y_pin_pitch, 'right')
            current_y = snap_to_grid(current_y + group_pitch, manufacturing_grid)

        # Control pins on right
        w_we_in = f'w{i}_we_in'
        w_ce_in = f'w{i}_ce_in'
        w_clk = f'w{i}_clk'
        current_y = lef_add_rl_pin(LEF_file, mem, w_we_in, is_input, current_y, y_pin_pitch, 'right')
        current_y = lef_add_rl_pin(LEF_file, mem, w_ce_in, is_input, current_y, y_pin_pitch, 'right')
        current_y = lef_add_rl_pin(LEF_file, mem, w_clk, is_input, current_y, y_pin_pitch, 'right')

        if mem.process.verticalPinsOnly == True:
            for j in range(int(bits)):
                w_wd_in = f'w{i}_wd_in[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, w_wd_in, is_input, current_y, y_pin_pitch, 'left')
        else:
            # Data pins on bottom
            bot_pins_per_port = bits
            bot_center = bot_starts[i] if i < len(bot_starts) else bot_starts[0]
            # bot_start = calculate_centered_start(bot_pins_per_port, x_pin_pitch, group_pitch, bot_center, manufacturing_grid)
            bot_start = calculate_centered_start(
                bot_pins_per_port, 
                x_pin_pitch, 
                group_pitch, 
                bot_center, 
                manufacturing_grid
                 
            )
            
            current_x = bot_start
            for j in range(int(bits)):
                w_wd_in = f'w{i}_wd_in[{j}]'
                current_x = lef_add_tb_pin(LEF_file, mem, w_wd_in, is_input, current_x, y_pin_pitch, x_pin_pitch, 'bottom')
            current_x += x_pin_pitch

def gen_rw_port(pin_p) -> float:
    """Read/Write ports split between left/right for addr+control, top/bottom for data"""
    LEF_file           = pin_p.LEF_file
    mem                = pin_p.mem
    num_rwports        = pin_p.num_rwports
    num_rports         = pin_p.num_rports
    num_wports         = pin_p.num_wports
    y_pin_pitch        = pin_p.y_pin_pitch
    x_pin_pitch        = pin_p.x_pin_pitch
    bits               = pin_p.bits
    addr_width         = pin_p.addr_width
    has_wmask          = pin_p.has_wmask
    num_wmask          = pin_p.num_wmask
    group_pitch        = pin_p.group_pitch
    left_starts        = pin_p.left_starts
    right_starts       = pin_p.right_starts
    top_starts         = pin_p.top_starts
    bot_starts         = pin_p.bot_starts
    manufacturing_grid = pin_p.manufacturing_grid_um

    for i in range(num_rwports):
        wmask_pins = num_wmask if has_wmask else 0
        
        # Left side: addr + ce + clk (read control)
        left_pins_per_port = addr_width + 2  # ce_in + clk
        left_idx = num_rports + i  # Offset by number of read ports
        left_center = left_starts[left_idx] if left_idx < len(left_starts) else left_starts[-1]
        left_start = calculate_centered_start(left_pins_per_port, y_pin_pitch, group_pitch, left_center, manufacturing_grid)
        
        current_y = left_start
        
        # Address pins on left
        for j in range(int(addr_width)):
            rw_addr_in = f'rw{i}_addr_in[{j}]'
            current_y = lef_add_rl_pin(LEF_file, mem, rw_addr_in, is_input, current_y, y_pin_pitch, 'left')
        current_y = snap_to_grid(current_y + group_pitch, manufacturing_grid)
    
        # Read control pins on left
        rw_ce_in = f'rw{i}_ce_in'
        rw_clk = f'rw{i}_clk'
        current_y = lef_add_rl_pin(LEF_file, mem, rw_ce_in, is_input, current_y, y_pin_pitch, 'left')
        current_y = lef_add_rl_pin(LEF_file, mem, rw_clk, is_input, current_y, y_pin_pitch, 'left')

        # RIGHT PIN PLACEMENTS
        # Right side: we + wmask (write control)
        right_pins_per_port = 1 + wmask_pins  # we_in + wmask
        right_idx = num_wports + i  # Offset by number of write ports
        right_center = right_starts[right_idx] if right_idx < len(right_starts) else right_starts[-1]
        right_start = calculate_centered_start(right_pins_per_port, y_pin_pitch, group_pitch, right_center, manufacturing_grid)
        
        current_y = right_start
        
        # Write mask pins on right
        if has_wmask:
            for j in range(int(num_wmask)):
                rw_wmask_in = f'rw{i}_wmask_in[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, rw_wmask_in, is_input, current_y, y_pin_pitch, 'right')
            current_y = snap_to_grid(current_y + group_pitch, manufacturing_grid)

        # Write enable on right
        rw_we_in = f'rw{i}_we_in'
        current_y = lef_add_rl_pin(LEF_file, mem, rw_we_in, is_input, current_y, y_pin_pitch, 'right')

        if mem.process.verticalPinsOnly == True:
            for j in range(int(bits)):
                rw_rd_out = f'rw{i}_rd_out[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, rw_rd_out, is_output, current_y, y_pin_pitch, 'right')
        else:
            # Read data pins on top
            top_pins_per_port = bits
            top_idx = num_rports + i  # Offset by number of read ports
            top_center = top_starts[top_idx] if top_idx < len(top_starts) else top_starts[-1]
            # top_start = calculate_centered_start(top_pins_per_port, x_pin_pitch, group_pitch, top_center, manufacturing_grid)
            top_start = calculate_centered_start(
                top_pins_per_port, 
                x_pin_pitch, 
                group_pitch, 
                top_center, 
                manufacturing_grid
                 
            )
            
            current_x = top_start
            for j in range(int(bits)):
                rw_rd_out = f'rw{i}_rd_out[{j}]'
                current_x = lef_add_tb_pin(LEF_file, mem, rw_rd_out, is_output, current_x, y_pin_pitch, x_pin_pitch, 'top')
            current_x += x_pin_pitch

        if mem.process.verticalPinsOnly == True:
            for j in range(int(bits)):
                rw_wd_in = f'rw{i}_wd_in[{j}]'
                current_y = lef_add_rl_pin(LEF_file, mem, rw_wd_in, is_input, current_y, y_pin_pitch, 'left')
        else:
            # Write data pins on bottom
            bot_pins_per_port = bits
            bot_idx = num_wports + i  # Offset by number of write ports
            bot_center = bot_starts[bot_idx] if bot_idx < len(bot_starts) else bot_starts[-1]
            # bot_start = calculate_centered_start(bot_pins_per_port, x_pin_pitch, group_pitch, bot_center, manufacturing_grid)
            bot_start = calculate_centered_start(
                bot_pins_per_port, 
                x_pin_pitch, 
                group_pitch, 
                bot_center, 
                manufacturing_grid
                 
            )
            
            current_x = bot_start
            for j in range(int(bits)):
                rw_wd_in = f'rw{i}_wd_in[{j}]'
                current_x = lef_add_tb_pin(LEF_file, mem, rw_wd_in, is_input, current_x, y_pin_pitch, x_pin_pitch, 'bottom')
            current_x += x_pin_pitch