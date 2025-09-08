import os
import math

from utils.mem_init.modules import *
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
         f'\nPIN PARAMETERS\n'
         f'metLayerHorizontalPin       : {gbl.process.metLayerHorizontalPin}\n'
         f'metLayerVerticalPin         : {gbl.process.metLayerVerticalPin}\n'
         f'y_pinPitch_um               : {gbl.process.y_pinPitch_um}\n'
         f'x_pinPitch_um               : {gbl.process.x_pinPitch_um}\n'
         f'pinPitchFactor              : {gbl.pinPitchFactor}\n'
         f'y_pinOffset_um              : {gbl.process.y_pinOffset_um}\n'
         f'x_pinOffset_um              : {gbl.process.x_pinOffset_um}\n'
         f'x_pinWidth_um               : {gbl.process.x_pinWidth_um}\n'
         f'x_pinHeight_um              : {gbl.process.x_pinHeight_um}\n'  
         f'y_pinWidth_um               : {gbl.process.y_pinWidth_um}\n'
         f'y_pinHeight_um              : {gbl.process.y_pinHeight_um}\n'  
         f'\nPOWER GRID\n'
         f'metLayerPowerGrid           : {gbl.process.metLayerPowerGrid}\n'
         f'directionPowerGrid          : {gbl.process.directionPowerGrid}\n'
         f'powerGridWidth_um           : {gbl.process.powerGridWidth_um}\n'
         f'powerGridPitch_um           : {gbl.process.powerGridPitch_um}\n'
         f'powerGridOffset_um          : {gbl.process.powerGridOffset_um}\n'
         
         f'\nTIMING\n'        
         f't_setup_ns                  : {gbl.t_setup_ns}\n'
         f't_hold_ns                   : {gbl.t_hold_ns}\n'
         f'cap_input_pf                : {gbl.cap_input_pf}\n'
         
         f'\nADDITIONAL PARAMS\n'
         f'heightSnapPinPitch          : {gbl.process.heightSnapPinPitch}\n'
         f'widthSnapPinPitch           : {gbl.process.widthSnapPinPitch}\n'
         f'column_mux_factor overriden : {gbl.column_mux_factor_overriden}\n'
         f'column_mux_factor           : {gbl.process.column_mux_factor}\n'
         f'snapWidth_um                : {gbl.process.snapWidth_um}\n'
         f'snapHeight_um               : {gbl.process.snapHeight_um}\n'
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
    width_in_bits     = gbl.width_in_bits

    if 'write_granularity' in sram_data and sram_data['write_granularity'] > 0:
        gbl.has_write_mask = True
        gbl.write_granularity = int(sram_data['write_granularity'])
    else:
        gbl.has_write_mask = False
        gbl.write_granularity = width_in_bits
        return
        
    if gbl.has_write_mask:
        if (width_in_bits % gbl.write_granularity == 0):
            return width_in_bits // gbl.write_granularity
        else:
            raise Exception(f"Invalid write_granularity: width_in_bits ({width_in_bits}) is not divisible by write_granularity ({gbl.write_granularity}).")
    else:
        return 0  # No write mask