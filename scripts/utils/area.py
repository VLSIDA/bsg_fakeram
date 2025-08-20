import os
import sys
import math 


def get_macro_dimensions(mem, process) -> int:
  """DYNAMIC SIZING (preserve variable names; neutralize global port scaling)
  Original multiplied whole macro by (r+w+rw) in x and y.
  Keep xfactor/yfactor variables but set them to neutral (or asymmetric) scales."""


  column_mux_factor       = int(max(1, int(mem.column_mux_factor)))
  contacted_poly_pitch_um = mem.contacted_poly_pitch_nm / 1000.0
  fin_pitch_um            = mem.finPitch_nm / 1000.0
  width_in_bits           = int(mem.sram_data['width'])
  depth                   = int(mem.sram_data['depth'])
  num_banks               = int(mem.sram_data['banks'])

  h0_tracks               = mem.h0_tracks or 1
  w0_polys                = mem.w0_polys or 1

  # dummy overhead
  dh_read                 = mem.dh_read or 1
  dw_read                 = mem.dw_read or 1
  dh_write                = mem.dh_write or 1
  dw_write                = mem.dw_write or 1
  dh_rw                   = mem.dh_rw or 1
  dw_rw                   = mem.dw_rw or 1

  # Compute bitcell height/width in microns from tracks/pitches
  h_tracks = h0_tracks + mem.r*dh_read + mem.w*dh_write + mem.rw*dh_rw
  w_polys  = w0_polys  + mem.r*dw_read + mem.w*dw_write + mem.rw*dw_rw

  bitcell_height = h_tracks * fin_pitch_um
  bitcell_width  = w_polys  * contacted_poly_pitch_um

  read_ports = max(1, mem.r + mem.rw)
  if read_ports >= 3:
    cmux_cap = 2
  elif read_ports == 2:
    cmux_cap = 4
  else:
    cmux_cap = 8
  aspect_ratio_factor = max(1, min(column_mux_factor, cmux_cap))

  # rows reduced by mux 
  # columns increased by mux
  all_bitcell_height = bitcell_height * depth
  all_bitcell_width  = bitcell_width  * width_in_bits

  if num_banks == 2 or num_banks == 4:
    all_bitcell_height = all_bitcell_height / num_banks
    all_bitcell_width  = all_bitcell_width * num_banks
  elif num_banks != 1:
    raise Exception("Unsupported number of banks: {}".format(num_banks))
  
  # Same logic from FakeRAM2.0
  all_bitcell_height = all_bitcell_height / aspect_ratio_factor
  all_bitcell_width = all_bitcell_width * aspect_ratio_factor

  total_height = all_bitcell_height * 1.2
  total_width  = all_bitcell_width  * 1.2
  return total_height, total_width
