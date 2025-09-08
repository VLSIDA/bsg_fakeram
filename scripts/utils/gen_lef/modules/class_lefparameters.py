import os

from utils.gen_lef.lef_globals import *
from utils.gen_lef.coordinates.snap_height import snap_height_to_track

from decimal import Decimal, ROUND_HALF_UP

################################################################################
# LEF PARAMETERS CLASS
#
# Centralizes process/memory geometry and tech knobs for LEF generation:
# sets paths, macro dimensions, pin pitches, metal layers, and power grid.
# Computes derived pitches, snaps width/height to manufacturing grid, and
# snaps height to track when enabled.
#
# Functions:
#   _d_get_multiply_value_round_halfup() - multiply and round (half-up) to a given increment
################################################################################

class LEF_Parameters:
    def __init__(self, mem):
        self.mem                   = mem
        self.LEF_file              = os.sep.join([mem.results_dir, mem.fakeram_name_extension + mem.name + '.lef'])
        self.name                  = mem.name
        self.depth                 = mem.depth
        self.bits                  = mem.width_in_bits
        self.addr_width            = mem.addr_width
        self.metal_prefix          = mem.process.metalPrefix
        self.num_rports            = mem.r
        self.num_wports            = mem.w
        self.num_rwports           = mem.rw
        self.num_wmasks            = mem.wmask
        self.has_wmask             = mem.has_write_mask
        self.banks                 = mem.num_banks
        self.metLayerHorizontalPin = mem.process.metLayerHorizontalPin
        self.metLayerVerticalPin   = mem.process.metLayerVerticalPin
        self.x_offset              = mem.process.x_pinOffset_um
        self.y_offset              = mem.process.y_pinOffset_um
        self.pin_pitch_factor      = mem.pinPitchFactor
        self.unscaled_x_pin_pitch  = mem.process.x_pinPitch_um
        self.unscaled_y_pin_pitch  = mem.process.pinPitch_um
        self.x_pin_width           = mem.process.x_pinWidth_um
        self.x_pin_height          = mem.process.x_pinHeight_um
        self.y_pin_width           = mem.process.y_pinWidth_um
        self.y_pin_height          = mem.process.y_pinHeight_um
        self.metLayerPowerGrid     = mem.process.metLayerPowerGrid
        self.directionPowerGrid    = mem.process.directionPowerGrid
        self.powerGridWidth_um     = mem.process.powerGridWidth_um
        self.powerGridPitch_um     = mem.process.powerGridPitch_um
        self.powerGridOffset_um    = mem.process.powerGridOffset_um
        self.heightSnapPinPitch    = mem.process.heightSnapPinPitch
        self.widthSnapPinPitch     = mem.process.widthSnapPinPitch

        self.x_pin_pitch = self._d_get_multiply_value_round_halfup(self.unscaled_x_pin_pitch, self.pin_pitch_factor, rounding_val=0.001)
        self.y_pin_pitch = self._d_get_multiply_value_round_halfup(self.unscaled_y_pin_pitch, self.pin_pitch_factor, rounding_val=0.001)

        self.manufacturing_grid_um = mem.process.manufacturing_grid_um
    
        self.w                     = snap_to_grid(mem.width_um, mem.process.manufacturing_grid_um)
        self.h                     = snap_to_grid(mem.height_um, mem.process.manufacturing_grid_um)
        mem.width_um               = self.w
        mem.height_um              = self.h
        
        # Calculate pin height,
        # if heightSnaptoTrack true, will snap to track 
        # else force with y offset
        self.h = snap_height_to_track(mem, self.h, self.y_pin_pitch)
        mem.height_um = self.h

    def _d_get_multiply_value_round_halfup(self, value1, value2, rounding_val):
            """ returns the value multiplied by pitch_factor, rounded to the nearest 0.001 (three decimal places), as a float."""
            return float((Decimal(str(value1)) * Decimal(str(value2))).quantize(Decimal(str(rounding_val)), rounding=ROUND_HALF_UP))
