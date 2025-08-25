
from dataclasses import dataclass
from utils.init_mem.mem_globals import *

tech_nm_idx                  = 0
capacity_bytes_idx           = 1
associativity_idx            = 2
output_width_bits_idx        = 3
access_time_idx              = 4
cycle_time_ns_idx            = 5
dyn_search_energy_idx        = 6
dyn_read_energy_idx          = 7
dyn_write_energy_idx         = 8
standby_leakage_per_bank_idx = 9
area_idx                     = 10
fo4_idx                      = 11
width_idx                    = 12
height_idx                   = 13

@dataclass
class HybridData():
    access_time_ns              : float = None
    cycle_time_ns               : float = None
    pin_dynamic_power_mW        : float = None
    standby_leakage_per_bank_mW : float = None
    fo4_ps                      : float = None

class CactiData():
    def __init__(self, mem, cacti_data):
    
        # Initialize with CACTI data
        self.tech_nm                     = int(cacti_data[tech_nm_idx])
        self.capacity_bytes              = int(cacti_data[capacity_bytes_idx])        # Unused
        self.associativity               = int(cacti_data[associativity_idx])         # Unused
        self.output_width_bits           = int(cacti_data[output_width_bits_idx])     # Unused
        self.access_time_ns              = float(cacti_data[access_time_idx])
        self.cycle_time_ns               = float(cacti_data[cycle_time_ns_idx])
        # self.dyn_search_energy_nj        = float(cacti_data[dyn_search_energy_idx]) # Unused
        self.dyn_read_energy_nj          = float(cacti_data[dyn_read_energy_idx])     # Unused
        self.dyn_write_energy_nj         = float(cacti_data[dyn_write_energy_idx])
        self.standby_leakage_per_bank_mW = float(cacti_data[standby_leakage_per_bank_idx])
        self.area_mm2                    = float(cacti_data[area_idx])
        self.fo4_ps                      = float(cacti_data[fo4_idx])
        self.width_um                    = float(cacti_data[width_idx])
        self.height_um                   = float(cacti_data[height_idx])

        self.pin_dynamic_power_mW        = self.dyn_write_energy_nj
        
