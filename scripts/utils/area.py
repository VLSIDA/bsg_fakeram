import os
import sys
import math 


def get_macro_dimensions(mem) -> int:
  """DYNAMIC SIZING (preserve variable names; neutralize global port scaling)
  Original multiplied whole macro by (r+w+rw) in x and y.
  Keep xfactor/yfactor variables but set them to neutral (or asymmetric) scales."""


  column_mux_factor       = int(max(1, int(mem.column_mux_factor)))
  contacted_poly_pitch_um = mem.contacted_poly_pitch_nm / 1000.0
  fin_pitch_um            = mem.finPitch_nm / 1000.0
  width_in_bits           = int(mem.sram_data['width'])
  depth                   = int(mem.sram_data['depth'])
  num_banks               = int(mem.sram_data['banks'])

  H0_TRACKS               = mem.H0_TRACKS or 1
  W0_POLYS                = mem.W0_POLYS or 1

  # Dummy overhead
  DH_READ                 = mem.DH_READ or 1
  DW_READ                 = mem.DW_READ or 1
  DH_WRITE                = mem.DH_WRITE or 1
  DW_WRITE                = mem.DW_WRITE or 1
  DH_RW                   = mem.DH_RW or 1
  DW_RW                   = mem.DW_RW or 1

  # Compute bitcell height/width in microns from tracks/pitches
  h_tracks = H0_TRACKS + mem.r*DH_READ + mem.w*DH_WRITE + mem.rw*DH_RW
  w_polys  = W0_POLYS  + mem.r*DW_READ + mem.w*DW_WRITE + mem.rw*DW_RW

  bitcell_height = h_tracks * fin_pitch_um
  bitcell_width  = w_polys  * contacted_poly_pitch_um

  read_ports = max(1, mem.r + mem.rw)
  if read_ports >= 3:
    cmux_cap = 2
  elif read_ports == 2:
    cmux_cap = 4
  else:
    cmux_cap = 8
  effective_cmux = max(1, min(column_mux_factor, cmux_cap))
  print(f'Effect cmux: {effective_cmux}')

  # rows reduced by mux 
  # columns increased by mux
  all_bitcell_height = bitcell_height * (depth / effective_cmux)
  all_bitcell_width  = bitcell_width  * (width_in_bits * effective_cmux)

  if num_banks == 2 or num_banks == 4:
    all_bitcell_height = all_bitcell_height / num_banks
    all_bitcell_width  = all_bitcell_width * num_banks
  elif num_banks != 1:
    raise Exception("Unsupported number of banks: {}".format(num_banks))

  total_height = all_bitcell_height * 1.2
  total_width  = all_bitcell_width  * 1.2

  return total_height, total_width
