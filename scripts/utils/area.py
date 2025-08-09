import os
import sys
import math 

"""
TODO: Make area.py flexible across different designs
"""
def get_macro_dimensions(mem) -> int:
  Y_ASYMMETRIC_SRAM_SCALING = 1/2 # Adjusts to number of pins anyways

  # DYNAMIC SIZING
  if mem.is_asymmetric:
    xfactor = ((mem.r + mem.w) + mem.rw)
    yfactor = ((mem.r + mem.w) * 1 + mem.rw) * Y_ASYMMETRIC_SRAM_SCALING
  else:
    xfactor = (mem.r + mem.w) + mem.rw
    yfactor = (mem.r + mem.w) * 1 + mem.rw

  column_mux_factor       = mem.process.column_mux_factor
  contacted_poly_pitch_um = mem.contacted_poly_pitch_nm / 1000
  fin_pitch_um            = mem.finPitch_nm / 1000
  width_in_bits           = int(mem.sram_data['width'])
  depth                   = int(mem.sram_data['depth'])
  num_banks               = int(mem.sram_data['banks'])

  # Corresponds to the recommended 122 cell in asap7
  bitcell_height = 10 * fin_pitch_um
  bitcell_width = 2 * contacted_poly_pitch_um

  all_bitcell_height =  bitcell_height * depth
  all_bitcell_width =  bitcell_width * width_in_bits

  if num_banks == 2 or num_banks == 4:
    all_bitcell_height = all_bitcell_height / num_banks
    all_bitcell_width = all_bitcell_width * num_banks
  elif num_banks != 1:
    raise Exception("Unsuppor\d number of banks: {}".format(num_banks))

  all_bitcell_height = all_bitcell_height / column_mux_factor
  all_bitcell_width = all_bitcell_width * column_mux_factor

  total_height = all_bitcell_height * 1.2
  total_width = all_bitcell_width * 1.2

  return total_height * yfactor, total_width * xfactor