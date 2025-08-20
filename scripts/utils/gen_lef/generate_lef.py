
from utils.gen_lef.modules.lef_parameters import *
from utils.gen_lef.modules.pin_parameters import *
from utils.gen_lef.logic import *

################################################################################
# CREATE LEF view for the given SRAM
################################################################################

def generate_lef( mem ):
    # Memory parameters
    LEF_params = LEF_Parameters(mem)
    pin_params = PinStartCoords(LEF_params)

    gen_header(LEF_params)

    gen_r_port(pin_params)
    gen_w_port(pin_params)
    gen_rw_port(pin_params)

    gen_strapes(mem, LEF_params)

    gen_obs(LEF_params)
