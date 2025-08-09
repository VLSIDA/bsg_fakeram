import sys

################################################################################
# PROCESS CLASS
#
# This class stores the infromation about the process that the memory is being
# generated in. Every memory has a pointer to a process object. The information
# for the process comes from the json configuration file (typically before the
# "sram" list section).
################################################################################

class Process: 

  def __init__(self, json_data): 
    # Needed parameters from JSON File
    self.tech_nm                  = int(json_data['tech_nm']) if 'tech_nm' in json_data else None
    self.voltage                  = str(json_data['voltage']) if 'voltage' in json_data else None
    self.metalPrefix              = str(json_data['metalPrefix']) if 'metalPrefix' in json_data else None
    self.metalLayerPins           = str(json_data['metal_layer']) if 'metal_layer' in json_data else str(self.metalPrefix + '4')
    self.pinWidth_nm              = int(json_data['pinWidth_nm']) if 'pinWidth_nm' in json_data else None
    self.pinPitch_nm              = int(json_data['pinPitch_nm']) if 'pinPitch_nm' in json_data else None
    self.manufacturing_grid_nm    = int(json_data['manufacturing_grid_nm']) if 'manufacturing_grid_nm' in json_data else None
    
    # Optional
    self.snapWidth_nm             = int(json_data['snapWidth_nm']) if 'snapWidth_nm' in json_data else 1
    self.snapHeight_nm            = int(json_data['snapHeight_nm']) if 'snapHeight_nm' in json_data else 1
    self.column_mux_factor        = int(json_data['column_mux_factor']) if 'column_mux_factor' in json_data else 1
    self.pinHeight_nm             = int(json_data['pinHeight_nm']) if 'pinHeight_nm' in json_data else (self.pinWidth_nm) # Default to square pins
    self.flipPins                 = str(json_data['flipPins']) if 'flipPins' in json_data else 'false'
    self.custom_tech              = str(json_data['custom_tech_name']) if 'custom_tech_name' in json_data else False
    self.hybrid                   = str(json_data['hybrid']).lower() == 'true' if 'hybrid' in json_data else False
    print('Hybrid checking: ', self.hybrid)
    
    # Converted values
    self.tech_um                  = self.tech_nm / 1000.0
    self.pinWidth_um              = self.pinWidth_nm / 1000.0
    self.pinHeight_um             = self.pinHeight_nm / 1000.0
    self.pinPitch_um              = self.pinPitch_nm / 1000.0
    self.manufacturing_grid_um    = self.manufacturing_grid_nm / 1000.0

    # Unused
    self.vlogTimingCheckSignalExpansion = bool(json_data['vlogTimingCheckSignalExpansion']) if 'vlogTimingCheckSignalExpansion' in json_data else False
    # self.metal_track_pitch_um  = self.metal_track_pitch_nm / 1000.0


    # if (self.pin_pitch_nm % self.metal_track_pitch_nm != 0):
    #   print("Pin Pitch %d not a multiple of Metal Track Pitch %d" %(self.pin_pitch_nm,self.metal_track_pitch_nm))
    #   sys.exit(1)
    if (self.pinPitch_nm % self.manufacturing_grid_nm != 0):
      print("Pin Pitch %d not a multiple of Manufacturing Grid %d" %(self.pinPitch_nm, self.manufacturing_grid_nm))
      sys.exit(1)

"""
self.tech_nm
self.metalPrefix
self.pinWidth_nm
self.pinPitch_nm
self.voltage
self.snapWidth_nm
self.snapHeight_nm
self.flipPins
self.pinHeight_nm
self.vlogTimingCheckSignalExpansion
"""
