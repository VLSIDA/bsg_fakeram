import math
import re
import os
import sys
from pathlib import Path
from utils.cacti_config import cacti_config
from utils.area import get_macro_dimensions, TECH_BITCELL_UM
################################################################################
# MEMORY CLASS
#
# This class stores the infromation about a specific memory that is being
# generated. This class takes in a process object, the infromation in one of
# the items in the "sram" list section of the json configuration file, and
# finally runs cacti to generate the rest of the data.
################################################################################

class Memory:

  def __init__( self, process, sram_data , output_dir = None, cacti_dir = None):

    self.process        = process
    self.name           = str(sram_data['name'])
    self.width_in_bits  = int(sram_data['width'])
    self.depth          = int(sram_data['depth'])
    self.num_banks      = int(sram_data['banks'])
    self.cache_type     = str(sram_data['type']) if 'type' in sram_data else 'cache'
    self.has_wmask      = False if str(sram_data.get('no_wmask', "")) == "true" else True
    self.banking_technique = str(sram_data.get('banking_technique', 'width'))
    
    # Naive attempt for setting up multiple banks. 
    # Splices either width or depth based on 'banking_technique'
    if self.num_banks > 1 and self.num_banks % 2 == 0:
      if self.banking_technique == 'depth':
        self.depth = math.ceil(self.depth / self.num_banks)
        sram_data['depth'] = self.depth 
      elif self.banking_technique == 'width':
        self.width_in_bits = math.ceil(self.width_in_bits / self.num_banks)
        sram_data['width'] = self.width_in_bits
      else:
        raise Exception("Unsupported banking type '{}', use either 'width' or 'depth' ('width' is DEFAULT)".format(sram_data['banking_technique']))
    self.r_ports                            = int(sram_data['ports'].get('r', 0))
    self.w_ports                            = int(sram_data['ports'].get('w', 0))
    self.rw_ports                           = int(sram_data['ports'].get('rw', 0))
    
    # Write granularity (default to byte-level if not specified).
    # 8 = one mask bit per data byte (typical SRAM byte-write enable).
    # 1 = one mask bit per data bit (per-bit write mask).
    self.write_granularity = int(sram_data.get('write_granularity', 8))
    
    # Write mode (default to write-first if not specified)
    # Options: 'write_first' (write-through), 'read_first' (no-change), 'write_through' (combinational)
    self.write_mode    = str(sram_data.get('write_mode', 'write_first'))


    self.width_in_bytes = math.ceil(self.width_in_bits / 8.0)
    self.total_size     = self.width_in_bytes * self.depth
    if output_dir: # Output dir was set by command line option
      p = str(Path(output_dir).expanduser().resolve(strict=False))
      self.results_dir = os.sep.join([p, self.name])
    else:
      self.results_dir = os.sep.join([os.getcwd(), 'results', self.name])
    if not os.path.exists( self.results_dir ):
      os.makedirs( self.results_dir )
    
    print(f'\n\n\n***************************Run for {self.name}***************************\n\n\n')

    # Per-tech analytical timing/power constants. asap7 numbers were
    # carried over from FakeRAM2.0; sky130hd numbers are order-of-magnitude
    # estimates from the OpenRAM 130nm 6T sram characterizations
    # (sram_1rw1_8_64_sky130: ~1.4 ns access, ~1 ns cycle, ~0.05 mW
    # standby per bank, ~200 ps FO4, ~0.015 mW per pin). Adjust if real
    # silicon measurements become available.
    TECH_ANALYTIC = {
      # gt2n (2nm GAAFET): faster than asap7 (FO4 ~5 ps vs 9 ps), but
      # access_time_ns and cycle_time_ns are anchored to asap7's own
      # measured values (0.2183ns / 0.1566ns) rather than scaled by the
      # FO4 ratio -- bitline/sense-amp timing is bitcell/array-dominated,
      # not logic-gate-switching-dominated, so it doesn't scale with FO4
      # the way a logic path does (the "SRAM scaling wall": memory timing
      # scales much slower across nodes than logic speed). gt2n and asap7
      # are both leading-edge finFET/GAAFET nodes with comparable bitcell
      # physics, so gt2n's access/cycle time should be close to asap7's,
      # not a further FO4-scaled-down multiple of it; cycle_time_ns holds
      # the same ~0.72 cycle/access ratio asap7 and sky130hd both show.
      2: dict(
        access_time_ns=0.200,  # asap7's 0.2183 * ~90%
        cycle_time_ns=0.1435,  # access_time_ns * asap7/sky130hd's ~0.72 cycle/access ratio
        standby_leakage_per_bank_mW=0.10, fo4_ps=5.0,
        pin_dynamic_power_mW=0.001,
        cap_input_pf=0.000488,  # gt2_6t_buf_x1_w31_lvt input cap (real GT2N PDK min-driver cell)
        t_setup_ns=0.007, t_hold_ns=0.007,  # gt2_6t_dffasync_x1_w31_lvt D-vs-CLK, nominal-slew corner
      ),
      7: dict(
        access_time_ns=0.2183, cycle_time_ns=0.1566,
        standby_leakage_per_bank_mW=0.1289, fo4_ps=9.0632,
        pin_dynamic_power_mW=0.0013449,
      ),
      130: dict(
        access_time_ns=1.4, cycle_time_ns=1.0,
        standby_leakage_per_bank_mW=0.05, fo4_ps=200.0,
        pin_dynamic_power_mW=0.015,
      ),
    }
    if process.tech_nm in TECH_ANALYTIC:
      assert process.tech_nm in TECH_BITCELL_UM, (
        f"tech_nm={process.tech_nm} has an analytical timing entry in "
        f"TECH_ANALYTIC but no bitcell entry in TECH_BITCELL_UM (area.py) -- "
        f"add one, or get_macro_dimensions() will silently fall back to "
        f"requiring fin_pitch_nm/contacted_poly_pitch_nm instead."
      )
      self.tech_node_nm  = process.tech_nm
      self.associativity = 1
      for k, v in TECH_ANALYTIC[process.tech_nm].items():
        setattr(self, k, v)
      self.height_um, self.width_um = get_macro_dimensions(process, sram_data)

      overall_mult = 1
      wmask_mult = 0 if self.has_wmask == False else 0.045
      # Height and Width Multiplier based on the amount of r, w, and rw ports,
      # ASSUMING there is more than 1 port
      if int(sram_data['ports']['r']) + int(sram_data['ports']['rw']) + int(sram_data['ports']['w']) > 1:
        r_port_mult = int(sram_data['ports']['r']) * 0.3
        # Add wmask_mult to per-port multipliers for w and rw
        w_port_mult = int(sram_data['ports']['w']) * (0.25 + wmask_mult)
        rw_port_mult = int(sram_data['ports']['rw']) * (0.4 + wmask_mult)
        overall_mult = (1 + r_port_mult + w_port_mult + rw_port_mult)
      self.height_um = self.height_um * (overall_mult + wmask_mult)
      self.width_um = self.width_um * (overall_mult + wmask_mult)
    else:
      if output_dir: # Output dir was set by command line option
        p = str(Path(output_dir).expanduser().resolve(strict=False))
        self.results_dir = os.sep.join([p, self.name])
      else:
        self.results_dir = os.sep.join([os.getcwd(), 'results', self.name])
      if not os.path.exists( self.results_dir ):
        os.makedirs( self.results_dir )
      if cacti_dir:
        self.cacti_dir = cacti_dir
      else:
        self.cacti_dir = os.environ['CACTI_BUILD_DIR']

      # IF size is unavailable for tag org (cacti error), try to generate 
      # as close to the same config that is configurable 
      original_width_in_bits = self.width_in_bits
      original_width_in_bytes = self.width_in_bytes
      while True:
        try:
          self.__run_cacti()
          with open( os.sep.join([self.results_dir, 'cacti.cfg.out']), 'r' ) as fid:
            lines = [line for line in fid]
            cacti_data = lines[-1].split(',')
          self.tech_node_nm                = int(cacti_data[0])
          self.associativity               = int(cacti_data[2])
          self.access_time_ns              = float(cacti_data[4])
          self.cycle_time_ns               = float(cacti_data[5])
          self.pin_dynamic_power_mW        = float(cacti_data[8])
          self.standby_leakage_per_bank_mW = float(cacti_data[9])
          self.fo4_ps                      = float(cacti_data[11])
          self.width_um                    = float(cacti_data[12])
          self.height_um                   = float(cacti_data[13])
        except FileNotFoundError:
          # IF no size within reason is available, terminate as usual
          print(f"Byte width of {self.width_in_bytes} doesn't work with cacti. Attempting again with different values.")
          self.width_in_bits = self.width_in_bits + 8
          self.width_in_bytes = math.ceil(self.width_in_bits / 8.0)
          self.total_size     = self.width_in_bytes * self.depth
          # Raise the same error, as the config doesn't work even within reason
          if self.width_in_bits >= original_width_in_bits + (8 * 2):
            raise
        else:
          break
      # Revert the width values back for correct pin count (also try to size width of physical macro according to OG size)
      if self.width_in_bits != original_width_in_bits:
        self.width_um = self.width_um * original_width_in_bits / self.width_in_bits
        print("\n\n\n*********************INFO******************************\n\n\n")
        print(f"Re-calculating width using ratio of original width in bits ({original_width_in_bits}) to the width in bits fed to cacti ({self.width_in_bits})")
        self.width_in_bits = original_width_in_bits
        self.width_in_bytes = original_width_in_bytes

      
    
    # nangate45 (CACTI path, below) has no override yet -- set it there under
    # a tech_nm==45 check before this line, not by adding a key to
    # TECH_ANALYTIC, which would also divert it off the CACTI path entirely.
    if not hasattr(self, 'cap_input_pf'):  # blanket default; gt2n sets its own above
      self.cap_input_pf = 0.005

    self.tech_node_um = self.tech_node_nm / 1000.0

    print(f'Original {self.name} size = {self.width_um} x {self.height_um}')
    
    # Adjust to snap
    self.width_um = (math.ceil((self.width_um*1000.0)/self.process.snapWidth_nm)*self.process.snapWidth_nm)/1000.0
    self.height_um = (math.ceil((self.height_um*1000.0)/self.process.snapHeight_nm)*self.process.snapHeight_nm)/1000.0
    self.area_um2 = self.width_um * self.height_um

    #self.pin_dynamic_power_mW = (0.5 * self.cap_input_pf * (float(self.process.voltage)**2))*1e9 ;# P = 0.5*CV^2
  
    if not hasattr(self, 't_setup_ns'):  # blanket default; gt2n sets its own above
      self.t_setup_ns = 0.050  ;# arbitrary 50ps setup
    if not hasattr(self, 't_hold_ns'):  # blanket default; gt2n sets its own above
      self.t_hold_ns  = 0.050  ;# arbitrary 50ps hold

  # __run_cacti: shell out to cacti to generate a csv file with more data
  # regarding this memory based on the input parameters from the json
  # configuration file.
  def __run_cacti( self ):
    # For different port configurations, configure CACTI appropriately
    rw_ports = self.rw_ports
    r_ports = self.r_ports if hasattr(self, 'r_ports') else 0
    w_ports = self.w_ports if hasattr(self, 'w_ports') else 0
    
    fid = open(os.sep.join([self.results_dir,'cacti.cfg']), 'w')
    fid.write( cacti_config.format( self.total_size
             , self.width_in_bytes, rw_ports, r_ports, w_ports
             , self.process.tech_um, self.width_in_bytes*8, self.num_banks
             , self.cache_type ))
    fid.close()
    odir = os.getcwd()
    os.chdir(self.cacti_dir )
    cmd = os.sep.join(['.','cacti -infile ']) + os.sep.join([self.results_dir,'cacti.cfg'])
    os.system( cmd)
    os.chdir(odir)

