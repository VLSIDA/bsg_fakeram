from utils.gen_lef.lef_globals import *

def gen_strapes(mem, lef_p) -> None:

    LEF_file              = lef_p.LEF_file
    manufacturing_grid_um = lef_p.manufacturing_grid_um
    metalLayerPins        = lef_p.metalLayerPins
    min_pin_width         = lef_p.min_pin_width
    flip                  = lef_p.flip
    h                     = lef_p.h
    w                     = lef_p.w

    LEF_file = open(LEF_file, 'a')

    supply_pin_width      = min_pin_width*4
    supply_pin_half_width = snap_to_grid(supply_pin_width/2, manufacturing_grid_um)
    supply_pin_pitch      = snap_to_grid(mem.process.pinPitch_um*8, manufacturing_grid_um)

    """Non-fliped assumes metal1 is vertical therefore
        supply pins on metal4 will be horizontal and signal pins will also be on
        metal4. If set to true, supply pins on metal4 will be vertical and signal
        pins will be on metal3."""
    if flip:
        # Prevent overlapped from VDD/VSS by adding pin width + x_offset
        pw_space = snap_to_grid(mem.process.pinHeight_um + mem.process.pinPitch_um*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space + supply_pin_pitch*2, manufacturing_grid_um)
        LEF_file.write('  PIN VSS\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE GROUND ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s ;\n' % metalLayerPins)

        while x_step <= w - mem.process.pinPitch_um:
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, (mem.process.pinHeight_um*2), x_step+supply_pin_half_width, h-(mem.process.pinHeight_um*2)))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)
    
        LEF_file.write('    END\n')
        LEF_file.write('  END VSS\n')

        pw_space = snap_to_grid(mem.process.pinHeight_um + mem.process.pinPitch_um*2, manufacturing_grid_um)
        x_step = snap_to_grid(pw_space + supply_pin_pitch, manufacturing_grid_um)
        LEF_file.write('  PIN VDD\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE POWER ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s ;\n' % metalLayerPins)

        while x_step <= w - mem.process.pinPitch_um:
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, (mem.process.pinHeight_um*2), x_step+supply_pin_half_width, h-(mem.process.pinHeight_um*2)))
            x_step = snap_to_grid(x_step + supply_pin_pitch*2, manufacturing_grid_um)

        LEF_file.write('    END\n')
        LEF_file.write('  END VDD\n')

    else:
        ph_space = snap_to_grid(mem.process.pinHeight_um + mem.process.pinHeight_um*2, manufacturing_grid_um)
        y_step = snap_to_grid(ph_space + supply_pin_pitch*2, manufacturing_grid_um)
        LEF_file.write('  PIN VSS\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE GROUND ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s ;\n' % metalLayerPins)

        while y_step <= h - mem.process.pinHeight_um:
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((mem.process.pinHeight_um*2), y_step-supply_pin_half_width, w-(mem.process.pinHeight_um*2), y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)

        LEF_file.write('    END\n')
        LEF_file.write('  END VSS\n')

        ph_space = snap_to_grid(mem.process.pinHeight_um + mem.process.pinHeight_um*2, manufacturing_grid_um)
        y_step = snap_to_grid(ph_space + supply_pin_pitch, manufacturing_grid_um)
        LEF_file.write('  PIN VDD\n')
        LEF_file.write('    DIRECTION INOUT ;\n')
        LEF_file.write('    USE POWER ;\n')
        LEF_file.write('    PORT\n')
        LEF_file.write('      LAYER %s ;\n' % metalLayerPins)

        while y_step <= h - mem.process.pinHeight_um:
            LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((mem.process.pinHeight_um*2), y_step-supply_pin_half_width, w-(mem.process.pinHeight_um*2), y_step+supply_pin_half_width))
            y_step = snap_to_grid(y_step + supply_pin_pitch*2, manufacturing_grid_um)
            
        LEF_file.write('    END\n')
        LEF_file.write('  END VDD\n')

    LEF_file.close()