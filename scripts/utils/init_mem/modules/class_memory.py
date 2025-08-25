import math
from dataclasses import dataclass

################################################################################
# MEMORY CLASS
#
# This class stores the information about a specific memory that is being
# generated. This class takes in a process object, the information in one of
# the items in the "sram" list section of the json configuration file, and
# finally runs cacti to generate the rest of the data.
################################################################################

class Memory():
	def __init__( self, process, sram_data ):

		# Main Memory Parameters
		self.process                     = process
		self.sram_data                   = sram_data
		self.name                        = str(sram_data.get('name' , None))
		self.width_in_bits               = int(sram_data.get('width', None))
		self.depth                       = int(sram_data.get('depth', None))
		self.addr_width                  = math.ceil(math.log2(self.depth))
		self.width_in_bytes              = math.ceil((self.width_in_bits / 8.0))
		self.total_size                  = self.width_in_bytes * self.depth

		self.tech_node_um                = self.process.tech_um
		self.t_hold_ns                   = self.process.t_hold_ns
		self.t_setup_ns                  = self.process.t_setup_ns
		self.cap_input_pf                = self.process.cap_input_pf

		# Optional Memory Parameters
		self.num_banks                   = int(sram_data.get('banks', 1))
		self.pitchFactor                 = int(sram_data.get('pitchFactor', 1))
		self.cache_type                  = str(sram_data.get('type','cache'))
		self.write_mode                  = str(sram_data.get('write_mode','write_first'))

		# Parameter overrides
		self.column_mux_factor_overriden = True if 'column_mux_factor_override' in sram_data else False
		self.column_mux_factor           = float(sram_data.get('column_mux_factor_override', self.process.column_mux_factor))
		self.r                           = int(sram_data['ports'].get('r', 0))
		self.w                           = int(sram_data['ports'].get('w', 0))
		self.rw                          = int(sram_data['ports'].get('rw', 0))

		self.results_dir                 = None
		self.cacti_dir				     = None

		self.area_mm2                    = None
		self.height_um                   = None
		self.width_um                    = None
	
		# Write Masks
		self.has_write_mask              = None
		self.write_granularity           = None
		self.wmask                       = None

		# Custom Data Only Required / Optional Hybrid Data Override
		self.access_time_ns              = None
		self.cycle_time_ns               = None
		self.standby_leakage_per_bank_mW = None
		self.fo4_ps                      = None
		self.capacity_bytes              = None
		self.associativity               = None
		self.output_width_bits           = None
		self.dyn_search_energy_nj        = None
		self.dyn_read_energy_nj          = None
		self.dyn_write_energy_nj         = None
		self.pin_dynamic_power_mW        = None

		# Custom Data Only Required
		self.custom_data                 = None
		self.finPitch_nm                 = None
		self.contacted_poly_pitch_nm     = None
		self.h0_tracks                   = None
		self.w0_polys                    = None
		self.dh_read                     = None
		self.dw_read                     = None
		self.dh_write                    = None
		self.dw_write                    = None
		self.dh_rw                       = None
		self.dw_rw                       = None

		self.__post_init__()

	def __post_init__(self):
		TimingData(
			access_time_ns              = self.access_time_ns,
			cycle_time_ns               = self.cycle_time_ns,
			standby_leakage_per_bank_mW = self.standby_leakage_per_bank_mW,
			fo4_ps                      = self.fo4_ps,
			capacity_bytes              = self.capacity_bytes,
			associativity               = self.associativity,
			output_width_bits           = self.output_width_bits,
			dyn_search_energy_nj        = self.dyn_search_energy_nj,
			dyn_read_energy_nj          = self.dyn_read_energy_nj,
			dyn_write_energy_nj         = self.dyn_write_energy_nj,
			pin_dynamic_power_mW        = self.pin_dynamic_power_mW
		)

@dataclass
class TimingData():  
      access_time_ns              :  float
      cycle_time_ns               :  float
      standby_leakage_per_bank_mW :  float
      fo4_ps                      :  float
      capacity_bytes              :  float
      associativity               :  float
      output_width_bits           :  float
      dyn_search_energy_nj        :  float
      dyn_read_energy_nj          :  float
      dyn_write_energy_nj         :  float
      pin_dynamic_power_mW        :  float
