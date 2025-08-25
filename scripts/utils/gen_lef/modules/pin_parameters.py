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
    def __init__(self, lef_p):
        self.lef_p                 = lef_p
        self.LEF_file              = lef_p.LEF_file
        self.mem                   = lef_p.mem
        self.num_rports            = lef_p.num_rports
        self.num_wports            = lef_p.num_wports
        self.num_rwports           = lef_p.num_rwports
        self.num_wmask             = lef_p.num_wmasks
        self.has_wmask             = lef_p.has_wmask
        self.y_pin_pitch           = lef_p.y_pin_pitch
        self.x_pin_pitch           = lef_p.x_pin_pitch
        self.bits                  = lef_p.bits
        self.addr_width            = lef_p.addr_width
        self.group_pitch           = lef_p.group_pitch
        self.manufacturing_grid_um = lef_p.manufacturing_grid_um


        """ Read ports 
            - data pins are on the top
            - Address and control pins are on the left
        """

        top_config = HorizontalPortStart(
            pin_pitch = lef_p.x_pin_pitch,
            num_ports = lef_p.num_rports + lef_p.num_rwports,
            dimension = lef_p.w,
            offset    = lef_p.x_offset,
            grid      = lef_p.manufacturing_grid_um
        )
        
        left_config = VerticalPortStart(
            pin_pitch = lef_p.y_pin_pitch,
            num_ports = lef_p.num_rports + lef_p.num_rwports,
            dimension = lef_p.h,
            offset    = lef_p.y_offset,
            grid      = lef_p.manufacturing_grid_um
        )


        """ Write ports
            - data pins are on the bottom.
            - Address and control pins are on the right
        """

        bottom_config = HorizontalPortStart(
            pin_pitch = lef_p.x_pin_pitch,
            num_ports = lef_p.num_wports + lef_p.num_rwports,
            dimension = lef_p.w,
            offset    = lef_p.x_offset,
            grid      = lef_p.manufacturing_grid_um
        )
        
        right_config = VerticalPortStart(
            pin_pitch = lef_p.y_pin_pitch,
            num_ports = lef_p.num_wports + lef_p.num_rwports,
            dimension = lef_p.h,
            offset    = lef_p.y_offset,
            grid      = lef_p.manufacturing_grid_um
        )
        
        
        self.left_starts  : List[float] = calculate_port_starts(left_config)
        self.right_starts : List[float] = calculate_port_starts(right_config)
        self.top_starts   : List[float] = calculate_port_starts(top_config)
        self.bot_starts   : List[float] = calculate_port_starts(bottom_config)