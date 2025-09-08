
from utils.gen_lef.lef_globals import snap_to_grid

################################################################################
# TRACK ALIGNMENT HELPERS
#
# Only when heightSnapPinPitch is TRUE:
#   Pins and macro height are aligned to routing tracks.
#
# Functions:
#   align_track_tb_pin()   - For top/bottom pins, centers the pin on the nearest
#                            Y-track using (track_offset_y, track_pitch_y) and
#                            returns (y_bottom, y_top) for the pin rectangle.
#
#   snap_height_to_track() - Snaps pin height to manufacturing grid, aligns the
#                            bottom pin center to a Y-track, computes the top pin
#                            center on a Y-track so all rows fit, and increases
#                            macro height as needed; returns the final snapped height.
################################################################################

def align_track_tb_pin(mem
            , y_edge
            , pinHeight
            , track_offset_y
            , track_pitch_y
            , pin_name
            , side ) -> tuple:
    heightSnapPinPitch = mem.process.heightSnapPinPitch
    widthSnapPinPitch  = mem.process.widthSnapPinPitch
    
    if heightSnapPinPitch == True:
        if side == 'top':
            y_top = y_edge
            y_bottom = y_top - pinHeight
            aligned_y_center = y_top - (pinHeight / 2)
        elif side == 'bottom':
            y_bottom = y_edge
            y_top = y_bottom + pinHeight
            aligned_y_center = y_bottom + (pinHeight / 2)

        n_y = round((aligned_y_center - track_offset_y) / track_pitch_y)
        expected_center = track_offset_y + n_y * track_pitch_y

    elif heightSnapPinPitch == False:
        # TRUE FORCE OFFSET: No rounding, use exact edge-relative positioning
        if side == 'top':
            # For top pins, maintain exact distance from top edge
            y_top = y_edge
            y_bottom = y_top - pinHeight
            
        elif side == 'bottom':
            # For bottom pins, maintain exact distance from bottom edge  
            y_bottom = y_edge
            y_top = y_bottom + pinHeight
            
    return y_bottom, y_top

def snap_height_to_track(mem
                , h
                , scaled_y_pitch
                ) -> float:
    heightSnapPinPitch    = mem.process.heightSnapPinPitch
    y_offset              = mem.process.y_pinOffset_um
    manufacturing_grid_um = mem.process.manufacturing_grid_um
    pin_height            = mem.process.x_pinHeight_um

    """adjust macro height to fit"""
    if heightSnapPinPitch == True:
        pinHeight = snap_to_grid(float(pin_height), manufacturing_grid_um)
        track_pitch_y = scaled_y_pitch
        track_offset_y = float(y_offset)
        
        required_bot_center = pinHeight / 2
        
        n_bot = round((required_bot_center - track_offset_y) / track_pitch_y)
        bot_center_on_track = track_offset_y + n_bot * track_pitch_y
        
        if bot_center_on_track - (pinHeight / 2) < 0:
            shift_needed = (pinHeight / 2) - bot_center_on_track
            track_offset_y += shift_needed
            bot_center_on_track = pinHeight / 2
            y_offset = track_offset_y
        
        max_possible_tracks = int((h - pinHeight) / track_pitch_y) + 1
        
        top_center_on_track = bot_center_on_track + (max_possible_tracks - 1) * track_pitch_y
        required_macro_height = top_center_on_track + (pinHeight / 2)
        
        if required_macro_height < h:
            top_center_on_track += track_pitch_y
            required_macro_height = top_center_on_track + (pinHeight / 2)
        
        final_height = snap_to_grid(required_macro_height, manufacturing_grid_um)
    
    elif heightSnapPinPitch == False:
        # TRUE FORCE OFFSET: Keep original height, extend if needed
        pinHeight = snap_to_grid(float(pin_height), manufacturing_grid_um)
        track_offset_y = float(y_offset)
        
        # Calculate potential pin positions with exact offset
        bottom_pin_center = pinHeight / 2  # First pin center
        top_pin_center = bottom_pin_center + ((h - pinHeight) // scaled_y_pitch) * scaled_y_pitch
        
        # Check if pins would extend beyond macro bounds
        bottom_edge = bottom_pin_center - (pinHeight / 2)
        top_edge = top_pin_center + (pinHeight / 2)
        
        # Extend macro if needed
        if bottom_edge < 0:
            extension_needed = abs(bottom_edge)
            final_height = h + extension_needed
            mem._bottom_edge_offset = bottom_edge
        elif top_edge > h:
            extension_needed = top_edge - h
            final_height = h + extension_needed
            mem._bottom_edge_offset = 0
        else:
            final_height = h
            mem._bottom_edge_offset = 0
            
        final_height = snap_to_grid(final_height, manufacturing_grid_um)
        
    
    return final_height