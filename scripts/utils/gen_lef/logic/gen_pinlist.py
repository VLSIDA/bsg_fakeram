
import traceback

from utils.gen_lef.decimal_helpers import *
from utils.gen_lef.modules.class_pingrid import PinGrid, PinSlot

################################################################################
# GENERATE PIN LIST HELPERS
#
# Utilizes PinGrid Class and provides helpers to select equidistant pins within 
# a section or across a whole side.
#
# Functions:
#   generate_equidistant_sectioned_pins() - choose pins within [start,end] section
#   get_equidistant_whole_side_pins()     - choose pins across whole side w/ margin
#   _get_side_parameters()                - return slots, dimension, and pin pitch
################################################################################

class GeneratePinList(PinGrid):
    def __init__(self, mem):
        super().__init__(mem)

        # DEBUG PARAMS
        self.gen_whole_side_list_debug : bool  = False
        self.gen_section_list_debug    : bool  = False

#### Private Functions
#---------------------
    def _get_side_parameters(self
                , side : str) -> tuple[list, float, float]:
        """Takes in parameter "side" if valid

        Returns
            available_slots - side's all available slots

            dimension       - side's dimension (height/width)

            pin_pitch       - side's x or y pitch
        """
        if side == 'top':
            available_slots = self.list_top_pins
            dimension = self.w
            pin_pitch = self.x_pin_pitch
        elif side == 'bottom':
            available_slots = self.list_bot_pins
            dimension = self.w
            pin_pitch = self.x_pin_pitch
        elif side == 'left':
            available_slots = self.list_left_pins
            dimension = self.h
            pin_pitch = self.y_pin_pitch
        elif side == 'right':
            available_slots = self.list_right_pins
            dimension = self.h
            pin_pitch = self.y_pin_pitch
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'top', 'bottom', 'left', or 'right'")
        return available_slots, dimension, pin_pitch
    
#### Public Functions
#--------------------
    def generate_equidistant_sectioned_pins(self
                                    , side        : str
                                    , start       : float
                                    , end         : float
                                    , metLayer    : int
                                    , num_pins    : float = None
                                    , new_section : bool  = None
                                    , padding     : float = None) -> list[object]:
        """
        Filter available slots in section, then distribute num_pins evenly across those indices.
        Validates against available slots created by the class.
        """
        if self.gen_section_list_debug:
            print("="*60)
            print(f"\nStarting Equidistant Section Debug CALLED: {self.num_gen_section_calls}\n")
            print(f"side: {side}")
            print(f"start: {start}")
            print(f"end: {end}")
            print(f"metLayer: {metLayer}")
            print(f"num_pins: {num_pins}")
            print(f"new_section: {new_section}")
            print(f"padding: {padding}\n")
            print("="*60)
            self.num_gen_section_calls += 1
            
        if new_section is None:
            new_section = False

        if padding is None:
            padding = 0.001

        pin_list = []
        available_slots, dimension, pin_pitch = self._get_side_parameters(side)
        pin_width = self.y_pin_width if (side == 'left' or side == 'right') else self.x_pin_width

        if new_section == True:
            actual_start = d_get_multiply(dimension, d_get_add(start, padding))
            actual_end = d_get_multiply(dimension, d_get_add(end, padding))
        else:
            actual_start = d_get_multiply(dimension, start)
            actual_end = d_get_multiply(dimension, end)
        section_length = d_get_subtract(actual_end, actual_start)

        # Filter valid slots
        valid_slots = []
        for slot in available_slots:
            
            # Valid if between starting and end points of SRAM, 
            # if unused and not on same metal layer
            if (actual_start <= slot.slot <= actual_end and 
                slot.used == False and 
                slot.metLayer == metLayer):
                valid_slots.append(slot)

        if not valid_slots:
            traceback.print_stack()
            raise SystemExit(
                f"ERROR: Pins at {side} Calling num_pins: {num_pins}\n"
                f"ERROR: No valid slots in the specified section!\n"
            )

        if self.gen_section_list_debug:
            unique_coords = set(slot.slot for slot in valid_slots)
            print(f"DEBUG: Unique coordinates in valid_slots: {len(unique_coords)}")
            print(f"DEBUG: Total valid_slots: {len(valid_slots)}")
            if len(unique_coords) != len(valid_slots):
                print("WARNING: Duplicate coordinates found in valid_slots!")

        if num_pins is None:
            num_pins = int(d_get_divide(section_length, pin_pitch))
            if num_pins < 1:
                num_pins = 1
            num_pins = min(num_pins, len(valid_slots))
        else:
            num_pins = min(num_pins, len(valid_slots))
        
        if num_pins <= 0:
            return pin_list

        # Divide evenly across available slot indices
        if num_pins >= len(valid_slots):
            selected_indices = list(range(len(valid_slots)))
        elif num_pins == 1:
            selected_indices = [len(valid_slots) // 2]
        else:
            selected_indices = []
            total_slots = len(valid_slots)
            
            if (total_slots - 1) % (num_pins - 1) == 0:
                step = (total_slots - 1) // (num_pins - 1)
                for i in range(num_pins):
                    if i == num_pins - 1:
                        idx = total_slots - 1
                    else:
                        idx = i * step
                    selected_indices.append(idx)
            else:
                step_size = d_get_divide(d_get_subtract(total_slots, 1), d_get_subtract(num_pins, 1))
                for i in range(num_pins):
                    if i == 0:
                        idx = 0
                    elif i == num_pins - 1:
                        idx = total_slots - 1
                    else:
                        idx = d_get_round_to_int(d_get_multiply(i, step_size))
                    selected_indices.append(idx)
            
        selected_slots = [valid_slots[i] for i in selected_indices]
        
        # Debug output
        if self.gen_section_list_debug:
            print(f"DEBUG: Section {start:.3f}-{end:.3f} = {actual_start:.3f}-{actual_end:.3f}, length={section_length:.3f}")
            print(f"DEBUG: Found {len(valid_slots)} valid slots in section")
            print(f"DEBUG: Requesting {num_pins} pins from {len(valid_slots)} available slots")
            print(f"DEBUG: Even distribution indices: {selected_indices}")
            print(f"DEBUG: Final selected indices: {selected_indices}")
            selected_positions = [d_get_add(s.slot, d_get_divide(pin_width, 2)) for s in selected_slots]
            print(f"DEBUG: Selected {len(selected_slots)} slot positions: {[f'{p:.3f}' for p in selected_positions]}")
            if len(selected_positions) > 1:
                spacings = [d_get_subtract(selected_positions[i+1], selected_positions[i]) for i in range(len(selected_positions)-1)]
                print(f"DEBUG: Spacings between pins: {[f'{s:.3f}' for s in spacings]}")
                print(f"DEBUG: Min spacing: {min(spacings):.3f}, Max spacing: {max(spacings):.3f}")
                spacing_range = d_get_subtract(max(spacings), min(spacings))
                print(f"DEBUG: Spacing uniformity (max-min): {spacing_range:.3f}")
        
        # Create slot object in selected slots
        for slot in selected_slots:
            new_slot = PinSlot(
                slot=slot.slot,
                used=True,
                side=side,
                metLayer=metLayer
            )
            pin_list.append(new_slot)
            slot.used = True
        return pin_list

    def get_equidistant_whole_side_pins(self
                                , side         : str
                                , metLayer     : int
                                , margin       : float = None
                                , num_pins     : int   = None
                                , pin_list     : list  = None
                                , min_distance : int   = None) -> list[object]:
        """
        Generate equidistant pins across whole side with margin.
        """
        available_slots, dimension, pin_pitch = self._get_side_parameters(side)
        
        if pin_list is None:
            pin_list = []
        if margin is None:
            margin = 0.1
        if min_distance is None:
            min_distance = 1
        
        section_start = margin
        section_end = d_get_subtract(1, margin)
        actual_start = d_get_multiply(dimension, section_start)
        actual_end = d_get_multiply(dimension, section_end)
        section_length = d_get_subtract(actual_end, actual_start)
        
        # Filter valid slots
        valid_slots = []
        for slot in available_slots:

            # Valid if between starting and end points of SRAM, 
            # if unused and not on same metal layer
            if (actual_start <= slot.slot <= actual_end and 
                slot.used == False and 
                slot.metLayer == metLayer):
                valid_slots.append(slot)
            
        if not valid_slots:
            traceback.print_stack()
            raise SystemExit("ERROR: No valid slots in the specified section!")
        
        if num_pins is None:
            num_pins = int(d_get_divide(section_length, pin_pitch))
            if num_pins < 1:
                num_pins = 1
            num_pins = min(num_pins, len(valid_slots))
        else:
            num_pins = min(num_pins, len(valid_slots))
        
        if num_pins <= 0:
            return pin_list

        selected_slots = []
        
        # Equidistant placement
        if num_pins == 1:
            middle_idx = len(valid_slots) // 2
            selected_slots.append(valid_slots[middle_idx])
        else:
            step = (len(valid_slots) - 1) / (num_pins - 1)
            for i in range(num_pins):
                idx = int(round(i * step))
                selected_slots.append(valid_slots[idx])
        
        for slot in selected_slots:
            new_slot = PinSlot(
                slot=slot.slot,
                used=True,
                side=side,
                metLayer=metLayer
            )
            pin_list.append(new_slot)
            for orig_slot in available_slots:
                if abs(orig_slot.slot - slot.slot) < 0.001:
                    orig_slot.used = True
                    break
        
        if self.gen_whole_side_list_debug:
            print(f"DEBUG: Selected {len(selected_slots)} equidistant pins for side {side}")
            positions = [slot.slot for slot in selected_slots]
            print(f"DEBUG: Pin positions: {[f'{p:.3f}' for p in positions]}")
        
        return pin_list
