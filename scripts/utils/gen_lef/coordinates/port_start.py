import sys
from utils.gen_lef.lef_globals import snap_to_grid

def calculate_port_starts(side):
    """Calculate starting positions for ports based on count"""
    
    pin_pitch = side.pin_pitch
    num_ports = side.num_ports
    dimension = side.dimension
    offset    = side.offset
    grid      = side.grid

    if num_ports == 0:
        return []
    
    # Align everything to manufacturing grid
    offset_aligned = snap_to_grid(offset, grid)
    pin_pitch_aligned = snap_to_grid(pin_pitch, grid)
    
    # Calculate available space and distribute ports
    available_space = dimension - 2 * offset_aligned
    available_tracks = int(available_space / pin_pitch_aligned)
    
    if num_ports > available_tracks:
        print(f"ERROR: Not enough tracks for {num_ports} ports")
        sys.exit(1)
    
    track_spacing = available_tracks // (num_ports + 1)
    
    positions = []
    for i in range(num_ports):
        # Calculate position directly in manufacturing grid units
        track_pos = offset_aligned + ((i + 1) * track_spacing * pin_pitch_aligned)
        pos = snap_to_grid(track_pos, grid)
        positions.append(pos)
    
    return positions

def calculate_centered_start(total_pins, pin_pitch, group_pitch, center_pos, grid):
    """Calculate starting position to center pins around a position"""

    # Align all inputs to manufacturing grid
    pin_pitch_aligned = snap_to_grid(pin_pitch, grid)
    group_pitch_aligned = snap_to_grid(group_pitch, grid)
    center_aligned = snap_to_grid(center_pos, grid)
    
    # Calculate total space needed
    total_space = (total_pins - 1) * pin_pitch_aligned + 2 * group_pitch_aligned
    
    # Calculate starting position
    start_pos = center_aligned - (total_space / 2) + group_pitch_aligned
    
    return snap_to_grid(start_pos, grid)