
import sys
import traceback

from utils.gen_lef.lef_globals import *
from utils.gen_lef.logic.lef_writers import *
from utils.gen_lef.logic.gen_ports import *


################################################################################
# WRAPPER CLASSES
#
# PinListWrapper: holds tuned placement parameters and helpers that return
#                 prevalidated pin-slot lists for specific sections/sides.
#
# PinIndexWrapper: writes pins by index into a given pin_list with safety checks.
################################################################################
    
class PinListWrapper(LEF_Parameters):
    def __init__(self, mem):
        super().__init__(mem)
        self.mem                            = mem
        self.left_group_padding             = 0.005
        self.right_group_padding            = 0.005
        self.w_mask_padding                 = 0.01
        self.r_port_control_padding         = self.left_group_padding
        self.r_addr_padding                 = self.left_group_padding
        self.w_addr_padding                 = self.right_group_padding
        self.w_port_control_padding         = self.right_group_padding
        self.min_distance_between_port_pins = 5
        self.r_control_metal_layer          = self.metLayerVerticalPin
        self.r_control_section_start        = 0.03
        self.r_control_section_end          = 0.04
        self.r_control_metal_layer          = self.metLayerVerticalPin
        self.r_control_side                 = "left"
        self.w_control_metal_layer          = self.metLayerVerticalPin
        self.w_control_side                 = "right"
        self.w_control_section_start        = 0.90
        self.w_control_section_end          = 0.92
        self.r_addr_in_metal_layer          = self.metLayerVerticalPin
        self.r_addr_in_side                 = "left"
        self.r_addr_in_section_start        = 0.1
        self.r_addr_in_section_end          = 0.15
        self.w_addr_in_metal_layer          = self.metLayerVerticalPin
        self.w_addr_in_side                 = "right"
        self.w_addr_in_section_start        = 0.1
        self.w_addr_in_section_end          = 0.15
        self.w_mask_side                    = "right"
        self.w_mask_section_start           = 0.02
        self.w_mask_section_end             = 0.08
        self.w_mask_metal_layer             = self.metLayerVerticalPin
        self.rd_out_pin_margin              = 0.05
        self.rd_out_metal_layer             = self.metLayerHorizontalPin
        self.rd_out_side                    = "top"
        self.wd_in_pin_margin               = 0.05
        self.wd_in_metal_layer              = self.metLayerHorizontalPin
        self.wd_in_side                     = 'bottom'

#### Private Functions
#---------------------
    def _validate_generated_pin_list(self, pin_list : list, num_pins : int, start : float = None, end : float = None) -> None:
        if len(pin_list) < num_pins:
            traceback.print_stack() 
            if start == None or end == None:
                print(f'ERROR: Not enough valid pins in section {start}-{end}')
            print(f'ERROR: Got {len(pin_list)} pins, needed {num_pins}')
            raise SystemExit("Exiting with error")
        return
    
#### Public Functions
#--------------------
    def get_list_sectioned_r_addr_pins_wrapper(self
                                    , curr_port_num      :  int ) -> list:  
        """ Wrapper for function `write_rport_addr_in_pin`
        Contains special variables `track_rw_port_addr_in` to track how large the read port side is. 
        If there are read and read-write ports in the given SRAM, function `write_rport_addr_in_pin`
        deletes 'rw' key from local dictionary, thus marking `is_rw_port_addr_in_written` variable to False. 
        """

        self.r_addr_padding = self.left_group_padding
        section_start, section_end = self.r_addr_in_section_start, self.r_addr_in_section_end
        section_size = d_get_subtract_round_second_fpoint(section_end, section_start)

        # Track positions
        self.track_rw_port_addr_in_start = self.r_addr_in_section_end

        self.track_rw_port_addr_in_end = d_get_add_round_second_fpoint(self.r_addr_in_section_end
                                        , d_get_subtract_round_second_fpoint(self.w_addr_in_section_end, self.w_addr_in_section_start
            )
        )
        current_section_start = d_get_add_round_second_fpoint(section_start
                                    , d_get_multiply(curr_port_num, section_size
            )
        )
        current_section_end = d_get_add_round_second_fpoint(current_section_start, section_size)
        if curr_port_num > 0:
            if self.r_addr_padding == None:
                print("INFO: No padding specified, using default.")
            pin_list = self.generate_equidistant_sectioned_pins(
                side        = self.r_addr_in_side,
                start       = current_section_start,
                end         = current_section_end,
                metLayer    = self.r_addr_in_metal_layer,
                num_pins    = self.addr_width,
                padding     = self.r_addr_padding,
                new_section = True
            )
            self.r_addr_padding += self.left_group_padding

            # track rw addr in padding
            self.track_rw_port_addr_in_start += self.left_group_padding
            self.track_rw_port_addr_in_end += self.left_group_padding
        else:
            pin_list = self.generate_equidistant_sectioned_pins(
                side     = self.r_addr_in_side, 
                start    = current_section_start, 
                end      = current_section_end,
                metLayer = self.r_addr_in_metal_layer,
                num_pins = self.addr_width
            )
        self._validate_generated_pin_list(pin_list
                                , self.addr_width
                                , start      = current_section_start
                                , end        = current_section_end 
        )
        return pin_list
    
    def get_list_sectioned_r_control_pins_wrapper(self
                                   , curr_port_num          : int
                                   , r_num_control_pins     : int  ) -> list:
        section_start, section_end = self.r_control_section_start, self.r_control_section_end
        section_size = d_get_subtract_round_second_fpoint(section_end, section_start)
            
        current_section_start = d_get_add_round_second_fpoint(section_start
                                            , d_get_multiply(curr_port_num, section_size
            )
        )
        current_section_end = d_get_add_round_second_fpoint(current_section_start, section_size)
        
        if curr_port_num > 0:
            if self.r_port_control_padding == None:
                print("INFO: No padding specified, using default.")
            pin_list = self.generate_equidistant_sectioned_pins(
                side        = self.r_control_side,
                start       = current_section_start,
                end         = current_section_end,
                metLayer    = self.r_control_metal_layer,
                num_pins    = r_num_control_pins,
                padding     = self.r_port_control_padding,
                new_section = True
            )
            self.r_port_control_padding += self.left_group_padding
        else:
            pin_list = self.generate_equidistant_sectioned_pins(
                side     = self.r_control_side, 
                start    = current_section_start, 
                end      = current_section_end,
                metLayer = self.r_control_metal_layer,
                num_pins = r_num_control_pins
            )
        self._validate_generated_pin_list(pin_list
                            , r_num_control_pins
                            , start = current_section_start
                            , end   = current_section_start 
        )
        return pin_list
    
    def get_list_sectioned_w_addr_pins_wrapper(self
                                   , curr_port_num : int
                                   , is_rport_or_rw_port : bool 
                                   , is_rw_port_addr_in_written : bool ) -> list:
        """ Wrapper for function `write_wport_addr_in_pin`

        Handles special case where generated list from `generate_equidistant_sectioned_pins` 
        returns a list of pin slots with PinSlot.side = 'left', only if left side is free.
        """
        
        if is_rport_or_rw_port == False and is_rw_port_addr_in_written == False:
            self.w_addr_in_side = 'left'
            self.w_addr_in_section_start = self.r_addr_in_section_start
            self.w_addr_in_section_end = self.r_addr_in_section_end
            print('INFO: Left side available for write control pins')
        else:
            self.w_addr_in_section_start, self.w_addr_in_section_end = self.track_rw_port_addr_in_start, self.track_rw_port_addr_in_end

        section_start, section_end = self.w_addr_in_section_start, self.w_addr_in_section_end
        section_size = d_get_subtract_round_second_fpoint(section_end, section_start)
        self.track_w_port_end = section_start
        current_section_start = d_get_add_round_second_fpoint(section_start, d_get_multiply(curr_port_num, section_size))
        current_section_end = d_get_add_round_second_fpoint(current_section_start, section_size)
        if curr_port_num > 0:
            if self.w_addr_padding == None:
                print("INFO: No padding specified, using default.")
            pin_list = self.generate_equidistant_sectioned_pins(
                side        = self.w_addr_in_side,
                start       = current_section_start,
                end         = current_section_end,
                metLayer    = self.w_addr_in_metal_layer,
                num_pins    = self.addr_width,
                padding     = self.w_addr_padding,
                new_section = True
            )
            self.w_addr_padding += self.left_group_padding
        else:
            pin_list = self.generate_equidistant_sectioned_pins(
                side     = self.w_addr_in_side, 
                start    = current_section_start, 
                end      = current_section_end,
                metLayer = self.w_addr_in_metal_layer,
                num_pins = self.addr_width
            )
        self._validate_generated_pin_list(pin_list
                            , self.addr_width
                            , start = current_section_start
                            , end   = current_section_end)
        return pin_list
    
    def get_list_sectioned_w_control_pins_wrapper(self
                                   , curr_port_num           : int
                                   , w_num_control_pins      : int
                                   , is_rport_or_rw_port     : bool
                                   , is_rw_port_addr_in_written : bool) -> list:
        if is_rport_or_rw_port == False and is_rw_port_addr_in_written == False:
            self.w_control_side = 'left'
            self.w_control_section_start = self.r_control_section_start
            self.w_control_section_end = self.r_control_section_end
            print('INFO: Left side available for write control pins')
        section_start, section_end = self.w_control_section_start, self.w_control_section_end
        section_size = d_get_subtract_round_second_fpoint(section_end, section_start)
        current_section_start = d_get_add_round_second_fpoint(section_start, d_get_multiply(curr_port_num, section_size))
        current_section_end = d_get_add_round_second_fpoint(current_section_start, section_size)
            
        if curr_port_num > 0:
            if self.w_port_control_padding == None:
                print("INFO: No padding specified, using default.")
            pin_list = self.generate_equidistant_sectioned_pins(
                side        = self.w_control_side,
                start       = current_section_start,
                end         = current_section_end,
                metLayer    = self.w_control_metal_layer,
                num_pins    = w_num_control_pins,
                padding     = self.w_port_control_padding,
                new_section = True
            )
            self.w_port_control_padding += self.left_group_padding

        else:
            pin_list = self.generate_equidistant_sectioned_pins(
                side     = self.w_control_side, 
                start    = current_section_start, 
                end      = current_section_end,
                metLayer = self.w_control_metal_layer,
                num_pins = w_num_control_pins
            )
        self._validate_generated_pin_list(pin_list
                                , w_num_control_pins
                                , start = current_section_start
                                , end   = current_section_end)
        return pin_list
    
    def get_list_sectioned_wmask_pins_wrapper(self
                                   , curr_port_num : int
                                   , total_wmask_in_bits) -> list:
        if curr_port_num > 0:
            if self.w_mask_padding == None:
                print("INFO: No padding specified, using default.")
            pin_list = self.generate_equidistant_sectioned_pins(
                side        = self.w_mask_side,
                start       = self.w_mask_section_start,
                end         = self.w_mask_section_end,
                metLayer    = self.w_mask_metal_layer,
                num_pins    = total_wmask_in_bits,
                padding     = self.w_mask_padding,
                new_section = True
            )
        else:
            pin_list = self.generate_equidistant_sectioned_pins(
                side     = self.w_mask_side, 
                start    = self.w_mask_section_start, 
                end      = self.w_mask_section_end,
                metLayer = self.w_mask_metal_layer,
                num_pins = total_wmask_in_bits
            )
        self._validate_generated_pin_list(pin_list, total_wmask_in_bits, start=self.w_mask_section_start, end=self.w_mask_section_end)
        return pin_list

    def get_equidistant_whole_side_rd_pins_wrapper(self
                                    , side               : str
                                    , metalLayer         : int
                                    , num_pins           : int) -> list:
        pin_list = self.get_equidistant_whole_side_pins(side
                                                    , metalLayer
                                                    , margin=self.rd_out_pin_margin 
                                                    , num_pins=num_pins
                                                    , min_distance=self.min_distance_between_port_pins)

        self._validate_generated_pin_list(pin_list, num_pins)
        return pin_list

    def get_equidistant_whole_side_wd_pins_wrapper(self
                                    , side             : str
                                    , metalLayer       : int
                                    , num_pins         : int) -> list:
        pin_list = self.get_equidistant_whole_side_pins(side
                                                    , metalLayer
                                                    , margin=self.wd_in_pin_margin 
                                                    , num_pins=num_pins
                                                    , min_distance=self.min_distance_between_port_pins)
        self._validate_generated_pin_list(pin_list, num_pins)
        return pin_list

class PinIndexWrapper(LEF_WriteFunctions):
    def __init__(self, mem):
        super().__init__(mem)

#### Private Functions
#---------------------
    def _validate_index_less_than_pin_list(self
                            , pin_id   : str
                            , index    : int
                            , pin_list : list[object] ) -> None:
        if index >= len(pin_list):
            traceback.print_stack()
            print(f'ERROR: {pin_id}: {pin_id} index {index} out of bounds (pin_list has {len(pin_list)} pins)')
            raise SystemExit("Exiting with error")
        return
    
#### Public Functions
#--------------------
    def get_index_write_vertical_input_wrapper(self
                                    , pin_id   : str
                                    , side     : str
                                    , index    : int
                                    , pin_list : list) -> int:
        
        self._validate_index_less_than_pin_list(pin_id, index, pin_list)

        self.write_input_vertical_pin_to_lef(
            pinslot = pin_list[index],
            pin_id  = pin_id,
            side    = side
        )
        return 1

    def get_index_write_horizontal_output_wrapper(self
                                    , pin_id   : str
                                    , side     : str
                                    , index    : int
                                    , pin_list : list) -> int:
        
        self._validate_index_less_than_pin_list(pin_id, index, pin_list)
        
        self.write_output_horizontal_pin_to_lef(
            pinslot = pin_list[index],
            pin_id  = pin_id,
            side    = side
        )
        return 1
    
    def get_index_write_horizontal_input_wrapper(self
                                    , pin_id   : str
                                    , side     : str
                                    , index    : int
                                    , pin_list : list) -> int:
        
        self._validate_index_less_than_pin_list(pin_id, index, pin_list)
        
        self.write_input_horizontal_pin_to_lef(
            pinslot = pin_list[index],
            pin_id  = pin_id,
            side    = side
        )
        return 1