import os
import math

from utils.init_mem.modules import *
from decimal import Decimal, ROUND_UP
from utils.cacti_config import cacti_config

# TODO: should also want to print summary of srams at end of run
def print_init_sram(gbl):
    total_ports = gbl.r + gbl.w + gbl.rw
    if total_ports == 0:
      raise Exception("SRAM needs at least one port.")
    print(f'\n '
          f'\n##################################################\n')
    print(f'Creating SRAM: {gbl.name} of width: {gbl.width_in_bits} and depth: {gbl.depth}')
    print('\n##################################################\n')
    print(f'Total Ports                 : {total_ports} \n'
          f'Num Port R                  : {gbl.r} \n'
          f'Num Port W                  : {gbl.w} \n'
          f'Num Port RW                 : {gbl.rw} \n'
          f'Num Banks                   : {gbl.num_banks}\n'
            )
  
    if gbl.has_write_mask:
        print(
           f'Has write mask    : True\n'
           f'Num Port Wmask    : {gbl.wmask}\n'
           f'Write granularity : {gbl.write_granularity}\n'
        )
    
    print(
         f'\nMETAL LAYER PINS\n'
         f'metLayerHorizontalPin       : {gbl.process.metLayerHorizontalPin}\n'
         f'metLayerVerticalPin         : {gbl.process.metLayerVerticalPin}\n'

         f'\nMETAL LAYER POWER GRID\n'
         f'metLayerPowerGrid           : {gbl.process.metLayerPowerGrid}\n'
         f'directionPowerGrid          : {gbl.process.directionPowerGrid}\n'

         f'\nPITCH PARAMETERS\n'
         f'pinSnapMode                 : {gbl.process.pinSnapMode}\n'
         f'{'x_trackPitch_nm' if gbl.process.pinSnapMode == 'track' else 'x_pinPitch_nm'}             : {gbl.process.x_trackPitch_nm if gbl.process.pinSnapMode == 'track' else gbl.process.x_pinPitch_nm}\n'
         f'{'y_trackPitch_nm' if gbl.process.pinSnapMode == 'track' else 'y_pinPitch_nm'}             : {gbl.process.y_trackPitch_nm if gbl.process.pinSnapMode == 'track' else gbl.process.y_pinPitch_nm}\n'
         f'y_pinOffset_um              : {gbl.process.y_pinOffset_um}\n'
         f'x_pinOffset_um              : {gbl.process.x_pinOffset_um}\n'
         f'pitchFactor                 : {gbl.pitchFactor}\n'
         
         f'\nPIN DIMENSIONS\n'
         f'pinWidth_nm                 : {gbl.process.pinWidth_nm}\n'
         f'pinHeight_nm                : {gbl.process.pinHeight_nm}\n'        

         f'\nTIMING\n'        
         f't_setup_ns                  : {gbl.t_setup_ns}\n'
         f't_hold_ns                   : {gbl.t_hold_ns}\n'
         f'cap_input_pf                : {gbl.cap_input_pf}\n'
         
         f'\nADDITIONAL PARAMS\n'
         f'heightSnaptoTrack           : {gbl.process.heightSnaptoTrack}\n'
         f'widthSnaptoTrack            : {gbl.process.widthSnaptoTrack}\n'
         f'equidistantPins             : {gbl.process.equidistantPins}\n'
         f'verticalPinsOnly            : {gbl.process.verticalPinsOnly}\n'
         f'column_mux_factor overriden : {gbl.column_mux_factor_overriden}\n'
         f'column_mux_factor           : {gbl.process.column_mux_factor}\n'
         f'snapWidth_nm                : {gbl.process.snapWidth_nm}\n'
         f'snapHeight_nm               : {gbl.process.snapHeight_nm}\n'
         f'\nUSE CUSTOM TECH: {gbl.process.use_custom_tech}\n'
    )
        
    if gbl.process.use_custom_tech == True:
        print(
            f'hybrid:                     : {gbl.custom_data.hybrid}\n'
            f'use_custom_area             : {gbl.custom_data.use_custom_area}\n'
            f'transistor_architecture     : {gbl.custom_data.transistor_architecture}\n'
            f'access_time_ns              : {gbl.custom_data.access_time_ns or gbl.access_time_ns}\n'
            f'cycle_time_ns               : {gbl.custom_data.cycle_time_ns or gbl.cycle_time_ns}\n'
            f'fo4_ps                      : {gbl.custom_data.fo4_ps or gbl.fo4_ps}\n'
            f'dyn_write_energy_nj         : {gbl.dyn_write_energy_nj or None}\n'
            f'standby_leakage_per_bank_mW : {gbl.custom_data.standby_leakage_per_bank_mW or gbl.standby_leakage_per_bank_mW}\n'
            f'pin_dynamic_power_mW        : {gbl.custom_data.pin_dynamic_power_mW or gbl.pin_dynamic_power_mW}\n'
            f'contacted_poly_pitch_nm     : {gbl.custom_data.contacted_poly_pitch_nm}\n'
            f'finPitch_nm                 : {gbl.custom_data.finPitch_nm}\n'
            f'h0_tracks                   : {gbl.custom_data.h0_tracks}\n'
            f'w0_polys                    : {gbl.custom_data.w0_polys}\n'
            f'dh_read                     : {gbl.custom_data.dh_read}\n'
            f'dw_read                     : {gbl.custom_data.dw_read}\n'
            f'dh_write                    : {gbl.custom_data.dh_write}\n'
            f'dw_write                    : {gbl.custom_data.dw_write}\n'
            f'dh_rw                       : {gbl.custom_data.dh_rw}\n'
            f'dw_rw                       : {gbl.custom_data.dw_rw}\n\n')
    print(
        f'Total height                : {gbl.height_um}\n'
        f'Total width                 : {gbl.width_um}\n')
    print('\n ')

# def round_up_to_multiple(n, multiple) -> float:
    # return math.ceil(n / multiple) * multiple


def round_up_to_multiple(n, multiple) -> float:
    d_n = Decimal(str(n))
    d_multiple = Decimal(str(multiple))
    # Divide, round up, then multiply back
    quotient = (d_n / d_multiple).to_integral_value(rounding=ROUND_UP)
    result = quotient * d_multiple
    return float(result)

def get_custom(gbl, custom_param, cacti_data) -> float:
  """ use cacti value of parameter if hybrid is not used, if hybrid
  is true then either use cacti data or custom parameter if given """
  return cacti_data if gbl.custom_data.hybrid == False else (custom_param or cacti_data)

def use_cacti(gbl) -> bool:
  """ Only returns true if hybrid option is used """
  if gbl.process.use_custom_tech == False or (gbl.process.use_custom_tech == True and gbl.custom_data.hybrid == True):
     print('Running Cacti with overidden values...\n') if gbl.custom_data.hybrid == True else print('Running Cacti...\n')
     return True
  print("Not using cacti...")
  return False

def run_cacti( gbl ) -> None:
    fid = open(os.sep.join([gbl.results_dir,'cacti.cfg']), 'w')
    fid.write(
        cacti_config.format(
            gbl.total_size,
            gbl.width_in_bytes,
            gbl.rw,
            gbl.r,
            gbl.w,
            gbl.process.tech_um,
            gbl.width_in_bytes * 8,
            gbl.num_banks,
            gbl.cache_type
        )
    )
    fid.close()
    odir = os.getcwd()
    os.chdir(gbl.cacti_dir )
    cmd = os.sep.join(['.','cacti -infile ']) + os.sep.join([gbl.results_dir,'cacti.cfg'])
    os.system( cmd)
    os.chdir(odir)

def get_cmux_dimensions(gbl, height_um, width_um) -> float:
    """ Same column mux calculation logic from FakeRAM2.0 """
    height_um = height_um / gbl.column_mux_factor
    width_um = width_um * gbl.column_mux_factor
    return height_um, width_um

def get_bank_dimensions(gbl, height_um, width_um) -> float:
    """ Same bank calculation logic from FakeRAM2.0 """
    height_um = height_um / gbl.num_banks
    width_um = width_um * gbl.num_banks
    return height_um, width_um

def get_write_granularity(gbl) -> int:
    """ returns write granularity of sram """
    sram_data         = gbl.sram_data
    has_write_mask    = gbl.has_write_mask
    write_granularity = gbl.write_granularity
    width_in_bits     = gbl.width_in_bits

    if 'write_granularity' in sram_data:
        has_write_mask = True
        write_granularity = int(sram_data['write_granularity'])
    else:
        has_write_mask = False
        write_granularity = width_in_bits
        
    if has_write_mask:
        if (width_in_bits % write_granularity == 0):
            return width_in_bits // write_granularity
        else:
            raise Exception(f"Invalid write_granularity: width_in_bits ({width_in_bits}) is not divisible by write_granularity ({gbl.write_granularity}).")
    else:
        return 0  # No write mask