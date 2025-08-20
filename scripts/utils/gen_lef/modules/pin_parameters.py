from typing import List
from dataclasses import dataclass
from utils.gen_lef.coordinates.port_start import calculate_port_starts

@dataclass
class VerticalPortStart:
    pin_pitch :  float
    num_ports :  int
    dimension :  float
    offset    :  float
    grid      :  float

@dataclass
class HorizontalPortStart:
    pin_pitch :  float
    num_ports :  int
    dimension :  float
    offset    :  float
    grid      :  float

class PinStartCoords:
    def __init__(self, lef_params):
        self.lef_params      = lef_params
        self.LEF_file        = lef_params.LEF_file
        self.mem             = lef_params.mem
        self.num_rports      = lef_params.num_rports
        self.num_wports      = lef_params.num_wports
        self.num_rwports     = lef_params.num_rwports
        self.num_wmask       = lef_params.num_wmasks
        self.has_wmask       = lef_params.has_wmask
        self.y_min_pin_pitch = lef_params.y_min_pin_pitch
        self.x_min_pin_pitch = lef_params.x_min_pin_pitch
        self.bits            = lef_params.bits
        self.addr_width      = lef_params.addr_width
        self.group_pitch     = lef_params.group_pitch


        """ Read ports 
            - data pins are on the top
            - Address and control pins are on the left
        """

        top_config = HorizontalPortStart(
            pin_pitch = lef_params.x_min_pin_pitch,
            num_ports = lef_params.num_rports + lef_params.num_rwports,
            dimension = lef_params.w,
            offset    = lef_params.x_offset,
            grid      = lef_params.manufacturing_grid_um
        )
        
        left_config = VerticalPortStart(
            pin_pitch = lef_params.y_min_pin_pitch,
            num_ports = lef_params.num_rports + lef_params.num_rwports,
            dimension = lef_params.h,
            offset    = lef_params.y_offset,
            grid      = lef_params.manufacturing_grid_um
        )


        """ Write ports
            - data pins are on the bottom.
            - Address and control pins are on the right
        """

        bottom_config = HorizontalPortStart(
            pin_pitch = lef_params.x_min_pin_pitch,
            num_ports = lef_params.num_wports + lef_params.num_rwports,
            dimension = lef_params.w,
            offset    = lef_params.x_offset,
            grid      = lef_params.manufacturing_grid_um
        )
        
        right_config = VerticalPortStart(
            pin_pitch = lef_params.y_min_pin_pitch,
            num_ports = lef_params.num_wports + lef_params.num_rwports,
            dimension = lef_params.h,
            offset    = lef_params.y_offset,
            grid      = lef_params.manufacturing_grid_um
        )
        
        
        self.left_starts  : List[float] = calculate_port_starts(left_config)
        self.right_starts : List[float] = calculate_port_starts(right_config)
        self.top_starts   : List[float] = calculate_port_starts(top_config)
        self.bot_starts   : List[float] = calculate_port_starts(bottom_config)