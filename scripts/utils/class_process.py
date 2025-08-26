import sys

################################################################################
# PROCESS CLASS
#
# This class stores the infromation about the process that the memory is being
# generated in. Every memory has a pointer to a process object. The information
# for the process comes from the json configuration file (typically before the
# "sram" list section).
################################################################################

class Process :  
	def __init__(self, json_data) :  
		self.tech_nm               = int(json_data['tech_nm'])
		self.voltage               = str(json_data['voltage'])
		self.manufacturing_grid_nm = int(json_data.get('manufacturing_grid_nm', 1))
		self.metalPrefix           = str(json_data.get('metalPrefix', None))
		self.metLayerHorizontalPin = int(json_data['pinParams'].get('metLayerHorizontalPin', 4))
		self.metLayerVerticalPin   = int(json_data['pinParams'].get('metLayerVerticalPin', 4))
		self.x_pinOffset_nm		   = int(json_data['pinParams'].get('x_pinOffset_nm', 0))
		self.y_pinOffset_nm		   = int(json_data['pinParams'].get('y_pinOffset_nm', 0))
		self.x_pinPitch_nm         = int(json_data['pinParams'].get('x_pinPitch_nm', None))
		self.y_pinPitch_nm         = int(json_data['pinParams'].get('y_pinPitch_nm', None))
		self.pinWidth_nm 		   = int(json_data['pinParams'].get('pinWidth_nm'))
		self.pinHeight_nm		   = int(json_data['pinParams'].get('pinHeight_nm', self.pinWidth_nm))
		self.metLayerPowerGrid     = int(json_data['powerGridParams'].get('metLayerPowerGrid', 4))
		self.directionPowerGrid    = str(json_data['powerGridParams'].get('directionPowerGrid', "vertical"))
		self.powerGridWidth_nm     = int(json_data['powerGridParams'].get('powerGridWidth_nm', self.pinWidth_nm))
		self.powerGridPitch_nm     = int(json_data['powerGridParams'].get('powerGridPitch_nm', self.y_pinPitch_nm))
		self.powerGridOffset_nm	   = int(json_data['powerGridParams'].get('powerGridOffset_nm', 0))
		self.heightSnapPinPitch    = bool(json_data['additionalParams'].get('heightSnapPinPitch', False))
		self.widthSnapPinPitch     = bool(json_data['additionalParams'].get('widthSnapPinPitch', False))
		self.equidistantPins	   = bool(json_data['additionalParams'].get('equidistantPins', False))
		self.verticalPinsOnly	   = bool(json_data['additionalParams'].get('verticalPinsOnly', False))
		self.column_mux_factor     = int(json_data['additionalParams'].get('column_mux_factor', 1))
		self.snapWidth_nm          = int(json_data['additionalParams'].get('snapWidth_nm', 1))
		self.snapHeight_nm         = int(json_data['additionalParams'].get('snapHeight_nm', 1))
		self.t_setup_ns            = float(json_data['timing'].get('t_setup_ns', 0.050))
		self.t_hold_ns             = float(json_data['timing'].get('t_hold_ns', 0.050))
		self.cap_input_pf          = float(json_data['timing'].get('cap_input_pf', 0.005))	
		self.use_custom_tech	   = bool(json_data.get('use_custom_tech', False))
			
		self.pinPitch_nm = self.y_pinPitch_nm
		
		# Converted values
		self.tech_um               = self.tech_nm / 1000.0
		self.manufacturing_grid_um = self.manufacturing_grid_nm / 1000.0

		self.pinPitch_um           = self.pinPitch_nm / 1000.0
		self.y_pinPitch_um         = self.y_pinPitch_nm / 1000.0
		self.x_pinPitch_um         = self.x_pinPitch_nm / 1000.0
		self.y_pinOffset_um        = self.y_pinOffset_nm / 1000.0
		self.x_pinOffset_um        = self.x_pinOffset_nm / 1000.0
		self.powerGridWidth_um     = self.powerGridWidth_nm / 1000.0
		self.powerGridPitch_um     = self.powerGridPitch_nm / 1000.0
		self.powerGridOffset_um    = self.powerGridOffset_nm / 1000.0

		self.pinWidth_um           = self.pinWidth_nm / 1000.0
		self.pinHeight_um          = self.pinHeight_nm / 1000.0
		self.snapWidth_um		   = self.snapWidth_nm / 1000.0
		self.snapHeight_um		   = self.snapHeight_nm / 1000.0

		# TODO :  From original bsg fakeram
		# self.vlogTimingCheckSignalExpansion = bool(json_data['vlogTimingCheckSignalExpansion']) if 'vlogTimingCheckSignalExpansion' in json_data else False
		# self.metal_track_pitch_um           = self.metal_track_pitch_nm / 1000.0
		# if (self.pin_pitch_nm % self.metal_track_pitch_nm != 0) :  
		#   print("Pin Pitch %d not a multiple of Metal Track Pitch %d" %(self.pin_pitch_nm,self.metal_track_pitch_nm))
		#   sys.exit(1)

		if (self.pinPitch_nm % self.manufacturing_grid_nm != 0) :  
			print("Pin Pitch %d not a multiple of Manufacturing Grid %d" %(self.pinPitch_nm, self.manufacturing_grid_nm))
			sys.exit(1)