import sys

from utils.init_mem.mem_area import get_macro_dimensions

################################################################################
# CUSTOM CLASS
#
# This class stores the infromation about the custom parameters that the memory
# is being generated in.
################################################################################

class CustomData:
    def __init__(self, custom_data):
        self.hybrid                      = custom_data['hybrid'] if 'hybrid' in custom_data else False

        # TODO
        self.use_custom_area            = bool(custom_data.get('use_custom_area', False))
        self.transistor_architecture    = str(custom_data.get('transistor_architecture', None))

        # Required Custom Only Params / Optional Hybrid Params
        self.access_time_ns              = float(custom_data.get('access_time_ns', 0.0))
        self.cycle_time_ns               = float(custom_data.get('cycle_time_ns', 0.0))
        self.fo4_ps                      = float(custom_data.get('fo4_ps', 0.0))
        self.standby_leakage_per_bank_mW = float(custom_data.get('standby_leakage_per_bank_mW', 0.0))
        self.pin_dynamic_power_mW        = float(custom_data.get('pin_dynamic_power_mW', 0.0))
        self.finPitch_nm                 = float(custom_data.get('finPitch_nm', 0.0))
        self.contacted_poly_pitch_nm     = float(custom_data.get('contacted_poly_pitch_nm', 0.0))
        
        # FinFet
        self.h0_tracks                   = float(custom_data.get('h0_tracks', 0.0))
        self.w0_polys                    = float(custom_data.get('w0_polys', 0.0))

        # Optional Custom Params
        self.dh_read                     = float(custom_data.get('dh_read', 1))
        self.dw_read                     = float(custom_data.get('dw_read', 1))
        self.dh_write                    = float(custom_data.get('dh_write', 1))
        self.dw_write                    = float(custom_data.get('dw_write', 1))
        self.dh_rw                       = float(custom_data.get('dh_rw', 1))
        self.dw_rw                       = float(custom_data.get('dw_rw', 1))
