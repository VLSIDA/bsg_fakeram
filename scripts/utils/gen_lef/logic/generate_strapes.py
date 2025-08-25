from utils.gen_lef.lef_globals import *

def gen_strapes(lef_p) -> None:

    LEF_file              = lef_p.LEF_file
    manufacturing_grid_um = lef_p.manufacturing_grid_um
    metLayerPowerGrid     = lef_p.metLayerPowerGrid
    metal_prefix          = lef_p.metal_prefix
    min_pin_width         = lef_p.min_pin_width
    directionPowerGrid    = lef_p.directionPowerGrid
    h                     = lef_p.h
    w                     = lef_p.w
    unscaled_pin_pitch    = lef_p.unscaled_y_pin_pitch
    pin_height            = lef_p.pin_height

    LEF_file = open(LEF_file, 'a')

    supply_pin_width      = min_pin_width*4
    supply_pin_half_width = snap_to_grid(supply_pin_width/2, manufacturing_grid_um)
    supply_pin_pitch      = snap_to_grid(unscaled_pin_pitch*8, manufacturing_grid_um)

    """Non-fliped assumes metal1 is vertical therefore
        supply pins on metal4 will be horizontal and signal pins will also be on
        metal4. If set to true, supply pins on metal4 will be vertical and signal
        pins will be on metal3."""
    if directionPowerGrid == 'vertical':
        # Prevent overlapped from VDD/VSS by adding pin width + x_offset
        pw_space = snap_to_grid(pin_height + unscaled_pin_pitch*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space + supply_pin_pitch*2, manufacturing_grid_um)
        LEF_file.write('  PIN VSS\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE GROUND ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s%s ;\n' % (metal_prefix,metLayerPowerGrid))

        while x_step <= w - unscaled_pin_pitch - (unscaled_pin_pitch*2):
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, (pin_height*2), x_step+supply_pin_half_width, h-(pin_height*2)))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)
    
        LEF_file.write('    END\n')
        LEF_file.write('  END VSS\n')

        pw_space = snap_to_grid(pin_height + unscaled_pin_pitch*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space + supply_pin_pitch, manufacturing_grid_um)
        LEF_file.write('  PIN VDD\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE POWER ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s%s ;\n' % (metal_prefix,metLayerPowerGrid))

        while x_step <= w - unscaled_pin_pitch - (unscaled_pin_pitch*2):
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, (pin_height*2), x_step+supply_pin_half_width, h-(pin_height*2)))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)

        LEF_file.write('    END\n')
        LEF_file.write('  END VDD\n')

    else:
        ph_space = snap_to_grid(pin_height + pin_height*2, manufacturing_grid_um)
        y_step = snap_to_grid(ph_space + supply_pin_pitch*2, manufacturing_grid_um)
        LEF_file.write('  PIN VSS\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE GROUND ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s%s ;\n' % (metal_prefix,metLayerPowerGrid))

        while y_step <= h - pin_height - (unscaled_pin_pitch*2):
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((pin_height*2), y_step-supply_pin_half_width, w-(pin_height*2), y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)

        LEF_file.write('    END\n')
        LEF_file.write('  END VSS\n')

        ph_space = snap_to_grid(pin_height + pin_height*2, manufacturing_grid_um)
        y_step = snap_to_grid(ph_space + supply_pin_pitch, manufacturing_grid_um)
        LEF_file.write('  PIN VDD\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE POWER ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s%s ;\n' % (metal_prefix,metLayerPowerGrid))

        while y_step <= h - pin_height - (unscaled_pin_pitch*2):
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((pin_height*2), y_step-supply_pin_half_width, w-(pin_height*2), y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)
            
        LEF_file.write('    END\n')
        LEF_file.write('  END VDD\n')

    LEF_file.close()