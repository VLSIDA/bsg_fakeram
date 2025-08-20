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
    self.tech_nm                  = int(json_data['tech_nm'])
    self.voltage                  = str(json_data['voltage'])
    self.metalPrefix              = str(json_data['metalPrefix']) if 'metalPrefix' in json_data else None
    self.pinWidth_nm              = int(json_data['pinWidth_nm'])
    self.pinPitch_nm              = int(json_data['pinPitch_nm'])
    self.manufacturing_grid_nm    = int(json_data['manufacturing_grid_nm'])
    self.t_setup_ns               = float(json_data['t_setup_ns'])
    self.t_hold_ns                = float(json_data['t_hold_ns'])
    self.cap_input_pf             = float(json_data['cap_input_pf'])
    
    # Optional
    self.y_offset_nm              = int(json_data['y_offset_nm']) if 'y_offset_nm' in json_data else 0
    self.x_offset_nm              = int(json_data['x_offset_nm']) if 'x_offset_nm' in json_data else 0
    self.x_pinPitch_nm            = int(json_data['x_pinPitch_nm']) if 'x_pinPitch_nm' in json_data else self.pinPitch_nm
    self.pinHeight_nm             = int(json_data['pinHeight_nm']) if 'pinHeight_nm' in json_data else self.pinWidth_nm # Default to square pins
    self.column_mux_factor        = int(json_data['column_mux_factor']) if 'column_mux_factor' in json_data else 1
    self.snapWidth_nm             = int(json_data['snapWidth_nm']) if 'snapWidth_nm' in json_data else 1
    self.snapHeight_nm            = int(json_data['snapHeight_nm']) if 'snapHeight_nm' in json_data else 1
    self.metalLayerPins           = str(json_data['metalLayerPins']) if 'metalLayerPins' in json_data else str(self.metalPrefix + '4')
    self.verticalPinsOnly         = json_data['verticalPinsOnly'] if 'verticalPinsOnly' in json_data else False
    self.flipPins                 = json_data['flipPins'] if 'flipPins' in json_data else False
    self.use_custom_tech          = json_data['use_custom_tech'] if 'use_custom_tech' in json_data else False
    self.heightSnaptoTrack        = json_data['heightSnaptoTrack'] if 'heightSnaptoTrack' in json_data else False

    # Converted values
    self.tech_um                  = self.tech_nm / 1000.0
    self.pinWidth_um              = self.pinWidth_nm / 1000.0
    self.pinHeight_um             = self.pinHeight_nm / 1000.0
    self.pinPitch_um              = self.pinPitch_nm / 1000.0
    self.x_pinPitch_um            = self.x_pinPitch_nm / 1000.0
    self.manufacturing_grid_um    = self.manufacturing_grid_nm / 1000.0
    self.y_offset_um              = self.y_offset_nm / 1000.0
    self.x_offset_um              = self.x_offset_nm / 1000.0

    # TODO: From original bsg fakeram
    # self.vlogTimingCheckSignalExpansion = bool(json_data['vlogTimingCheckSignalExpansion']) if 'vlogTimingCheckSignalExpansion' in json_data else False
    # self.metal_track_pitch_um  = self.metal_track_pitch_nm / 1000.0
    # if (self.pin_pitch_nm % self.metal_track_pitch_nm != 0):
    #   print("Pin Pitch %d not a multiple of Metal Track Pitch %d" %(self.pin_pitch_nm,self.metal_track_pitch_nm))
    #   sys.exit(1)

    if (self.pinPitch_nm % self.manufacturing_grid_nm != 0):
      print("Pin Pitch %d not a multiple of Manufacturing Grid %d" %(self.pinPitch_nm, self.manufacturing_grid_nm))
      sys.exit(1)

    required = [
      self.tech_nm,
      self.voltage,
      # self.metalPrefix,
      # self.metalLayerPins,
      self.pinWidth_nm,
      self.pinPitch_nm,
      self.manufacturing_grid_nm,
      self.t_setup_ns,
      self.t_hold_ns,
      self.cap_input_pf
    ]

    for param in required:
      if param is None or param == "":
        print(f"Parameter: {param} either empty or not an integer!")
        sys.exit(1)