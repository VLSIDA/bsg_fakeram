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
    # Main Memory Parameters
    self.process           = process
    self.sram_data         = sram_data
    self.name              = str(sram_data['name'] ) if 'name'  in sram_data else None
    self.width_in_bits     = int(sram_data['width']) if 'width' in sram_data else None
    self.depth             = int(sram_data['depth']) if 'depth' in sram_data else None
    self.width_in_bytes    = math.ceil((self.width_in_bits / 8.0))
    self.total_size        = self.width_in_bytes * self.depth

    # Optional Parameters
    self.num_banks                   = int(sram_data['banks'])
    self.cache_type                  = str(sram_data['type']) if 'type' in sram_data else 'cache'
    self.write_mode                  = str(sram_data['write_mode']) if 'write_mode' in sram_data else 'write_first'
    self.column_mux_factor           = int(sram_data['column_mux_factor_override']) if 'column_mux_factor_override' in sram_data else self.process.column_mux_factor
    self.column_mux_factor_overriden = True if 'column_mux_factor_override' in sram_data else False

    # Dynamic number ports
    self.r =  get_value(sram_data, 'r' , idx=0, default=0, cast_type=int)
    self.w =  get_value(sram_data, 'w' , idx=0, default=0, cast_type=int)
    self.rw = get_value(sram_data, 'rw', idx=0, default=0, cast_type=int)
    
    # Defatuls to left
    self.r_portside    = get_value(sram_data, 'r' , idx=1, default="left", cast_type=str)
    self.w_portside    = get_value(sram_data, 'w' , idx=1, default="left", cast_type=str)
    self.rw_portside   = get_value(sram_data, 'rw', idx=1, default="left", cast_type=str)
    self.is_asymmetric = True if (self.r_portside == 'right' or self.w_portside == 'right' or self.rw_portside == 'right') else False
    
    self._initialize_defaults()
    self._get_write_granularity()
    self._cacti_init(output_dir, cacti_dir, custom_tech_dir)
    self._print_init(total_ports = self.r + self.w + self.rw)

  def _initialize_defaults(self):
    self.temp_access_time_ns              = None
    self.temp_cycle_time_ns               = None
    self.temp_fo4_ps                      = None
    self.temp_dyn_write_energy_nj         = None
    self.temp_standby_leakage_per_bank_mW = None
    self.temp_pin_dynamic_power_mW        = None
    self.access_time_ns                   = None
    self.cycle_time_ns                    = None
    self.fo4_ps                           = None
    self.dyn_write_energy_nj              = None
    self.standby_leakage_per_bank_mW      = None
    self.pin_dynamic_power_mW             = None
    self.t_setup_ns                       = 0.050 # arbitrary 50ps setup
    self.t_hold_ns                        = 0.050 # arbitrary 50ps hold
    self.cap_input_pf                     = 0.005
    self.contacted_poly_pitch_nm          = None
    self.finPitch_nm                      = None
    self.H0_TRACKS                        = None
    self.W0_POLYS                         = None
    self.DH_READ                          = None
    self.DW_READ                          = None
    self.DH_WRITE                         = None
    self.DW_WRITE                         = None
    self.DH_RW                            = None
    self.DW_RW                            = None
    self.custom_tech_dir                  = None

  def _get_write_granularity(self):
    """ Init write granularity with checks """
    if 'write_granularity' in self.sram_data:
      self.has_write_mask = True
      self.write_granularity = int(self.sram_data['write_granularity'])
    else:
       self.has_write_mask = False
       self.write_granularity = self.width_in_bits
       
    if self.has_write_mask:
        if (self.width_in_bits % self.write_granularity == 0):
            self.wmask = self.width_in_bits // self.write_granularity
        else:
            raise Exception(f"Invalid write_granularity: width_in_bits ({self.width_in_bits}) is not divisible by write_granularity ({self.write_granularity}).")
    else:
        self.wmask = 0  # No write mask

  def _print_init(self, total_ports):
    if total_ports == 0:
      raise Exception("SRAM needs at least one port.")
    print('\n ')
    print('\n##################################################\n')
    print(f'Creating SRAM: {self.name} of width: {self.width_in_bits} and depth: {self.depth}')
    print('\n##################################################\n')
    print("Applying custom tech overrides...\n") if self.process.hybrid is False else print("Applying hybrid overrides...")
    print('Hybrid checking   : ', self.process.hybrid)
    print(f'column_mux_factor overriden? {self.column_mux_factor_overriden}')
    if self.column_mux_factor_overriden:
      print(f'Column mux overriden: {self.column_mux_factor}')
    print(f'Total Ports       : {total_ports} \n'
          f'Num Port R        : {self.r} \n'
          f'Num Port W        : {self.w} \n'
          f'Num Port RW       : {self.rw} \n'
          f'Port sides     \n'
          f' R                : {self.r_portside}\n' 
          f' W                : {self.w_portside}\n' 
          f' RW               : {self.rw_portside}'
            )
  
    if self.has_write_mask:
        print(f'Has write mask    : True\n'
              f'Num Port Wmask    : {self.wmask}\n'
              f'Write granularity : {self.write_granularity}\n')
        
    print('Has right port    : %s'%self.is_asymmetric)
    print(f'Flip              : {self.process.flipPins}\n')

    print(f'access_time_ns                   : {self.access_time_ns}\n'
          f'cycle_time_ns                    : {self.cycle_time_ns}\n'
          f'fo4_ps                           : {self.fo4_ps}\n'
          f'dyn_write_energy_nj              : {self.dyn_write_energy_nj or None}\n'
          f'standby_leakage_per_bank_mW      : {self.standby_leakage_per_bank_mW}\n'
          f'pin_dynamic_power_mW             : {self.pin_dynamic_power_mW}\n'
          f't_setup_ns                       : {self.t_setup_ns}\n'
          f't_hold_ns                        : {self.t_hold_ns}\n'
          f'cap_input_pf                     : {self.cap_input_pf}\n'
          f'contacted_poly_pitch_nm          : {self.contacted_poly_pitch_nm}\n'
          f'finPitch_nm                      : {self.finPitch_nm}\n'
          f'H0_TRACKS                        : {self.H0_TRACKS}\n'
          f'W0_POLYS                         : {self.W0_POLYS}\n'
          f'DH_READ                          : {self.DH_READ}\n'
          f'DW_READ                          : {self.DW_READ}\n'
          f'DH_WRITE                         : {self.DH_WRITE}\n'
          f'DW_WRITE                         : {self.DW_WRITE}\n'
          f'DH_RW                            : {self.DH_RW}\n'
          f'DW_RW                            : {self.DW_RW}\n\n'
          f'Total height                     : {self.height_um}\n'
          f'Total width                      : {self.width_um}\n')
    print('\n ')

  def _get_custom_tech(self):
    """ Override parameters if specified in custom tech """    
    # Set required custom tech parameters can be overridden by cacti 
    # else use original cacti values
    self.temp_access_time_ns              = tech_parser("access_time_ns", self.custom_tech_dir)
    self.temp_cycle_time_ns               = tech_parser("cycle_time_ns", self.custom_tech_dir)
    self.temp_fo4_ps                      = tech_parser("fo4_ps", self.custom_tech_dir)
    self.temp_dyn_write_energy_nj         = tech_parser("dyn_write_energy_nj", self.custom_tech_dir)
    self.temp_standby_leakage_per_bank_mW = tech_parser("standby_leakage_per_bank_mW", self.custom_tech_dir)
    self.temp_pin_dynamic_power_mW        = tech_parser("pin_dynamic_power_mW", self.custom_tech_dir)
    # Not in cacti, uses default values from original fakeram 
    self.t_setup_ns                       = tech_parser("t_setup_ns", self.custom_tech_dir) or 0.050
    self.t_hold_ns                        = tech_parser("t_hold_ns", self.custom_tech_dir) or 0.050
    self.cap_input_pf                     = tech_parser("cap_input_pf", self.custom_tech_dir) or 0.005
    # Required parameter for invalid tech nodes in cacti
    self.contacted_poly_pitch_nm          = tech_parser("contacted_poly_pitch_nm", self.custom_tech_dir)
    self.finPitch_nm                      = tech_parser("finPitch_nm", self.custom_tech_dir)
    self.H0_TRACKS                        = tech_parser("H0_TRACKS", self.custom_tech_dir)
    self.W0_POLYS                         = tech_parser("W0_POLYS", self.custom_tech_dir)
    self.DH_READ                          = tech_parser("DH_READ", self.custom_tech_dir)
    self.DW_READ                          = tech_parser("DW_READ", self.custom_tech_dir)
    self.DH_WRITE                         = tech_parser("DH_WRITE", self.custom_tech_dir)
    self.DW_WRITE                         = tech_parser("DW_WRITE", self.custom_tech_dir)
    self.DH_RW                            = tech_parser("DH_RW", self.custom_tech_dir)
    self.DW_RW                            = tech_parser("DW_RW", self.custom_tech_dir)
    # TODO: should have custom area if specified, force cacti values for now.
    """ If want to use custom area with cacti -- should have given finPitch,
    contacted_poly_pitch, known tracks for bitcell, and contacted poly width"""
    if self.process.hybrid is False:
      self.height_um, self.width_um = get_macro_dimensions(self)
    # print("Custom tech parameters applied successfully.\n")

  def _cacti_init(self, output_dir, cacti_dir, custom_tech_dir):
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
    if not self.use_custom_tech or (self.use_custom_tech and hasattr(self.process, 'hybrid') and self.process.hybrid == True):
      print('Running Cacti with overidden values...\n') if self.process.hybrid == True else print('Running Cacti...\n')
      
      # __run_cacti: shell out to cacti to generate a csv file with more data
      # regarding this memory based on the input parameters from the json
      # configuration file.
      self._run_cacti()
      
      # Parse CACTI results
      with open( os.sep.join([self.results_dir, 'cacti.cfg.out']), 'r' ) as fid:
        lines = [line for line in fid]
        cacti_data = lines[-1].split(',')

      # Initialize with CACTI data
      self.process.tech_nm             = int(cacti_data[0])
      self.capacity_bytes              = int(cacti_data[1])
      self.associativity               = int(cacti_data[2])
      self.output_width_bits           = int(cacti_data[3])
      self.access_time_ns              = float(cacti_data[4])
      self.cycle_time_ns               = float(cacti_data[5])
      #self.dyn_search_energy_nj        = float(cacti_data[6]) Unused
      #self.dyn_read_energy_nj          = float(cacti_data[7]) Unused
      self.dyn_write_energy_nj         = float(cacti_data[8]) # Also used in pin_dynamic_power_mW
      self.standby_leakage_per_bank_mW = float(cacti_data[9])
      self.area_mm2                    = float(cacti_data[10])
      self.fo4_ps                      = float(cacti_data[11])
      self.width_um                    = float(cacti_data[12])
      self.height_um                   = float(cacti_data[13])

    # Override with custom tech parameters if available
    if self.use_custom_tech:
      self._get_custom_tech()
      
      self.access_time_ns              = self.temp_access_time_ns if self.temp_access_time_ns is not None else self.access_time_ns
      self.cycle_time_ns               = self.temp_cycle_time_ns if self.temp_cycle_time_ns is not None else self.cycle_time_ns
      self.fo4_ps                      = self.temp_fo4_ps if self.temp_fo4_ps is not None else self.fo4_ps
      self.standby_leakage_per_bank_mW = self.temp_standby_leakage_per_bank_mW if self.temp_standby_leakage_per_bank_mW is not None else self.standby_leakage_per_bank_mW
      self.pin_dynamic_power_mW        = self.temp_pin_dynamic_power_mW if self.temp_pin_dynamic_power_mW is not None else self.dyn_write_energy_nj
      # self.dyn_write_energy_nj         = self.temp_dyn_write_energy_nj if self.temp_dyn_write_energy_nj is not None else self.dyn_write_energy_nj
  
    else:
      print("Using CACTI parameters only")

      """ Cacti defaults """
      self.t_setup_ns           = 0.050 ; # arbitrary 50ps setup
      self.t_hold_ns            = 0.050 ; # arbitrary 50ps hold
      self.pin_dynamic_power_mW = self.dyn_write_energy_nj  # Use CACTI energy as power estimate
      self.cap_input_pf         = 0.005
    
    self.tech_node_um = self.process.tech_nm / 1000.0

    # Adjust to snap
    self.width_um = (math.ceil((self.width_um*1000.0)/self.process.snapWidth_nm)*self.process.snapWidth_nm)/1000.0
    self.height_um = (math.ceil((self.height_um*1000.0)/self.process.snapHeight_nm)*self.process.snapHeight_nm)/1000.0
    self.area_um2 = self.width_um * self.height_um 

  # __run_cacti: shell out to cacti to generate a csv file with more data
  # regarding this memory based on the input parameters from the json
  # configuration file.
  def _run_cacti( self ):
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