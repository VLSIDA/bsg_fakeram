import math
import re
import os
import sys
from decimal import Decimal
from pathlib import Path
from utils.class_custom import Custom
from utils.cacti_config import cacti_config
from utils.area import get_macro_dimensions
################################################################################
# MEMORY CLASS
#
# This class stores the information about a specific memory that is being
# generated. This class takes in a process object, the information in one of
# the items in the "sram" list section of the json configuration file, and
# finally runs cacti to generate the rest of the data.
################################################################################

class Memory():
  def __init__( self, process, sram_data , custom_data, output_dir = None, cacti_dir = None):
    # Main Memory Parameters
    self.process                     = process
    self.sram_data                   = sram_data
    self.custom_data                 = custom_data
    self.name                        = str(sram_data['name'] ) if 'name'  in sram_data else None
    self.width_in_bits               = int(sram_data['width']) if 'width' in sram_data else None
    self.depth                       = int(sram_data['depth']) if 'depth' in sram_data else None
    self.width_in_bytes              = math.ceil((self.width_in_bits / 8.0))
    self.total_size                  = self.width_in_bytes * self.depth
    self.t_setup_ns                  = self.process.t_setup_ns
    self.t_hold_ns                   = self.process.t_hold_ns
    self.cap_input_pf                = self.process.cap_input_pf

    # Optional Memory Parameters
    self.num_banks                   = int(sram_data['banks']) if 'banks' in sram_data else 1
    self.pitchFactor                 = int(sram_data['pitchFactor']) if 'pitchFactor' in sram_data else 1
    self.cache_type                  = str(sram_data['type']) if 'type' in sram_data else 'cache'
    self.write_mode                  = str(sram_data['write_mode']) if 'write_mode' in sram_data else 'write_first'

    # Parameter overrides
    self.column_mux_factor_overriden = True if 'column_mux_factor_override' in sram_data else False
    self.column_mux_factor           = float(sram_data.get('column_mux_factor_override', self.process.column_mux_factor))
    print(f'column_mux_factor: {self.column_mux_factor}')

    self.r                           = int(sram_data['r']) if 'r' in sram_data else 0
    self.w                           = int(sram_data['w']) if 'w' in sram_data else 0
    self.rw                          = int(sram_data['rw']) if 'rw' in sram_data else 0

    # Init write mask 
    self.has_write_mask              = None
    self.dyn_write_energy_nj         = None
    self.write_granularity           = None
    self.wmask                       = None

    self._get_write_granularity()
    self._mem_init(sram_data, output_dir, cacti_dir)
    self._print_init(total_ports = self.r + self.w + self.rw)

  def _get_write_granularity(self):
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
    print(f'\n '
          f'\n##################################################\n')
    print(f'Creating SRAM: {self.name} of width: {self.width_in_bits} and depth: {self.depth}')
    print('\n##################################################\n')
    print("Applying custom tech overrides...\n") if self.custom_data.hybrid is False else print("Applying hybrid overrides...")
    print('Hybrid checking             :', self.custom_data.hybrid)
    print(f'Total Ports                 : {total_ports} \n'
          f'Num Port R                  : {self.r} \n'
          f'Num Port W                  : {self.w} \n'
          f'Num Port RW                 : {self.rw} \n'
            )
  
    if self.has_write_mask:
        print(f'Has write mask    : True\n'
              f'Num Port Wmask    : {self.wmask}\n'
              f'Write granularity : {self.write_granularity}\n')
        
    print(f'column_mux_factor override  : {self.column_mux_factor_overriden}')
    if self.column_mux_factor_overriden:
      print(f'Column mux overriden        : {self.column_mux_factor}')
    else:
       print(f'Column mux factor      : {self.column_mux_factor}')
    
    print(f'Num Banks                   : {self.num_banks}\n'
         f'Flip                        : {self.process.flipPins}\n'
         f'verticalPinsOnly            : {self.process.verticalPinsOnly  }\n'
         f'pinPitch_nm                 : {self.process.pinPitch_nm}\n'
         f'x_pinPitch_nm               : {self.process.x_pinPitch_nm}\n'
         f'pitchFactor                 : {self.pitchFactor}\n'
         f'heightSnaptoTrack           : {self.process.heightSnaptoTrack}\n'
         f'y_offset_um                 : {self.process.y_offset_um}\n'
         f'x_offset_um                 : {self.process.x_offset_um}\n')
    
    print(f'\n'
          f'access_time_ns              : {self.custom_data.access_time_ns or self.access_time_ns}\n'
          f'cycle_time_ns               : {self.custom_data.cycle_time_ns or self.cycle_time_ns}\n'
          f'fo4_ps                      : {self.custom_data.fo4_ps or self.fo4_ps}\n'
          f'dyn_write_energy_nj         : {self.dyn_write_energy_nj or None}\n'
          f'standby_leakage_per_bank_mW : {self.custom_data.standby_leakage_per_bank_mW or self.standby_leakage_per_bank_mW}\n'
          f'pin_dynamic_power_mW        : {self.custom_data.pin_dynamic_power_mW or self.pin_dynamic_power_mW}\n'
          f't_setup_ns                  : {self.t_setup_ns}\n'
          f't_hold_ns                   : {self.t_hold_ns}\n'
          f'cap_input_pf                : {self.cap_input_pf}\n'
          f'contacted_poly_pitch_nm     : {self.custom_data.contacted_poly_pitch_nm}\n'
          f'finPitch_nm                 : {self.custom_data.finPitch_nm}\n'
          f'h0_tracks                   : {self.custom_data.h0_tracks}\n'
          f'w0_polys                    : {self.custom_data.w0_polys}\n'
          f'dh_read                     : {self.custom_data.dh_read}\n'
          f'dw_read                     : {self.custom_data.dw_read}\n'
          f'dh_write                    : {self.custom_data.dh_write}\n'
          f'dw_write                    : {self.custom_data.dw_write}\n'
          f'dh_rw                       : {self.custom_data.dh_rw}\n'
          f'dw_rw                       : {self.custom_data.dw_rw}\n\n'
          f'Total height                : {self.height_um}\n'
          f'Total width                 : {self.width_um}\n')
    print('\n ')

  def _mem_init(self, sram_data, output_dir, cacti_dir) -> None:
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

    """Run cacti only if using a custom technology
    and using a valid cacti process node for
    overriding specific parameters."""
    if use_cacti(self):      
      """_run_cacti: shell out to cacti to generate a csv file with more data
       regarding this memory based on the input parameters from the json
       configuration file."""
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
      self.access_time_ns              = get_custom(self, self.custom_data.access_time_ns, cacti_data[4])
      self.cycle_time_ns               = get_custom(self, self.custom_data.cycle_time_ns, cacti_data[5])
      #self.dyn_search_energy_nj        = float(cacti_data[6]) Unused
      #self.dyn_read_energy_nj          = float(cacti_data[7]) Unused
      self.dyn_write_energy_nj         = float(cacti_data[8])  # Also used in pin_dynamic_power_mW
      self.pin_dynamic_power_mW        = get_custom(self, self.custom_data.pin_dynamic_power_mW, self.dyn_write_energy_nj)
      self.standby_leakage_per_bank_mW = get_custom(self, self.custom_data.standby_leakage_per_bank_mW, cacti_data[9])
      self.area_mm2                    = float(cacti_data[10])
      self.fo4_ps                      = get_custom(self, self.custom_data.fo4_ps, cacti_data[11])
      self.width_um                    = float(cacti_data[12])
      self.height_um                   = float(cacti_data[13])

      # Same column mux/bank calculation logic from FakeRAM2.0
      self.height_um = self.height_um / self.column_mux_factor
      self.width_um = self.width_um * self.column_mux_factor

      self.height_um = self.height_um / self.num_banks
      self.width_um = self.width_um * self.num_banks
  
    """ If want to run custom tech
    these are the required params for it
    to run """
    if self.process.use_custom_tech == True:
      # Initialize with custom data
      self.access_time_ns              = self.custom_data.access_time_ns
      self.cycle_time_ns               = self.custom_data.cycle_time_ns
      self.fo4_ps                      = self.custom_data.fo4_ps
      self.standby_leakage_per_bank_mW = self.custom_data.standby_leakage_per_bank_mW
      self.pin_dynamic_power_mW        = self.custom_data.pin_dynamic_power_mW
      self.finPitch_nm                 = self.custom_data.finPitch_nm
      self.contacted_poly_pitch_nm     = self.custom_data.contacted_poly_pitch_nm
      self.w0_polys                    = self.custom_data.w0_polys
      self.h0_tracks                   = self.custom_data.h0_tracks

      # self.column_mux_factor           = float(sram_data.get('column_mux_factor_override', self.column_mux_factor))
      self.dh_read                     = float(sram_data.get('dh_read_override', self.custom_data.dh_read))
      self.dw_read                     = float(sram_data.get('dw_read_override', self.custom_data.dw_read))
      self.dh_write                    = float(sram_data.get('dh_write_override', self.custom_data.dh_write))
      self.dw_write                    = float(sram_data.get('dw_write_override', self.custom_data.dw_write))
      self.dh_rw                       = float(sram_data.get('dh_rw_override', self.custom_data.dh_rw))
      self.dw_rw                       = float(sram_data.get('dw_rw_override', self.custom_data.dw_rw))

      self.height_um, self.width_um = get_macro_dimensions(self, self.process)
    else:
      print("Using CACTI parameters only")

      # Cacti defaults
      self.t_setup_ns                  = self.process.t_setup_ns
      self.t_hold_ns                   = self.process.t_hold_ns
      self.cap_input_pf                = self.process.cap_input_pf
      print(self.t_setup_ns)
      # self.pin_dynamic_power_mW = self.dyn_write_energy_nj # Use CACTI energy as power estimate
    
    self.tech_node_um = self.process.tech_nm / 1000.0

    # TODO:
    # Adjust to snap
    self.width_um = (math.ceil((self.width_um*1000.0)/self.process.snapWidth_nm)*self.process.snapWidth_nm)/1000.0
    self.height_um = (math.ceil((self.height_um*1000.0)/self.process.snapHeight_nm)*self.process.snapHeight_nm)/1000.0
    self.height_um, self.width_um = round_up_to_multiple(self.height_um, self.process.manufacturing_grid_nm), round_up_to_multiple(self.width_um, self.process.manufacturing_grid_nm)

    # ensure matches tracks
    pin_pitch_y_nm = int(round(self.process.pinPitch_um * 1000.0))
    pin_pitch_x_nm = int(round(self.process.x_pinPitch_um * 1000.0))
    snap_w_nm      = int(round(self.process.snapWidth_nm))
    snap_h_nm      = int(round(self.process.snapHeight_nm))
    manuf_grid_nm  = int(round(self.process.manufacturing_grid_nm))

    # Convert initial dimensions to nanometers
    width_nm  = int(round(self.width_um * 1000.0))
    height_nm = int(round(self.height_um * 1000.0))

    # Apply all constraints in order, rounding up each time
    width_nm  = math.ceil(width_nm / snap_w_nm) * snap_w_nm
    height_nm = math.ceil(height_nm / snap_h_nm) * snap_h_nm

    width_nm  = math.ceil(width_nm / manuf_grid_nm) * manuf_grid_nm
    height_nm = math.ceil(height_nm / manuf_grid_nm) * manuf_grid_nm

    width_nm  = math.ceil(width_nm / pin_pitch_x_nm) * pin_pitch_x_nm
    height_nm = math.ceil(height_nm / pin_pitch_y_nm) * pin_pitch_y_nm

    # Convert back to microns
    self.width_um = width_nm / 1000.0
    self.height_um = height_nm / 1000.0
    self.width_um += (self.width_um % self.process.x_pinPitch_um)
    self.width_um = math.ceil(self.width_um / self.process.x_pinPitch_um) * self.process.x_pinPitch_um
    assert (width_nm % pin_pitch_x_nm) == 0, f"Width {width_nm}nm not multiple of X pin pitch {pin_pitch_x_nm}nm"
    assert (height_nm % pin_pitch_y_nm) == 0, f"Height {height_nm}nm not multiple of Y pin pitch {pin_pitch_y_nm}nm"

    self.area_um2 = self.width_um * self.height_um

  # __run_cacti: shell out to cacti to generate a csv file with more data
  # regarding this memory based on the input parameters from the json
  # configuration file.
  def _run_cacti( self ) -> None:
    fid = open(os.sep.join([self.results_dir,'cacti.cfg']), 'w')
    fid.write(
        cacti_config.format(
            self.total_size,
            self.width_in_bytes,
            self.rw,
            self.r,
            self.w,
            self.process.tech_um,
            self.width_in_bytes * 8,
            self.num_banks,
            self.cache_type
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

def round_up_to_multiple(n, multiple) -> float:
    return math.ceil(n / multiple) * multiple

def get_custom(self, custom_param, cacti_data) -> float:
  """ use cacti value of parameter if hybrid is not used, if hybrid
  is true then either use cacti data or custom parameter if given """
  return cacti_data if self.custom_data.hybrid == False else (custom_param or cacti_data)

def use_cacti(self) -> bool:
  """ Only returns true if hybrid option is used """
  if self.process.use_custom_tech == False or (self.process.use_custom_tech == True and self.custom_data.hybrid == True):
     print('Running Cacti with overidden values...\n') if self.custom_data.hybrid == True else print('Running Cacti...\n')
     return True
  print("Not using cacti...")
  return False