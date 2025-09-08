
import traceback

from collections import deque
from utils.gen_lef.decimal_helpers import *
from utils.gen_lef.modules.class_pingrid import PinGrid
from utils.gen_lef.logic.gen_pinlist import GeneratePinList
from utils.gen_lef.logic.pin_wrappers import PinIndexWrapper, PinListWrapper

################################################################################
# GENERATE PORT CLASS
#
# This class generates SRAM port pin placement (control / address / data),
# using class PinListWrapper to build prevalidated slot lists and 
# class PinIndexWrapper to write LEF pins by index; tech params via
# class LEF_PinGrid.
#
# Functions:
#   write_rport_control_pin()       - Writes pin rport control pin
#   write_rport_addr_in_pin()       - Writes pin rport addr in pin
#   write_rport_rd_out_pin()        - Writes pin rport rd out pin
#   write_wport_control_pin()       - Writes pin wport control pin
#   write_wport_addr_in_pin()       - Writes pin wport addr in pin
#   write_wport_wd_in_pin()         - Writes pin wport wd in pin
#   write_wmask_in_pin()            - Writes pin wmask in pin
#   _is_overlapped(id, pin_list, i) - Validates pin if overlapped
#   generate_ports()                - Order of write port functions
#
# Notes:
#   - Threshold fields are defined but currently unused (reserved for tuning).
#   - _is_overlapped() aborts on same-slot/same-layer collisions.
################################################################################

class GeneratePorts(GeneratePinList
            , PinIndexWrapper
            , PinListWrapper):
    def __init__(self, mem):
        super().__init__(mem)

        self.r_ports_dict               = {"rw": self.num_rwports, "r": self.num_rports}
        self.w_ports_dict               = {"rw": self.num_rwports, "w": self.num_wports}
        self.r_control_pins             = ["clk", "ce_in"]
        self.w_control_pins             = ["clk", "ce_in", "we_in"]
        self.is_rw_port_addr_in_written = False
        self.w_num_control_pins         = len(self.w_control_pins)
        self.r_num_control_pins         = len(self.r_control_pins)
        self.w_control_threshold_left   = 3     # Unused
        self.r_control_threshold_left   = 3     # Unused
        self.r_addr_in_threshold_left   = 6     # Unused
        self.w_addr_in_threshold_left   = 6     # Unused
        self.is_rd_out_threshold        = False # Unused
        self.w_is_addr_threshold        = False # Unused
        self.r_is_addr_threshold        = False # Unused
        self.r_is_control_threshold     = False # Unused
        self.w_is_control_threshold     = False # Unused

        self.sides = ['left'
                , 'top'
                , 'right'
                , 'bottom'
                ]
        
        self.ports_written = self._init_ports_written()
        
        self.is_rport_and_rw_port = True if (self.r_ports_dict['r'] >= 1 and self.r_ports_dict['rw'] >= 1) else False
        self.is_rport_or_rw_port = True if (self.r_ports_dict['r'] >= 1 or self.r_ports_dict['rw'] >= 1) else False
        self.is_rwport_control_written = False

        # FIXME want to move all 'is rw port written' logic to the wrappers.
        # wrappers should handle those kind of cases

#### Private Functions
#---------------------
    def _init_ports_written(self
                , ports_written: dict = None
                , all_available_pins: list = ['clk', 'ce_in', 'addr_in', 'rd_out', 'we_in', 'wd_in']) -> dict[str, bool]:
        """
        Initialize port dictionary to track if ports are written.
        Returns dictionary of all port pins with boolean values set to False.
        """
        if ports_written is None:
            ports_written = {}
        
        # Define which pins are excluded for each port type
        pin_exclusions = {
            'r': {'we_in', 'wd_in'},
            'w': {'rd_out'},
            'rw': set()  # No exclusions for read-write ports
        }
        
        # Define which pins need bit indexing
        bit_indexed_pins = {
            'addr_in': self.addr_width,
            'rd_out': self.bits,
            'wd_in': self.bits
        }
        
        for port_type, num_ports in self.mem.sram_data['ports'].items():
            excluded_pins = pin_exclusions.get(port_type, set())
            for port_num in range(num_ports):
                for pin in all_available_pins:
                    if pin in excluded_pins:
                        continue
                    base_name = f"{port_type}{port_num}_{pin}"
                    if pin in bit_indexed_pins:
                        bit_count = bit_indexed_pins[pin]
                        for bit in range(bit_count):
                            ports_written[f"{base_name}[{bit}]"] = False
                    else:
                        ports_written[base_name] = False
        return ports_written
    
    def _is_port_written(self
                , port_name       :  str
                , port_type_index :  int
                , pin             :  str
                , pin_bit_index   :  int = None) -> bool:  
        """ returns true if given port value is true """
        if pin_bit_index != None:
            return self.ports_written[f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]"] == True
        else:
            return self.ports_written[f"{port_name}{port_type_index}_{pin}"] == True
    
    def _is_overlapped(self
            , id       :  str
            , pin_list :  list[object]
            , i        :  int ) -> None :  
        """ checks if pin is overlapped with any previous/current pins"""
        current_pin = pin_list[i]
        for j in range(i):
            other_pin = pin_list[j]
            if (abs(current_pin.slot - other_pin.slot) < 0.001 and 
                current_pin.metLayer == other_pin.metLayer):
                traceback.print_stack()
                print(f"ERROR: {id} overlaps with {pin_list[j]} at slot {current_pin.slot}, layer {current_pin.metLayer}")
                raise SystemExit('Exiting with error.')

#### Public Functions
#--------------------
    def write_rport_control_pin(self):
        """
        Write read and read-write port control pins based on threshold, banks, and group spacing.
        Handles special case if there are any read-write ports of the given sram will delete from
        local dictionary, then marking `is_rwport_control_written` to False, leaving 
        `write_wport_control_pin` function to write rw port to the right side. 
        """
        total_r_port_control_pins = 0 
        r_ports_dict = self.r_ports_dict.copy()

        if self.is_rport_and_rw_port:
            del r_ports_dict["rw"]
            self.is_rwport_control_written = False

        total_r_ports = sum(r_ports_dict.values())
        for curr_port_num in range(0, total_r_ports):
            pin_list = self.get_list_sectioned_r_control_pins_wrapper(
                                curr_port_num
                                , self.r_num_control_pins
            )
            port_name = None
            port_type_index = None
            current_port_index = 0
            for key, value in r_ports_dict.items():
                if curr_port_num < current_port_index + value:
                    port_name = key
                    port_type_index = curr_port_num - current_port_index
                    break
                current_port_index += value            

            if port_name is None:
                traceback.print_stack() 
                print(f"ERROR: Could not determine port name for port index {curr_port_num}")
                raise SystemExit("Exiting with error")

            for i, pin in enumerate(self.r_control_pins):
                if self._is_port_written(port_name, port_type_index, pin):
                    continue
                self._is_overlapped(f"{port_name}{port_type_index}_{pin}", pin_list, i)

                pin_used = self.get_index_write_vertical_input_wrapper(
                    pin_id   = f"{port_name}{port_type_index}_{pin}", 
                    side     = self.r_control_side,
                    index    = i,
                    pin_list = pin_list
                )
                self.ports_written[f"{port_name}{port_type_index}_{pin}"] = True # mark here as used
                total_r_port_control_pins += pin_used
                
                if total_r_port_control_pins > self.r_control_threshold_left:
                    pass 
            if self.banks > 1:
                pass
        print(f"Total read control pins placed: {total_r_port_control_pins}")
        return

    def write_rport_addr_in_pin(self):
        """
        Write read and read-write port address input pins based on threshold, banks, and group spacing.
        Handles special case if there are any read-write ports of the given sram will delete from
        local dictionary, then marking `is_rwport_control_written` to False, leaving 
        `write_wport_addr_in_pin` function to write rw port to the right side. 
        """
        total_r_addr_in_pins = 0 

        # Delete from local r port dictionary
        # Let w_addr_in generate rw's w_addr_in
        # Assuming rports has priority in generation
        r_ports_dict = self.r_ports_dict.copy()
        if self.is_rport_and_rw_port:
            del r_ports_dict["rw"]
            self.is_rw_port_addr_in_written = False

        total_r_ports = sum(r_ports_dict.values())

        for curr_port_num in range(0, total_r_ports):
            pin_list = self.get_list_sectioned_r_addr_pins_wrapper(
                curr_port_num, 
            )
            port_name = None
            port_type_index = None
            current_port_index = 0
            for key, value in r_ports_dict.items():
                if curr_port_num < current_port_index + value:
                    port_name = key
                    port_type_index = curr_port_num - current_port_index  # Offset within this port type
                    break
                current_port_index += value
            
            if port_name is None:
                print(f"ERROR: Could not determine port name for port index {curr_port_num}")
                traceback.print_stack() 
                raise SystemExit("Exiting with error")
            
            for pin_bit_index in range(0, self.addr_width):
                if self._is_port_written(port_name
                            , port_type_index
                            , "addr_in"
                            , pin_bit_index=pin_bit_index):
                    continue
                self._is_overlapped(f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]", pin_list, pin_bit_index)

                pin_used = self.get_index_write_vertical_input_wrapper(
                    pin_id   = f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]",
                    side     = self.r_addr_in_side,
                    index    = pin_bit_index,
                    pin_list = pin_list
                )
                self.ports_written[f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]"] = True # mark here as used
                total_r_addr_in_pins += pin_used

                # if port_name == 'rw':
                #     self.is_rw_port_addr_in_written = True
                
                if total_r_addr_in_pins > self.r_addr_in_threshold_left:
                    """
                    break when pins exceeded area of control logic
                    section area.
                    """
                    # self.r_control_side = 'right'
                    # section_start, section_end = 0.8 , 0.85
                    # self.r_is_control_threshold = True
                    pass 
            
            if self.banks == 2 or self.banks == 4:
                """
                TODO: Bank logic
                """
                # self.r_control_side = 'left'
                # section_start += 0.4
                # section_end += 0.4
                pass
        
        print(f"Total address input pins placed: {total_r_addr_in_pins}")
        return

    def write_rport_rd_out_pin(self):
        """
        Write read and read-write port data output pins based on threshold, banks, and group spacing.
        Handles pin assignment across multiple ports by traversing each bit of the ports data width.
        Ordering goes: rw ports before r ports, and avoids overlap by validating each
        generated pin location before insertion.        
        """
        used_r_rd_out_pins = 0
        total_rd_out_port_bits = sum(self.r_ports_dict.values()) * self.bits

        pin_list = self.get_equidistant_whole_side_rd_pins_wrapper(
            self.rd_out_side, self.rd_out_metal_layer, total_rd_out_port_bits
        )

        # highest port index first (rw1, rw0, then r0, etc.)
        instances = []
        for key, nports in self.r_ports_dict.items():
            for port_idx in range(nports - 1, -1, -1):  # reversed so rw1 comes before rw0
                instances.append([key, port_idx, 0])    # [key, port_idx, next_bit]

        q = deque(instances)
        pin_start_index = 0

        while q:
            key, port_idx, next_bit = q.popleft()
            self._is_overlapped(f"{key}{port_idx}_rd_out[{next_bit}]", pin_list, pin_start_index)
            pin_used = self.get_index_write_horizontal_output_wrapper(
                pin_id   = f"{key}{port_idx}_rd_out[{next_bit}]",
                side     = self.rd_out_side,
                index    = pin_start_index,
                pin_list = pin_list,
            )
            used_r_rd_out_pins += pin_used
            pin_start_index += 1
            next_bit += 1
            if next_bit < self.bits:
                q.append([key, port_idx, next_bit]) 

### Generate Write
    def write_wport_control_pin(self):
        """
        Write write and read-write port control pins based on threshold, banks, and group spacing.
        Handles special case when read-write ports of the given sram if `is_rwport_control_written`
        is set to True, this function will not write read-write control pin to right side.
        Additionally avoids overlap by validating each generated pin location before insertion.        
        """
        total_w_port_control_pins = 0 
        w_port_control_padding = self.left_group_padding
        w_ports_dict = self.w_ports_dict.copy()

        if self.is_rwport_control_written:
            del w_ports_dict['rw']

        total_w_ports = sum(w_ports_dict.values())
        for curr_port_num in range(0, total_w_ports):

            pin_list = self.get_list_sectioned_w_control_pins_wrapper(curr_port_num
                                                        , self.w_num_control_pins
                                                        , self.is_rport_or_rw_port
                                                        , self.is_rw_port_addr_in_written
            )
            w_port_control_padding += self.left_group_padding

            port_name = None
            port_type_index = None
            current_port_index = 0
            
            for key, value in w_ports_dict.items():
                if curr_port_num < current_port_index + value:
                    port_name = key
                    port_type_index = curr_port_num - current_port_index
                    break
                current_port_index += value
            
            if port_name is None:
                print(f"ERROR: Could not determine port name for port index {curr_port_num}")
                traceback.print_stack() 
                raise SystemExit("Exiting with error")
                        
            for i, pin in enumerate(self.w_control_pins):
                if self._is_port_written(port_name, port_type_index, pin):
                    continue
                self._is_overlapped(f"{port_name}{port_type_index}_{pin}", pin_list, i)

                pin_used = self.get_index_write_vertical_input_wrapper(
                    pin_id   = f"{port_name}{port_type_index}_{pin}", 
                    side     = self.w_control_side,
                    index    = i,
                    pin_list = pin_list
                )
                self.ports_written[f"{port_name}{port_type_index}_{pin}"] = True # mark here as used
                total_w_port_control_pins += pin_used

                if total_w_port_control_pins > self.w_control_threshold_left:
                    pass 
            if self.banks > 1:
                pass
        print(f"Total write control pins placed: {total_w_port_control_pins}")
        return

    def write_wport_addr_in_pin(self):
        """
        Write write and read-write port address in pins based on threshold, banks, and group spacing.
        Handles special case if there are any read-write ports of the given sram will delete from
        local dictionary, then marking `is_rwport_addr_in_written` to False, leaving 
        `write_wport_addr_in_pin` function to write rw port to the right side. 
        Additionally avoids overlap by validating each generated pin location before insertion.        
        """
        if self.is_rw_port_addr_in_written == True:
            print("INFO: rwport write attempt")
            return

        total_w_addr_in_pins = 0 
        total_w_ports = sum(self.w_ports_dict.values())
        for curr_port_num in range(0, total_w_ports):
            pin_list = self.get_list_sectioned_w_addr_pins_wrapper(
                curr_port_num, 
                self.is_rport_or_rw_port,
                self.is_rw_port_addr_in_written
            )
            port_name = None
            port_type_index = None
            current_port_index = 0
            for key, value in self.w_ports_dict.items():
                if curr_port_num < current_port_index + value:
                    port_name = key
                    port_type_index = curr_port_num - current_port_index  # Offset within this port type
                    break
                current_port_index += value
            
            if port_name is None:
                print(f"ERROR: Could not determine port name for port index {curr_port_num}")
                traceback.print_stack() 
                raise SystemExit("Exiting with error")
            
            for pin_bit_index in range(0, self.addr_width):
                if self._is_port_written(port_name
                            , port_type_index
                            , "addr_in"
                            , pin_bit_index=pin_bit_index):
                    continue
                self._is_overlapped(f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]", pin_list, pin_bit_index)

                pin_used = self.get_index_write_vertical_input_wrapper(
                    pin_id   = f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]",
                    side     = self.w_addr_in_side,
                    index    = pin_bit_index,
                    pin_list = pin_list
                )
                self.ports_written[f"{port_name}{port_type_index}_addr_in[{pin_bit_index}]"] = True # mark here as used
                total_w_addr_in_pins += pin_used
                
                if total_w_addr_in_pins > self.w_addr_in_threshold_left:
                    pass 
            
            if self.banks == 2 or self.banks == 4:
                pass
        
        print(f"Total address input pins placed: {total_w_addr_in_pins}")
        return
    
    def write_wport_wd_in_pin(self):
        """
        Write write and read-write port data output pins based on threshold, banks, and group spacing.
        Handles pin assignment across multiple ports by traversing each bit of the ports data width.
        Ordering goes: rw ports before w ports, and avoids overlap by validating each
        generated pin location before insertion.    
        """
        used_w_wd_in_pins = 0
        total_wd_in_port_bits = sum(self.w_ports_dict.values()) * self.bits

        # top is free for wd in
        if self.is_rport_or_rw_port == False:
            self.wd_in_side = "top"

        pin_list = self.get_equidistant_whole_side_wd_pins_wrapper(
            self.wd_in_side, self.wd_in_metal_layer, total_wd_in_port_bits
        )
        
        # highest port index first (rw1, rw0, then w0, etc)
        instances = []
        for key, nports in self.w_ports_dict.items():
            for port_idx in range(nports - 1, -1, -1):  # reversed so rw1 comes before rw0
                instances.append([key, port_idx, 0])

        q = deque(instances)
        pin_start_index = 0

        while q:
            key, port_idx, next_bit = q.popleft()
            self._is_overlapped(f"{key}{port_idx}_wd_in[{next_bit}]", pin_list, pin_start_index)
            pin_used = self.get_index_write_horizontal_input_wrapper(
                pin_id   = f"{key}{port_idx}_wd_in[{next_bit}]",
                side     = self.wd_in_side,
                index    = pin_start_index,
                pin_list = pin_list,
            )
            used_w_wd_in_pins += pin_used
            pin_start_index += 1

            next_bit += 1
            if next_bit < self.bits:
                q.append([key, port_idx, next_bit]) 
        return

    def write_wmask_in_pin(self):
        if not self.has_wmask:
            return

        total_wmask_in_bits = sum(self.w_ports_dict.values()) * self.num_wmasks
        used_wmask_pins = 0
        pin_bit_index = 0

        for key, curr_port_num in self.w_ports_dict.items():
            pin_list = self.get_list_sectioned_wmask_pins_wrapper(curr_port_num
                                                        , total_wmask_in_bits
            )

            for port_num in range(curr_port_num):
                for bit in range(self.num_wmasks):
                    self._is_overlapped(f"{key}{port_num}_wmask_in[{bit}]", pin_list, bit)
                    pin_used = self.get_index_write_vertical_input_wrapper(
                        pin_id   = f"{key}{port_num}_wmask_in[{bit}]",
                        side     = self.w_mask_side,
                        index    = pin_bit_index,
                        pin_list = pin_list,
                    )
                    used_wmask_pins += pin_used
                    pin_bit_index += 1
        return

    def generate_ports(self):
        for side in self.sides:
            if side == 'left': # pin creation on sides bottom up
                self.write_rport_control_pin()
                self.write_rport_addr_in_pin()
            if side == 'top':
                self.write_rport_rd_out_pin()
            if side == 'right':
                self.write_wport_control_pin()
                self.write_wport_addr_in_pin()
                self.write_wmask_in_pin()
            if side == 'bottom':
                self.write_wport_wd_in_pin()

        self.debug_check_ports = True
        if self.debug_check_ports:
            with open("validate_ports.txt", 'w') as f:
                for key,value in self.ports_written.items():
                    print(f'key,value: {key} {value}'
                        , file=f
                    )

    
