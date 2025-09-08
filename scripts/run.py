#!/usr/bin/env python3

import sys
import json
import argparse

from utils.class_process import Process
from utils.mem_init.modules import *

from utils.generate_lib import generate_lib
from utils.gen_lef.lef_core import generate_lef
from utils.generate_verilog import generate_verilog
from utils.generate_verilog import generate_verilog_bb

from utils.mem_init.mem_init import memory_initializer
from utils.mem_init.mem_globals import print_init_sram

################################################################################
# RUN GENERATOR
#
# This is the main part of the script. It will read in the JSON configuration
# file, create a Cacti configuration file, run Cacti, extract the data from
# Cacti, and then generate the timing, physical and logical views for each SRAM
# found in the JSON configuration file.
################################################################################

def _print_all_srams(memory_config_list: list[object]) -> None:
    banner_line = "=" * 100
    print("\n" + banner_line)
    print(" " * 40 + "SRAM CONFIG SUMMARY")
    print(banner_line)

    fields = [
        "width_in_bits", "depth", "addr_width", "width_in_bytes",
        "total_size", "tech_node_um", "t_hold_ns", "t_setup_ns",
        "cap_input_pf", "num_banks", "pinPitchFactor", "cache_type",
        "write_mode", "column_mux_factor", "r", "w", "rw",
        "has_write_mask", "write_granularity", "area_mm2", "height_um",
        "width_um", "wmask", "access_time_ns", "cycle_time_ns",
        "standby_leakage_per_bank_mW", "fo4_ps", "capacity_bytes",
        "associativity", "output_width_bits", "dyn_read_energy_nj",
        "dyn_write_energy_nj", "pin_dynamic_power_mW",
        "finPitch_nm", "contacted_poly_pitch_nm", "h0_tracks",
        "w0_polys", "dh_read", "dw_read", "dh_write", "dw_write",
        "dh_rw", "dw_rw"
    ]

    mid = len(fields) // 2
    left_fields, right_fields = fields[:mid], fields[mid:]

    for idx, mem in enumerate(memory_config_list, 1):
        print(f"\n[SRAM {idx}] {mem.name}")
        print("-" * 100)

        for lf, rf in zip(left_fields, right_fields):
            left_val = getattr(mem, lf, None)
            right_val = getattr(mem, rf, None)

            # Ensure safe string conversion
            left_val = "N/A" if left_val is None else str(left_val)
            right_val = "N/A" if right_val is None else str(right_val)

            print(f"{lf:30}: {left_val:<20}    {rf:30}: {right_val}")

    print("\n" + banner_line)
    print(" " * 40 + "END OF RUN")
    print(banner_line + "\n")


def get_args() -> argparse.Namespace:
    """
    Get command line arguments
    """
    parser = argparse.ArgumentParser(
        description="""
    BSG Black-box SRAM Generator --
    This project is designed to generate black-boxed SRAMs for use in CAD
    flows where either an SRAM generator is not avaible or doesn't
    exist.  """
    )

    parser.add_argument("config", help="JSON configuration file")

    parser.add_argument(
        "--output_dir", action="store", help="Output directory ", required=False, default=None
    )

    parser.add_argument(
        "--cacti_dir", action="store", help="CACTI installation directory ", required=False, default=None
    )

    return parser.parse_args()

memory_config_list = []

def main ( args : argparse.Namespace):

  # Load the JSON configuration file
  with open(args.config, 'r') as fid:
    raw = [line.strip() for line in fid if not line.strip().startswith('#')]
  json_data = json.loads('\n'.join(raw))

  # Create a process object (shared by all srams)
  process = Process(json_data)

  custom = json_data.get('custom_tech', None)

  # Go through each sram and generate the lib, lef and v files
  for sram_data in json_data['srams']:

    mem_init = Memory(process, sram_data)
    
    memory = memory_initializer(mem_init, custom, args.output_dir, args.cacti_dir)
    
    print_init_sram(memory)

    generate_lib(memory)
    
    generate_lef(memory)
    
    generate_verilog(memory)
    
    generate_verilog_bb(memory)

    memory_config_list.append(memory)


### Entry point
if __name__ == '__main__':
  args = get_args()
  main( args )
  _print_all_srams(memory_config_list)

