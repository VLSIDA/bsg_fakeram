################################################################################
# PROCESS CLASS
#
# This class stores the infromation about the process that the memory is being
# generated in. Every memory has a pointer to a process object. The information
# for the process comes from the json configuration file (typically before the
# "sram" list section).
# Additions:
#    - Added required information for asap7 (from ABKGroup's FakeRAM2.0)
################################################################################

class Process:

  def __init__(self, json_data):

    # From JSON configuration file
    self.tech_nm        = int(json_data['tech_nm'])
    self.metalPrefix    = str(json_data['metalPrefix'])
    self.voltage        = str(json_data['voltage'])
    if ('pinPitch_nm' in json_data):
      self.LRpitch_um     = self.TBpitch_um  = self.PSpitch_um = int(json_data['pinPitch_nm']) / 1000.0
    else:
      self.TBpitch_um = int(json_data['TBpinPitch_nm']) / 1000.0
      self.LRpitch_um = int(json_data['LRpinPitch_nm']) / 1000.0
      self.PSpitch_um = int(json_data['LRpinPitch_nm']) / 1000.0 if 'PSpinPitch_nm' not in json_data else int(json_data['PSpinPitch_nm']) / 1000.0
    if ('pinWidth_nm' in json_data):
      self.TBwidth_um     = self.LRwidth_um = self.PSwidth_um  = int(json_data['pinWidth_nm']) / 1000.0
    else:
      self.TBwidth_um = int(json_data['TBpinWidth_nm']) / 1000.0
      self.LRwidth_um = int(json_data['LRpinWidth_nm']) / 1000.0 
      self.PSwidth_um = int(json_data['LRpinWidth_nm']) / 1000.0 if 'PSpinWidth_nm' not in json_data else int(json_data['PSpinWidth_nm']) / 1000.0 
    if ('pinHeight_nm' in json_data):
      self.LRheight_um    = self.TBheight_um  = int(json_data['pinPitch_nm']) / 1000.0 if 'pinHeight_nm' not in json_data else int(json_data['pinHeight_nm']) / 1000.0
    else:
      self.TBheight_um   = self.TBwidth_um * 3 if 'TBpinHeight_nm' not in json_data else int(json_data['TBpinHeight_nm']) / 1000.0
      self.LRheight_um   = self.LRwidth_um * 3 if 'LRpinHeight_nm' not in json_data else int(json_data['LRpinHeight_nm']) / 1000.0
    

    if (self.tech_nm == 7):
      # Required from JSON if tech nm is 7
      self.fin_pitch_nm = int(json_data['fin_pitch_nm'])
      self.contacted_poly_pitch_nm = int(json_data['contacted_poly_pitch_nm'])
      self.column_mux_factor = int(json_data['column_mux_factor'])
      
      
    # Optional keys
    self.snapWidth_nm   = int(json_data['snapWidth_nm']) if 'snapWidth_nm' in json_data else 1
    self.snapHeight_nm  = int(json_data['snapHeight_nm']) if 'snapHeight_nm' in json_data else 1
    self.flipPins       = str(json_data['flipPins']) if 'flipPins' in json_data else 'false'
    # Explicit layer overrides for LR and TB pins (overrides flipPins layer logic)
    self.LRpinLayer     = str(json_data['LRpinLayer']) if 'LRpinLayer' in json_data else ''
    self.TBpinLayer     = str(json_data['TBpinLayer']) if 'TBpinLayer' in json_data else ''
    
    self.vlogTimingCheckSignalExpansion = bool(json_data['vlogTimingCheckSignalExpansion']) if 'vlogTimingCheckSignalExpansion' in json_data else False

    # Converted values
    self.tech_um     = self.tech_nm / 1000.0
    

