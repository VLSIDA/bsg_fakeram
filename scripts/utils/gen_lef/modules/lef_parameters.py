import os
import math

from utils.gen_lef.lef_globals import *
from utils.gen_lef.coordinates.snap_height import snap_height_to_track

class LEF_Parameters:
    def __init__(self, mem):
        self.mem                   = mem
        self.LEF_file              = os.sep.join([mem.results_dir, mem.name + '.lef'])
        self.name                  = mem.name
        self.depth                 = mem.depth
        self.bits                  = mem.width_in_bits
        self.banks                 = mem.num_banks
        self.w                     = snap_to_grid(mem.width_um, mem.process.manufacturing_grid_um)
        self.h                     = snap_to_grid(mem.height_um, mem.process.manufacturing_grid_um)
        mem.width_um               = self.w
        mem.height_um              = self.h
        self.flip                  = mem.process.flipPins
        self.num_rports            = mem.r
        self.num_wports            = mem.w
        self.num_rwports           = mem.rw
        self.num_wmasks            = mem.wmask
        self.has_wmask             = mem.has_write_mask
        self.pitch_factor          = mem.pitchFactor
        self.addr_width            = math.ceil(math.log2(mem.depth))
        self.min_pin_width         = float(mem.process.pinWidth_um)
        self.manufacturing_grid_um = mem.process.manufacturing_grid_um
        self.metal_prefix          = mem.process.metalPrefix
        self.metalLayerPins        = mem.process.metalLayerPins
        self.x_offset              = mem.process.x_offset_um
        self.y_offset              = mem.process.y_offset_um

        x_pitch = mem.process.x_pinPitch_um
        y_pitch = mem.process.pinPitch_um
        self.y_min_pin_pitch = get_quantized_value(y_pitch, self.pitch_factor, rounding=0.001)
        self.x_min_pin_pitch = get_quantized_value(x_pitch, self.pitch_factor, rounding=0.001)

        # TODO: Add padding to json
        # Particularly can be useful if overlap happens between pins
        # Currently has no check if there is overlap.
        self.padding               = 1
        self.group_pitch           = self.y_min_pin_pitch * self.padding
        
        # Calculate pin height,
        # if heightSnaptoTrack true, will snap to track 
        # else force with y offset
        self.h = snap_height_to_track(mem, self.h, self.y_min_pin_pitch)
        mem.height_um = self.h



