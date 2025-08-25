
from utils.gen_lef.modules.lef_parameters import *
from utils.gen_lef.modules.pin_parameters import *
from utils.gen_lef.logic import *

################################################################################
# CREATE LEF view for the given SRAM
################################################################################

def generate_lef( mem ):
    # Memory parameters
    lef_p = LEF_Parameters(mem)

    pin_params = PinStartCoords(lef_p)

    gen_header(lef_p)

    gen_r_port(pin_params)
    gen_w_port(pin_params)
    gen_rw_port(pin_params)

    gen_strapes(lef_p)

    gen_obs(lef_p)
