
from utils.gen_lef.modules import *
from utils.gen_lef.logic import *

################################################################################
# CREATE LEF view for the given SRAM
################################################################################

def generate_lef(mem):
    LEF_Parameters(mem)

    lef_writer = LEF_WriteFunctions(mem) 

    port_generator = GeneratePorts(mem)
    
    lef_writer.gen_header()

    port_generator.generate_ports()
    
    lef_writer.gen_straps()
    
    lef_writer.gen_obs()
