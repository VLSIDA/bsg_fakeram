
import os

from pathlib import Path
from utils.mem_init.modules import *
from utils.mem_init.mem_area import *
from utils.mem_init.mem_globals import *


def memory_initializer(mem: object, custom_data: dict, output_dir = None, cacti_dir = None) -> object:

    name = mem.name

    if output_dir: # Output dir was set by command line option
        p = str(Path(output_dir).expanduser().resolve(strict=False))
        results_dir = os.sep.join([p, name])
    else:
        results_dir = os.sep.join([os.getcwd(), 'results', name])
    if not os.path.exists( results_dir ):
        os.makedirs( results_dir )


    # Setup CACTI directory
    if cacti_dir:
        cacti_dir = cacti_dir
    else:
        cacti_dir = os.environ['CACTI_BUILD_DIR']
    
    mem.results_dir = results_dir
    mem.cacti_dir   = cacti_dir
    """ First want to initialize custom data in case 
    custom data is used for a custom only or hybrid sram
    configuration """
    custom_inst = CustomData(custom_data)
    mem.custom_data = custom_inst

    if use_cacti(mem):      
        """_run_cacti: shell out to cacti to generate a csv file with more data
        regarding this memory based on the input parameters from the json
        configuration file."""
        run_cacti(mem)

        # Parse CACTI results
        with open( os.sep.join([results_dir, 'cacti.cfg.out']), 'r' ) as fid:
            lines = [line for line in fid]
            cacti_data = lines[-1].split(',')

        cacti_inst = CactiData(mem, cacti_data)

        # Update mem object with cacti attributes
        mem.__dict__.update(cacti_inst.__dict__)

        # TODO: modularize this somewhere
        mem.height_um, mem.width_um = get_cmux_dimensions(mem, mem.height_um, mem.width_um)
        mem.height_um, mem.width_um = get_bank_dimensions(mem, mem.height_um, mem.width_um)

        """ Cacti is ran and will be overriden by custom values """
        if custom_inst.hybrid == True:
            hybrid_inst = HybridData(
                access_time_ns              = custom_inst.access_time_ns,
                cycle_time_ns               = custom_inst.cycle_time_ns,
                pin_dynamic_power_mW        = custom_inst.pin_dynamic_power_mW,
                standby_leakage_per_bank_mW = custom_inst.standby_leakage_per_bank_mW,
                fo4_ps                      = custom_inst.fo4_ps
            )

            # override cacti values from given custom data
            hybrid_overrides = {k: v for k, v in hybrid_inst.__dict__.items() 
                              if v is not None}
            mem.__dict__.update(hybrid_overrides)

    else:
        print('custom only')
        # Update Memory class with custom data
        mem.__dict__.update(custom_inst.__dict__)

    return mem_finalized_object(mem)

def mem_finalized_object(mem: object):
    """ inject additional variables here once main memory is initialized """

    mem.wmask = get_write_granularity(mem)

    mem.height_um, mem.width_um = get_macro_dimensions(mem)

    mem.area_um = final_area(mem)


    return mem