import os
import sys
import math 
from utils.mem_init.mem_globals import *


def get_macro_dimensions(mem) -> float:
	"""DYNAMIC SIZING (preserve variable names; neutralize global port scaling)
	Original multiplied whole macro by (r+w+rw) in x and y.
	Keep xfactor/yfactor variables but set them to neutral (or asymmetric) scales."""
	if use_cacti(mem):
		return mem.height_um, mem.width_um
	
	contacted_poly_pitch_um = mem.contacted_poly_pitch_nm / 1000.0
	fin_pitch_um            = mem.finPitch_nm / 1000.0
	width_in_bits           = int(mem.sram_data['width'])
	depth                   = int(mem.sram_data['depth'])
	num_banks               = int(mem.sram_data['banks'])
	h0_tracks               = mem.h0_tracks or 1
	w0_polys                = mem.w0_polys or 1
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

	# rows reduced by mux 
	# columns increased by mux
	all_bitcell_height = bitcell_height * depth
	all_bitcell_width  = bitcell_width  * width_in_bits

	if num_banks == 2 or num_banks == 4:
		all_bitcell_height, all_bitcell_width = get_bank_dimensions(mem, all_bitcell_height, all_bitcell_width)
	elif num_banks != 1:
		raise Exception("Unsupported number of banks: {}".format(num_banks))

	# Same logic from FakeRAM2.0
	all_bitcell_height, all_bitcell_width = get_cmux_dimensions(mem, all_bitcell_height, all_bitcell_width)


	total_height = all_bitcell_height * 1.2
	total_width  = all_bitcell_width  * 1.2
	return total_height, total_width

def final_area(mem) -> float:
    snapWidth_nm = mem.process.snapWidth_nm
    snapHeight_nm = mem.process.snapHeight_nm
    manufacturing_grid_nm = mem.process.manufacturing_grid_nm
    x_pinPitch_um = mem.process.x_pinPitch_um
    pinPitch_um = mem.process.pinPitch_um

    # TODO:
    # Adjust to snap
    # mem.width_um = (math.ceil((mem.width_um*1000.0)/snapWidth_nm)*snapWidth_nm)/1000.0
    # mem.height_um = (math.ceil((mem.height_um*1000.0)/snapHeight_nm)*snapHeight_nm)/1000.0

    # Need to know the idea of snapping width and height
    mem.width_um = round_up_to_multiple(mem.width_um*1000.0, snapWidth_nm) / 1000.0
    mem.height_um = round_up_to_multiple(mem.height_um*1000.0, snapHeight_nm) / 1000.0

    mem.height_um = round_up_to_multiple(mem.height_um, manufacturing_grid_nm)
    mem.width_um = round_up_to_multiple(mem.width_um, manufacturing_grid_nm)

    # TODO: snap to track pitch not pin pitch,
    # Use pin pitch for now (assumes track pitch)
    y_track_pitch = pinPitch_um
    x_track_pitch = x_pinPitch_um

    mem.height_um = round_up_to_multiple(mem.height_um, y_track_pitch)
    mem.width_um = round_up_to_multiple(mem.width_um, x_track_pitch)
    
    mem.area_um2 = mem.width_um * mem.height_um
    
    print(f'mem.width_um {mem.width_um}')
    print(f'mem.height_um {mem.height_um}')

    return mem.width_um * mem.height_um