import sys

from utils.gen_lef.decimal_helpers import *
from utils.gen_lef.modules.class_lefparameters import LEF_Parameters 

from dataclasses import dataclass, field
from typing import List

################################################################################
# LEF PIN GRID HELPER
#
# Builds and validates per-edge pin-slot grids (top/bottom/left/right) for a macro.
#
# Dataclass:
#   PinSlot                               - slot metadata (coord, side, layer, used)
#
# Functions:
#   _initialize_pins()                    - compute offsets, seeds, and containers
#   _initialize_pinlist()                 - populate candidate slots for all sides
#   _available_slots()                    - append per-layer slots for a side pair
#   _validate_list()                      - verify grid & pitch constraints
#   _d_if_divisible_manfufacturing_grid() - check slot vs manufacturing grid
#   _d_if_startcoord_multiple_of_pitch()  - check start coord vs pin pitch
#   _parse_list_side_manufacturing_grid() - validate all slots against grid
#   _parse_list_side_pin_pitch()          - validate all slots against pitch
################################################################################

@dataclass
class PinSlot:
    """ Reusable pin coord class """
    slot            :  float  = field(default_factory=float)
    used            :  bool   = field(default_factory=bool)
    side            :  str    = field(default_factory=str)
    metLayer        :  int    = field(default_factory=object)

class PinGrid(LEF_Parameters):
    def __init__(self,mem):
        super().__init__(mem)
        self.list_top_pins      : List[object] = None
        self.list_bot_pins      : List[object] = None
        self.list_left_pins     : List[object] = None
        self.list_right_pins    : List[object] = None
        self.w_offset           : float        = None
        self.h_offset           : float        = None

        # DEBUG PARAMS
        self.debug_list_validation : bool  = False

        self._initialize_pins()
        self._initialize_pinlist()
        self._validate_list()
        self.num_gen_section_calls = 0

#### Private Functions
#---------------------
    def _initialize_pins(self) -> None :  
        self.total_layers   = max(self.metLayerHorizontalPin, self.metLayerVerticalPin)
        self.w_offset       = d_get_subtract(self.w, self.x_offset)
        self.h_offset       = d_get_subtract(self.h, self.y_offset)
        self.x_dummy_pin    = d_get_divide(self.x_pin_width, 2)
        self.y_dummy_pin    = d_get_divide(self.y_pin_width, 2)
        self.start_coord_rl = d_get_add(self.y_offset, self.y_pin_pitch)
        self.start_coord_tb = d_get_add(self.x_offset, self.x_pin_pitch)
        self.list_top_pins , self.list_bot_pins   = [], []
        self.list_left_pins, self.list_right_pins = [], []

    def _initialize_pinlist(self) -> None:
        self._available_slots(
            self.w, self.x_pin_pitch, self.x_offset, self.x_dummy_pin, self.x_pin_width,
            self.start_coord_tb, self.list_top_pins, self.list_bot_pins, 
            'top', 'bottom'
        )
        
        self._available_slots(
            self.h, self.y_pin_pitch, self.y_offset, self.y_dummy_pin, self.y_pin_width,
            self.start_coord_rl, self.list_left_pins, self.list_right_pins,
            'left', 'right'
        )

    def _available_slots(self
                    , dimension   :  float
                    , pin_pitch   :  float
                    , offset      :  float
                    , dummy_pin   :  float
                    , pin_width   :  float
                    , start_coord :  float
                    , list1       :  list
                    , list2       :  list
                    , side1       :  str
                    , side2       :  str ) -> None:  
        step = start_coord
        while dimension - dummy_pin - offset > step:
            slot = d_get_subtract(step, d_get_divide(pin_width, 2))
        
            for met_num in range(1, self.total_layers+1):
                list1.append(PinSlot(
                  slot     = slot
                , used     = False
                , side     = side1
                , metLayer = met_num
                )
            )
                list2.append(PinSlot(
                  slot     = slot
                , used     = False
                , side     = side2
                , metLayer = met_num
                )
            )

            step = d_get_add(step, pin_pitch)

##### Verification 
    def _validate_list(self) -> None:
        manufacturing_grid = self.manufacturing_grid_um

        list_top_pins      = self._parse_list_side_manufacturing_grid(self.list_top_pins, manufacturing_grid)
        list_bot_pins      = self._parse_list_side_manufacturing_grid(self.list_bot_pins, manufacturing_grid)
        list_right_pins    = self._parse_list_side_manufacturing_grid(self.list_right_pins, manufacturing_grid)
        list_left_pins     = self._parse_list_side_manufacturing_grid(self.list_left_pins, manufacturing_grid)

        list_top_pins      = self._parse_list_side_pin_pitch(self.list_top_pins, self.unscaled_x_pin_pitch, self.x_pin_width)
        list_bot_pins      = self._parse_list_side_pin_pitch(self.list_bot_pins, self.unscaled_x_pin_pitch, self.x_pin_width)
        list_right_pins    = self._parse_list_side_pin_pitch(self.list_right_pins, self.unscaled_y_pin_pitch, self.y_pin_width)
        list_left_pins     = self._parse_list_side_pin_pitch(self.list_left_pins, self.unscaled_y_pin_pitch, self.y_pin_width)

        if len(self.list_top_pins) != len(self.list_bot_pins):
            print("Top and bottom sizes are not the same!")
            sys.exit(1)
        if len(self.list_left_pins) != len(self.list_right_pins):
            print("Left and right sizes are not the same!")
            sys.exit(1)

        print(
            f'list_top_pins passed   : {list_top_pins}\n'
            f'list_bot_pins passed   : {list_bot_pins}\n'
            f'list_right_pins passed : {list_right_pins}\n'
            f'list_left_pins passed  : {list_left_pins}\n'
            f'\n'
            f'Pin grid pass\n'
            )
        
    def _d_if_divisible_manfufacturing_grid(self
                        , slot : float
                        , grid : float ) -> bool:
        """ Returns true if individual slot is divisible by its manufacturing grid """
        return True if (Decimal(str(slot)) % Decimal(str(grid)) == 0) else False
    
    def _parse_list_side_manufacturing_grid(self
                        , pin_list: object
                        , manufacturing_grid: float ) -> bool:
        """ Returns true if all pin slots are divisible by manufacturing grid """
        for pin in pin_list:
            if self._d_if_divisible_manfufacturing_grid(pin.slot, manufacturing_grid) == False: 
                print(f'slot ({pin.slot}) not multiple of manufacturing grid ({manufacturing_grid})')
                sys.exit(1)
            if self.debug_list_validation:
                print(pin, "pass")
        return True
    
    def _d_if_startcoord_multiple_of_pitch(self
                        , start_coord : float
                        , pw          : float
                        , pitch       : float ) -> bool:
        """ Returns true if the starting coordinate is a multiple of the pitch """
        return True if (Decimal(str(d_get_add(start_coord, d_get_divide(pw, 2)))) % Decimal(str(pitch)) == 0) else False

    def _parse_list_side_pin_pitch(self
                        , pin_list  : object
                        , pin_pitch : float
                        , pin_width : float ) -> bool:
        for pin in pin_list:
            calculated_pos = d_get_add(pin.slot, d_get_divide(pin_width, 2))
            remainder = float(Decimal(str(calculated_pos)) % Decimal(str(pin_pitch)))
            
            if self.debug_list_validation:
                print(f"Debug: pin.slot={pin.slot}, pin_width/2={pin_width/2}, calculated_pos={calculated_pos}, pin_pitch={pin_pitch}, remainder={remainder}")
            
            if self._d_if_startcoord_multiple_of_pitch(pin.slot, pin_width, pin_pitch) == False:
                axis = "x" if pin_pitch == self.x_pin_pitch else "y"
                print(f'{axis} axis : slot ({calculated_pos}) not multiple of pin pitch! ({pin_pitch})')
                sys.exit(1)

            if self.debug_list_validation:
                print(f"{pin.slot} start coord: pass")
        return True