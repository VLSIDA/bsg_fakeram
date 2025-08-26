import os

from dataclasses import dataclass
from utils.gen_lef.lef_globals import *
from utils.gen_lef.coordinates.snap_height import snap_height_to_track

class LEF_Parameters:
    def __init__(self, mem):
        self.mem                   = mem
        self.LEF_file              = os.sep.join([mem.results_dir, mem.name + '.lef'])
        self.name                  = mem.name
        self.depth                 = mem.depth
        self.bits                  = mem.width_in_bits
        self.addr_width            = mem.addr_width
        self.metal_prefix          = mem.process.metalPrefix
        
        # Ports
        self.num_rports            = mem.r
        self.num_wports            = mem.w
        self.num_rwports           = mem.rw
        self.num_wmasks            = mem.wmask
        self.has_wmask             = mem.has_write_mask
        self.banks                 = mem.num_banks

        # Pin Params
        self.metLayerHorizontalPin = mem.process.metLayerHorizontalPin
        self.metLayerVerticalPin   = mem.process.metLayerVerticalPin
        self.x_offset              = mem.process.x_pinOffset_um
        self.y_offset              = mem.process.y_pinOffset_um
        self.pin_pitch_factor      = mem.pinPitchFactor
        self.unscaled_x_pin_pitch  = mem.process.x_pinPitch_um
        self.unscaled_y_pin_pitch  = mem.process.pinPitch_um
        self.pin_width             = mem.process.pinWidth_um
        self.pin_height            = mem.process.pinHeight_um

        # Power Grid
        self.metLayerPowerGrid     = mem.process.metLayerPowerGrid
        self.directionPowerGrid    = mem.process.directionPowerGrid
        self.powerGridWidth_um     = mem.process.powerGridWidth_um
        self.powerGridPitch_um     = mem.process.powerGridPitch_um
        self.powerGridOffset_um    = mem.process.powerGridOffset_um

        # Additional
        self.heightSnapPinPitch     = mem.process.heightSnapPinPitch
        self.widthSnapPinPitch      = mem.process.widthSnapPinPitch
        self.verticalPinsOnly       = mem.process.verticalPinsOnly

        self.x_pin_pitch = get_quantized_value(self.unscaled_x_pin_pitch, self.pin_pitch_factor, rounding=0.001)
        self.y_pin_pitch = get_quantized_value(self.unscaled_y_pin_pitch, self.pin_pitch_factor, rounding=0.001)

        # TODO: Add padding to json
        # Particularly can be useful if overlap happens between pins
        # Currently has no check if there is overlap.
        self.manufacturing_grid_um = mem.process.manufacturing_grid_um
        self.padding               = 1
        self.group_pitch           = self.y_pin_pitch * self.padding
    
        self.w                     = snap_to_grid(mem.width_um, mem.process.manufacturing_grid_um)
        self.h                     = snap_to_grid(mem.height_um, mem.process.manufacturing_grid_um)
        mem.width_um               = self.w
        mem.height_um              = self.h
        
        # Calculate pin height,
        # if heightSnaptoTrack true, will snap to track 
        # else force with y offset
        self.h = snap_height_to_track(mem, self.h, self.y_pin_pitch)
        mem.height_um = self.h
        
        # track_pitch = self.y_pin_pitch  # Assuming square grid
        # if abs(self.x_pin_pitch % track_pitch) > 0.001:
        #     # Round x_pin_pitch to nearest track-aligned value
        #     aligned_pitch = round(self.x_pin_pitch / track_pitch) * track_pitch
        #     print(f"INFO: Adjusting x_pin_pitch from {self.x_pin_pitch} to {aligned_pitch} for track alignment")
        #     self.x_pin_pitch = aligned_pitch