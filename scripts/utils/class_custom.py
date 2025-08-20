import sys

################################################################################
# CUSTOM CLASS
#
# This class stores the infromation about the custom parameters that the memory
# is being generated in.
################################################################################

class Custom:
    def __init__(self, process, custom_data):
        self.process                     = process
        self.hybrid                      = custom_data['hybrid'] if 'hybrid' in custom_data else False

        # Required Custom Only Params / Optional Hybrid Params
        self.access_time_ns              = float(custom_data['access_time_ns']) if 'access_time_ns' in custom_data else None
        self.cycle_time_ns               = float(custom_data['cycle_time_ns']) if 'cycle_time_ns' in custom_data else None
        self.fo4_ps                      = float(custom_data['fo4_ps']) if 'fo4_ps' in custom_data else None
        self.standby_leakage_per_bank_mW = float(custom_data['standby_leakage_per_bank_mW']) if 'standby_leakage_per_bank_mW' in custom_data else None
        self.pin_dynamic_power_mW        = float(custom_data['pin_dynamic_power_mW']) if 'pin_dynamic_power_mW' in custom_data else None
        self.finPitch_nm                 = float(custom_data['finPitch_nm']) if 'finPitch_nm' in custom_data else None
        self.contacted_poly_pitch_nm     = float(custom_data['contacted_poly_pitch_nm']) if 'contacted_poly_pitch_nm' in custom_data else None
        self.h0_tracks                   = float(custom_data['h0_tracks']) if 'h0_tracks' in custom_data else None
        self.w0_polys                    = float(custom_data['w0_polys']) if 'w0_polys' in custom_data else None

        # Optional Custom Params
        self.column_mux_factor           = float(custom_data['column_mux_factor']) if 'column_mux_factor' in custom_data else 1
        self.dh_read                     = float(custom_data['dh_read']) if 'dh_read' in custom_data else 1
        self.dw_read                     = float(custom_data['dw_read']) if 'dw_read' in custom_data else 1
        self.dh_write                    = float(custom_data['dh_write']) if 'dh_write' in custom_data else 1
        self.dw_write                    = float(custom_data['dw_write']) if 'dw_write' in custom_data else 1
        self.dh_rw                       = float(custom_data['dh_rw']) if 'dh_rw' in custom_data else 1
        self.dw_rw                       = float(custom_data['dw_rw']) if 'dw_rw' in custom_data else 1

        use_custom_only_requirements = [
            self.access_time_ns,
            self.cycle_time_ns,
            self.fo4_ps,
            self.standby_leakage_per_bank_mW,
            self.pin_dynamic_power_mW,
            self.finPitch_nm,
            self.contacted_poly_pitch_nm,
            self.column_mux_factor,
            self.h0_tracks,
            self.w0_polys
        ]

        # Custom only requirement checking
        if is_custom_only(self):
            for param in use_custom_only_requirements:
                if param is None and param == "":
                    print(f"Parameter: {param} either empty or not an integer!")
                    sys.exit(1)
        
def is_custom_only(self) -> bool:
    return self.process.use_custom_tech == True and self.hybrid == False
    