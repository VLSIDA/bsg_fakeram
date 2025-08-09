import math
import re
import os
import sys
from pathlib import Path
from utils.cacti_config import cacti_config
from utils.area import get_macro_dimensions
from utils.custom_tech_parser import tech_parser
################################################################################
# MEMORY CLASS
#
# This class stores the infromation about a specific memory that is being
# generated. This class takes in a process object, the infromation in one of
# the items in the "sram" list section of the json configuration file, and
# finally runs cacti to generate the rest of the data.
################################################################################

class Memory:

  def __init__( self, process, sram_data , output_dir = None, cacti_dir = None, custom_tech_dir = None):
    self.process           = process
    self.sram_data         = sram_data
    self.name              = str(sram_data['name'] ) if 'name'  in sram_data else Exception("Specify name")
    self.width_in_bits     = int(sram_data['width']) if 'width' in sram_data else Exception("Specify width")
    self.depth             = int(sram_data['depth']) if 'depth' in sram_data else Exception("Specify depth")
    self.num_banks         = int(sram_data['banks'])
    self.cache_type        = str(sram_data['type']) if 'type' in sram_data else 'cache'
    self.write_mode        = str(sram_data['write_mode']) if 'write_mode' in sram_data else 'write_first'
    self.width_in_bytes = math.ceil((self.width_in_bits / 8.0))
    self.total_size     = self.width_in_bytes * self.depth

    # Dynamic number ports
    self.r =  get_value(sram_data, 'r' , idx=0, default=0, cast_type=int)
    self.w =  get_value(sram_data, 'w' , idx=0, default=0, cast_type=int)
    self.rw = get_value(sram_data, 'rw', idx=0, default=0, cast_type=int)
    
    # Defatuls to left
    self.r_portside  = get_value(sram_data, 'r' , idx=1, default="left", cast_type=str)
    self.w_portside  = get_value(sram_data, 'w' , idx=1, default="left", cast_type=str)
    self.rw_portside = get_value(sram_data, 'rw', idx=1, default="left", cast_type=str)
    self.is_asymmetric = True if (self.r_portside == 'right' or self.w_portside == 'right' or self.rw_portside == 'right') else False
    
    print('\n##################################################\n')
    print(f'Creating SRAM: {self.name} of width: {self.width_in_bits} and depth: {self.depth}')
    print('\n##################################################\n')
    get_write_granularity(self, sram_data)
    print('\n ')
    print_init(self, total_ports = self.r + self.w + self.rw)
    print('\n')

    if output_dir: # Output dir was set by command line option
      p = str(Path(output_dir).expanduser().resolve(strict=False))
      self.results_dir = os.sep.join([p, self.name])
    else:
      self.results_dir = os.sep.join([os.getcwd(), 'results', self.name])
    if not os.path.exists( self.results_dir ):
      os.makedirs( self.results_dir )

    # Setup CACTI directory
    if cacti_dir:
      self.cacti_dir = cacti_dir
    else:
      self.cacti_dir = os.environ['CACTI_BUILD_DIR']

    # Check if custom tech is specified and validate
    self.use_custom_tech = False
    if self.process.custom_tech:
      yml_dir = os.path.join(custom_tech_dir, self.process.custom_tech + '.yml')
      if os.path.isfile(yml_dir):
        self.use_custom_tech = True
        self.custom_tech_dir = yml_dir
        # print(f"Using custom tech from: {yml_dir}\n")
  
    """
    Run cacti only if using a custom technology
    and using a valid cacti process node for
    overriding specific parameters
    """
    if not self.use_custom_tech or (self.use_custom_tech and hasattr(self.process, 'hybrid') and self.process.hybrid == 'true'):
      print('Running Cacti with overidden values\n') if self.process.hybrid == 'true' else print('Running Cacti\n')
      
      # __run_cacti: shell out to cacti to generate a csv file with more data
      # regarding this memory based on the input parameters from the json
      # configuration file.
      self.__run_cacti()
      
      # Parse CACTI results
      with open( os.sep.join([self.results_dir, 'cacti.cfg.out']), 'r' ) as fid:
        lines = [line for line in fid]
        cacti_data = lines[-1].split(',')

      # Initialize with CACTI data
      self.process.tech_nm                     = int(cacti_data[0])
      self.capacity_bytes              = int(cacti_data[1])
      self.associativity               = int(cacti_data[2])
      self.output_width_bits           = int(cacti_data[3])
      self.access_time_ns              = float(cacti_data[4])
      self.cycle_time_ns               = float(cacti_data[5])
      #self.dyn_search_energy_nj        = float(cacti_data[6]) Unused
      #self.dyn_read_energy_nj          = float(cacti_data[7]) Unused
      self.dyn_write_energy_nj         = float(cacti_data[8])
      self.standby_leakage_per_bank_mW = float(cacti_data[9])
      self.area_mm2                    = float(cacti_data[10])
      self.fo4_ps                      = float(cacti_data[11])
      self.width_um                    = float(cacti_data[12])
      self.height_um                   = float(cacti_data[13])

    # Override with custom tech parameters if available
    if self.use_custom_tech:
      print("Applying custom tech overrides...\n")
      get_custom_tech(self, 
          custom_params = [
          'access_time_ns',
          'cycle_time_ns', 
          'fo4_ps',
          'standby_leakage_per_bank_mW',
          'contacted_poly_pitch_nm',
          'finPitch_nm'
          ])
    else:
      print("Using CACTI parameters only")
      
      """ Cacti defaults """
      self.t_setup_ns           = 0.050 ; # arbitrary 50ps setup
      self.t_hold_ns            = 0.050 ; # arbitrary 50ps hold
      self.pin_dynamic_power_mW = self.dyn_write_energy_nj  # Use CACTI energy as power estimate
      self.cap_input_pf         = 0.005  # Default capacitance
    
      """
      on-fliped assumes metal1 is vertical therefore
      supply pins on metal4 will be horizontal and signal pins will also be on
      metal4. If set to true, supply pins on metal4 will be vertical and signal
      pins will be on metal3.
      """

    
    # Use custom dimensions if available, otherwise use CACTI dimensions
    # if self.use_custom_tech:
    #   self.height_um, self.width_um = get_macro_dimensions(process, sram_data, self.r, self.w, self.rw, self.is_asymmetric)
    
    self.tech_node_um = self.process.tech_nm / 1000.0

    # Adjust to snap
    self.width_um = (math.ceil((self.width_um*1000.0)/self.process.snapWidth_nm)*self.process.snapWidth_nm)/1000.0
    self.height_um = (math.ceil((self.height_um*1000.0)/self.process.snapHeight_nm)*self.process.snapHeight_nm)/1000.0
    self.area_um2 = self.width_um * self.height_um 
    print("Total Bitcell Height is", self.height_um) 
    print("Total Bitcell Width is", self.width_um) 

  # __run_cacti: shell out to cacti to generate a csv file with more data
  # regarding this memory based on the input parameters from the json
  # configuration file.
  def __run_cacti( self ):
    fid = open(os.sep.join([self.results_dir,'cacti.cfg']), 'w')
    fid.write(
        cacti_config.format(
            self.total_size,           # 0. Total memory size
            self.width_in_bytes,       # 1. Width in bytes
            self.rw,                   # 2. Number of read/write ports
            self.r,                    # 3. Number of read ports
            self.w,                    # 4. Number of write ports
            self.process.tech_um,      # 5. Technology node in micrometers
            self.width_in_bytes * 8,   # 6. Width in bits
            self.num_banks,            # 7. Number of banks
            self.cache_type            # 8. Cache type
        )
    )
    fid.close()
    odir = os.getcwd()
    os.chdir(self.cacti_dir )
    cmd = os.sep.join(['.','cacti -infile ']) + os.sep.join([self.results_dir,'cacti.cfg'])
    os.system( cmd)
    os.chdir(odir)

#########################################
# Helper Functions
#########################################

def get_write_granularity(self, sram_data) -> None:
    """ Init write granularity with checks """
    if 'write_granularity' in sram_data:
      self.has_write_mask = True
      self.write_granularity = int(sram_data['write_granularity'])
    else:
       self.has_write_mask = False
       self.write_granularity = self.width_in_bits
       
    if self.has_write_mask:
        if (self.width_in_bits % self.write_granularity == 0):
            self.wmask = self.width_in_bits // self.write_granularity
            print("Has write mask: True")
            print("Write granularity: ", self.write_granularity)
        else:
            raise Exception(f"Invalid write_granularity: width_in_bits ({self.width_in_bits}) is not divisible by write_granularity ({self.write_granularity}).")
    else:
        self.wmask = 0  # No write mask

def get_value(sram_data, key, idx=None, default=None, cast_type=None):
    """ Checks if list key parameter is valid """
    value = sram_data.get(key)
    if isinstance(value, (list, tuple)):
        if idx is not None and len(value) > idx and value[idx] is not None:
            return cast_type(value[idx]) if cast_type else value[idx]
        else:
            return default
    elif value is not None:
        return cast_type(value) if cast_type else value
    else:
        return default

def print_init(self, total_ports) -> None:
    if total_ports == 0:
      raise Exception("SRAM needs at least one port.")
    else:
       print('Total Ports    : ',total_ports)
       print('Num Port R     : ',self.r)
       print('Num Port W     : ',self.w)
       print('Num Port RW    : ',self.rw)
       print(f'Port sides     \n'
             f' R             : {self.r_portside}\n' 
             f' W             : {self.w_portside}\n' 
             f' RW            : {self.rw_portside}'
             )
    
       if self.has_write_mask:
        print('Num Port Wmask :',self.wmask)
       print('Has right port  : %s'%self.is_asymmetric)
       print(f'Flip           : {self.process.flipPins}')


def get_custom_tech(self, custom_params) -> None:
    """ Override parameters if specified in custom tech """
    for param in custom_params:
        value = tech_parser(param, self.custom_tech_dir)
        if value is not None:
            setattr(self, param, value)
            print(f"{param} overridden: {value}")
    
    # Set required custom tech parameters (not in CACTI)
    self.t_setup_ns = tech_parser("t_setup_ns", self.custom_tech_dir)
    self.t_hold_ns = tech_parser("t_hold_ns", self.custom_tech_dir)
    self.pin_dynamic_power_mW = tech_parser("pin_dynamic_power_mW", self.custom_tech_dir)
    self.cap_input_pf = tech_parser("cap_input_pf", self.custom_tech_dir)
    
    # Use custom dimensions if available
    self.height_um, self.width_um = get_macro_dimensions(self)
    
    print("Custom tech parameters applied successfully\n")