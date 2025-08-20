import os
import math
import time
import datetime

################################################################################
# GENERATE LIBERTY VIEW
#
# Generate a .lib file based on the given SRAM.
################################################################################

def generate_lib( mem ):

    # Make sure the data types are correct
    name              = str(mem.name)
    depth             = int(mem.depth)
    bits              = int(mem.width_in_bits)
    area              = float(mem.area_um2)
    x                 = float(mem.width_um)
    y                 = float(mem.height_um)
    leakage           = float(mem.standby_leakage_per_bank_mW)*1e3
    tsetup            = float(mem.t_setup_ns)
    thold             = float(mem.t_hold_ns)
    tcq               = float(mem.access_time_ns)
    clkpindynamic     = float(mem.pin_dynamic_power_mW)*1e3
    pindynamic        = float(mem.pin_dynamic_power_mW)*1e1
    min_driver_in_cap = float(mem.cap_input_pf)
    voltage           = float(mem.process.voltage)
    min_period        = float(mem.cycle_time_ns)
    fo4               = float(mem.fo4_ps)/1e3

    # Dynamic Ports
    num_rport = mem.r
    num_wport = mem.w  
    num_rwport = mem.rw
    # num_wmask = mem.wmask
    has_wmask = mem.has_write_mask

    # Number of bits for address
    addr_width    = math.ceil(math.log2(mem.depth))
    addr_width_m1 = addr_width-1

    # Get the date
    d = datetime.date.today()
    date = d.isoformat()
    current_time = time.strftime("%H:%M:%SZ", time.gmtime())

    # TODO: Arbitrary indicies for the NLDM table. This is used for Clk->Q arcs
    # as well as setup/hold times. We only have a single value for these, there
    # are two options. 1. adding some sort of static variation of the single
    # value for each table entry, 2. use the same value so all interpolated
    # values are the same. The 1st is more realistic but depend on good variation
    # values which is process sepcific and I don't have a strategy for
    # determining decent variation values without breaking NDA so right now we
    # have no variations.
    #
    # The table indicies are main min/max values for interpolation. The tools
    # typically don't like extrapolation so a large range is nice, but makes the
    # single value strategy described above even more unrealistic.
    #
    min_slew = 1   * fo4               ;# arbitrary (1x fo4, fear that 0 would cause issues)
    max_slew = 25  * fo4               ;# arbitrary (25x fo4 as ~100x fanout ... i know that is not really how it works)
    min_load = 1   * min_driver_in_cap ;# arbitrary (1x driver, fear that 0 would cause issues)
    max_load = 100 * min_driver_in_cap ;# arbitrary (100x driver)

    slew_indicies = '%.3f, %.3f' % (min_slew, max_slew) ;# input pin transisiton with between 1xfo4 and 100xfo4
    load_indicies = '%.3f, %.3f' % (min_load, max_load) ;# output capacitance table between a 1x and 32x inverter

    # Start generating the LIB file

    LIB_file = open(os.sep.join([mem.results_dir, name + '.lib']), 'w')

    write_init_lib(LIB_file, name, voltage, date, current_time, bits, area, max_slew, addr_width, addr_width_m1)

    if num_rport > 0:
      write_clk_ports(LIB_file, num_rport, 'r', name, slew_indicies, min_driver_in_cap, clkpindynamic, min_period)

      write_lib_ports(LIB_file, num_rport, 'r', name, max_load, slew_indicies, load_indicies, tcq, \
                      min_slew, max_slew, min_driver_in_cap, tsetup, thold, pindynamic)

    if num_wport > 0:
      write_clk_ports(LIB_file, num_wport, 'w', name, slew_indicies, min_driver_in_cap, clkpindynamic, min_period)

      write_lib_ports(LIB_file, num_wport, 'w', name, max_load, slew_indicies, load_indicies, tcq, \
                      min_slew, max_slew, min_driver_in_cap, tsetup, thold, pindynamic)
      if has_wmask:
        write_lib_wmask(LIB_file, num_wport, 'w', name, slew_indicies, min_driver_in_cap, tsetup, thold, pindynamic)

    if num_rwport > 0:
      write_clk_ports(LIB_file, num_rwport, 'rw', name, slew_indicies, min_driver_in_cap, clkpindynamic, min_period)
  
      write_lib_ports(LIB_file, num_rwport, 'rw', name, max_load, slew_indicies, load_indicies, tcq, \
                      min_slew, max_slew, min_driver_in_cap, tsetup, thold, pindynamic)
      if has_wmask:
        write_lib_wmask(LIB_file, num_rwport, 'rw', name, slew_indicies, min_driver_in_cap, tsetup, thold, pindynamic)

    
    LIB_file.write('    cell_leakage_power : %.3f;\n' % (leakage))
    LIB_file.write('}\n')

    LIB_file.write('\n')
    LIB_file.write('}\n')

    LIB_file.close()

########################################
# Helper functions
########################################

def write_init_lib(LIB_file, name, voltage, date, current_time, bits, area, max_slew, addr_width, addr_width_m1) -> None:

    LIB_file.write(f'library({name}) {{\n'
                   f'    technology (cmos);\n'
                   f'    delay_model : table_lookup;\n'
                   f'    revision : 1.0;\n'
                   f'    date : "{date} {current_time}";\n'
                   f'    comment : "SRAM";\n'
                   f'    time_unit : "1ns";\n'
                   f'    voltage_unit : "1V";\n'
                   f'    current_unit : "1uA";\n'
                   f'    leakage_power_unit : "1uW";\n'
                   f'    nom_process : 1;\n'
                   f'    nom_temperature : 25.000;\n'
                   f'    nom_voltage : {voltage};\n'
                   f'    capacitive_load_unit (1,pf);\n\n'
                   f'    pulling_resistance_unit : "1kohm";\n\n'
                   f'    operating_conditions(tt_1.0_25.0) {{\n'
                   f'        process : 1;\n'
                   f'        temperature : 25.000;\n'
                   f'        voltage : {voltage};\n'
                   f'        tree_type : balanced_tree;\n'
                   f'    }}\n'
                   f'\n')

    LIB_file.write( f'    /* default attributes */\n'
                    f'    default_cell_leakage_power : 0;\n'
                    f'    default_fanout_load : 1;\n'
                    f'    default_inout_pin_cap : 0.0;\n'
                    f'    default_input_pin_cap : 0.0;\n'
                    f'    default_output_pin_cap : 0.0;\n'
                    f'    default_input_pin_cap : 0.0;\n'
                    f'    default_max_transition : {max_slew:.3f};\n\n'
                    f'    default_operating_conditions : tt_1.0_25.0;\n'
                    f'    default_leakage_power_density : 0.0;\n'
                    f'\n')

    LIB_file.write( f'    /* additional header data */\n'
                    f'    slew_derate_from_library : 1.000;\n'
                    f'    slew_lower_threshold_pct_fall : 20.000;\n'
                    f'    slew_upper_threshold_pct_fall : 80.000;\n'
                    f'    slew_lower_threshold_pct_rise : 20.000;\n'
                    f'    slew_upper_threshold_pct_rise : 80.000;\n'
                    f'    input_threshold_pct_fall : 50.000;\n'
                    f'    input_threshold_pct_rise : 50.000;\n'
                    f'    output_threshold_pct_fall : 50.000;\n'
                    f'    output_threshold_pct_rise : 50.000;\n\n'
                    f'\n'
                    f'    lu_table_template({name}_mem_out_delay_template) {{\n' 
                    f'        variable_1 : input_net_transition;\n'
                    f'        variable_2 : total_output_net_capacitance;\n'
                    f'            index_1 ("1000, 1001");\n'
                    f'            index_2 ("1000, 1001");\n'
                    f'    }}\n'
                    f'    lu_table_template({name}_mem_out_slew_template) {{\n' 
                    f'        variable_1 : total_output_net_capacitance;\n'
                    f'            index_1 ("1000, 1001");\n'
                    f'    }}\n'
                    f'    lu_table_template({name}_constraint_template) {{\n' 
                    f'        variable_1 : related_pin_transition;\n'
                    f'        variable_2 : constrained_pin_transition;\n'
                    f'            index_1 ("1000, 1001");\n'
                    f'            index_2 ("1000, 1001");\n'
                    f'    }}\n'
                    f'    power_lut_template({name}_energy_template_clkslew) {{\n' 
                    f'        variable_1 : input_transition_time;\n'
                    f'            index_1 ("1000, 1001");\n'
                    f'    }}\n'
                    f'    power_lut_template({name}_energy_template_sigslew) {{\n' 
                    f'        variable_1 : input_transition_time;\n'
                    f'            index_1 ("1000, 1001");\n'
                    f'    }}\n'
                    f'    library_features(report_delay_calculation);\n'
                    f'    type ({name}_DATA) {{\n' 
                    f'        base_type : array ;\n'
                    f'        data_type : bit ;\n'
                    f'        bit_width : {bits};\n'
                    f'        bit_from : {int(bits)-1};\n'
                    f'        bit_to : 0 ;\n'
                    f'        downto : true ;\n'
                    f'    }}\n'
                    f'    type ({name}_ADDRESS) {{\n'
                    f'        base_type : array ;\n'
                    f'        data_type : bit ;\n'
                    f'        bit_width : {addr_width};\n'
                    f'        bit_from : {addr_width_m1};\n'
                    f'        bit_to : 0 ;\n'
                    f'        downto : true ;\n'
                    f'    }}\n')
    
    LIB_file.write( f'   cell({name}) {{\n'
                    f'       area : {area:.3f};\n'
                   #f'       dont_use : true;\n'
                   #f'       dont_touch : true;\n'
                    f'       interface_timing : true;\n'
                    f'       memory() {{\n'
                    f'           type : ram;\n'
                    f'           address_width : {addr_width};\n'
                    f'           word_width : {bits};\n'
                    f'    }}\n')
    

def write_lib_ports(LIB_file, num_port, type_port, name, max_load, slew_indicies, load_indicies, tcq, min_slew, max_slew, min_driver_in_cap, tsetup, thold, pindynamic) -> None:
    if type_port in ('r', 'rw'):
      for i in range(num_port) :
        LIB_file.write(f'    bus({type_port}{i}_rd_out)   {{\n'
                      f'        bus_type : {name}_DATA;\n'
                      f'        direction : output;\n'
                      f'        max_capacitance : {max_load:.3f};\n' # Based on 32x inverter being a common max (or near max) inverter
                      f'        memory_read() {{\n'
                      f'            address : {type_port}{i}_addr_in;\n'
                      f'        }}\n'
                      f'        timing() {{\n'
                      f'            related_pin : "{type_port}{i}_clk" ;\n'
                      f'            timing_type : rising_edge;\n'
                      f'            timing_sense : non_unate;\n'
                      f'            cell_rise({name}_mem_out_delay_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{load_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{tcq:.3f}, {tcq:.3f}", \\\n'
                      f'                  "{tcq:.3f}, {tcq:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'            cell_fall({name}_mem_out_delay_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{load_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{tcq:.3f}, {tcq:.3f}", \\\n'
                      f'                  "{tcq:.3f}, {tcq:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'            rise_transition({name}_mem_out_slew_template) {{\n'
                      f'                index_1 ("{load_indicies}");\n'
                      f'                values ("{min_slew:.3f}, {max_slew:.3f}")\n'
                      f'            }}\n'
                      f'            fall_transition({name}_mem_out_slew_template) {{\n'
                      f'                index_1 ("{load_indicies}");\n'
                      f'                values ("{min_slew:.3f}, {max_slew:.3f}")\n'
                      f'            }}\n'
                      f'        }}\n'
                      f'    }}\n')

    if type_port in ('w','rw'):
      for i in range(num_port) :
        LIB_file.write(f'    pin({type_port}{i}_we_in){{\n'
                      f'        direction : input;\n'
                      f'        capacitance : {min_driver_in_cap:.3f};\n'
                      f'        timing() {{\n'
                      f'            related_pin : "{type_port}{i}_clk";\n'
                      f'            timing_type : setup_rising ;\n'
                      f'            rise_constraint({name}_constraint_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{slew_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                      f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'            fall_constraint({name}_constraint_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{slew_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                      f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'        }} \n'
                      f'        timing() {{\n'
                      f'            related_pin : "{type_port}{i}_clk";\n'
                      f'            timing_type : hold_rising ;\n'
                      f'            rise_constraint({name}_constraint_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{slew_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                      f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'            fall_constraint({name}_constraint_template) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                index_2 ("{slew_indicies}");\n'
                      f'                values ( \\\n'
                      f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                      f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                      f'                )\n'
                      f'            }}\n'
                      f'        }}\n'
                      f'        internal_power(){{\n'
                      f'            rise_power({name}_energy_template_sigslew) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                      f'            }}\n'
                      f'            fall_power({name}_energy_template_sigslew) {{\n'
                      f'                index_1 ("{slew_indicies}");\n'
                      f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                      f'            }}\n'
                      f'        }}\n'
                      f'    }}\n')
        
      for i in range(num_port) :
        LIB_file.write(f'    bus({type_port}{i}_wd_in)   {{\n'
                       f'        bus_type : {name}_DATA;\n'
                       f'        memory_write() {{\n'
                       f'            address : {type_port}{i}_addr_in;\n'
                       f'            clocked_on : "{type_port}{i}_clk";\n'
                       f'        }}\n'
                       f'        direction : input;\n'
                       f'        capacitance : {min_driver_in_cap:.3f};\n'
                       f'        timing() {{\n'
                       f'            related_pin     : "{type_port}{i}_clk";\n'
                       f'            timing_type     : setup_rising ;\n'
                       f'            rise_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n' 
                       f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'  
                       f'                )\n'
                       f'            }}\n'
                       f'            fall_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n' 
                       f'                )\n'
                       f'            }}\n'
                       f'        }} \n'
                       f'        timing() {{\n'
                       f'            related_pin     : "{type_port}{i}_clk";\n'
                       f'            timing_type     : hold_rising ;\n'
                       f'            rise_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'            fall_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'        internal_power(){{\n'
                       f'            when : "(! ({type_port}{i}_we_in) )";\n'
                       f'            rise_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'            fall_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'        internal_power(){{\n'
                       f'            when : "({type_port}{i}_we_in)";\n'
                       f'            rise_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'            fall_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'    }}\n')


    for i in range(num_port):
      LIB_file.write(f'    pin({type_port}{i}_ce_in){{\n'
                    f'        direction : input;\n'
                    f'        capacitance : {min_driver_in_cap:.3f};\n'
                    f'        timing() {{\n'
                    f'            related_pin : "{type_port}{i}_clk";\n'
                    f'            timing_type : setup_rising ;\n'
                    f'            rise_constraint({name}_constraint_template) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                index_2 ("{slew_indicies}");\n'
                    f'                values ( \\\n'
                    f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                    f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                    f'                )\n'
                    f'            }}\n'
                    f'            fall_constraint({name}_constraint_template) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                index_2 ("{slew_indicies}");\n'
                    f'                values ( \\\n'
                    f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                    f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                    f'                )\n'
                    f'            }}\n'
                    f'        }} \n'
                    f'        timing() {{\n'
                    f'            related_pin : "{type_port}{i}_clk";\n'
                    f'            timing_type : hold_rising ;\n'
                    f'            rise_constraint({name}_constraint_template) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                index_2 ("{slew_indicies}");\n'
                    f'                values ( \\\n'
                    f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                    f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                    f'                )\n'
                    f'            }}\n'
                    f'            fall_constraint({name}_constraint_template) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                index_2 ("{slew_indicies}");\n'
                    f'                values ( \\\n'
                    f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                    f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                    f'                )\n'
                    f'            }}\n'
                    f'        }}\n'
                    f'        internal_power(){{\n'
                    f'            rise_power({name}_energy_template_sigslew) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                    f'            }}\n'
                    f'            fall_power({name}_energy_template_sigslew) {{\n'
                    f'                index_1 ("{slew_indicies}");\n'
                    f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                    f'            }}\n'
                    f'        }}\n'
                    f'    }}\n')

    for i in range(num_port) :
      LIB_file.write(f'    bus({type_port}{i}_addr_in)   {{\n'
                     f'        bus_type : {name}_ADDRESS;\n'
                     f'        direction : input;\n'
                     f'        capacitance : {min_driver_in_cap:.3f};\n'
                     f'        timing() {{\n'
                     f'            related_pin : "{type_port}{i}_clk";\n'
                     f'            timing_type : setup_rising ;\n'
                     f'            rise_constraint({name}_constraint_template) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                index_2 ("{slew_indicies}");\n'
                     f'                values ( \\\n'
                     f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                     f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                     f'                )\n'
                     f'            }}\n'
                     f'            fall_constraint({name}_constraint_template) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                index_2 ("{slew_indicies}");\n'
                     f'                values ( \\\n'
                     f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                     f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                     f'                )\n'
                     f'            }}\n'
                     f'        }} \n'
                     f'        timing() {{\n'
                     f'            related_pin : "{type_port}{i}_clk";\n'
                     f'            timing_type : hold_rising ;\n'
                     f'            rise_constraint({name}_constraint_template) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                index_2 ("{slew_indicies}");\n'
                     f'                values ( \\\n'
                     f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                     f'                  "{thold:.3f}, {thold:.3f}" \\\n' 
                     f'                )\n'
                     f'            }}\n'
                     f'            fall_constraint({name}_constraint_template) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                index_2 ("{slew_indicies}");\n'
                     f'                values ( \\\n'
                     f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                     f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                     f'                )\n'
                     f'            }}\n'
                     f'        }}\n'
                     f'        internal_power(){{\n'
                     f'            rise_power({name}_energy_template_sigslew) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                     f'            }}\n'
                     f'            fall_power({name}_energy_template_sigslew) {{\n'
                     f'                index_1 ("{slew_indicies}");\n'
                     f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                     f'            }}\n'
                     f'        }}\n'
                     f'    }}\n')
      
def write_clk_ports(LIB_file, num_port, type_port, name, slew_indicies, min_driver_in_cap, clkpindynamic, min_period) -> None:
      for i in range(num_port):
        LIB_file.write( f'    pin({type_port}{i}_clk)   {{\n'
                        f'        direction : input;\n'
                        f'        capacitance : {min_driver_in_cap*5:.3f};\n' # Clk pin is usually higher cap for fanout control, assuming an x5 driver.
                        f'        clock : true;\n'
                      #f'        max_transition : 0.01;\n') # Max rise/fall time
                      #f'        min_pulse_width_high : {min_period:.3f} ;\n'
                      #f'        min_pulse_width_low  : {min_period:.3f} ;\n'
                        f'        min_period           : {min_period:.3f} ;\n'
                      #f'        minimum_period(){\n'
                      #f'            constraint : %.3f ;\n' % min_period
                      #f'            when : "1";\n'
                      #f'            sdf_cond : "1";\n'
                      #f'        }\n'
                        f'        internal_power(){{\n'
                        f'            rise_power({name}_energy_template_clkslew) {{\n'
                        f'                index_1 ("{slew_indicies}");\n'
                        f'                values ("{clkpindynamic:.3f}, {clkpindynamic:.3f}")\n'
                        f'            }}\n'
                        f'            fall_power({name}_energy_template_clkslew) {{\n'
                        f'                index_1 ("{slew_indicies}");\n'
                        f'                values ("{clkpindynamic:.3f}, {clkpindynamic:.3f}")\n'
                        f'            }}\n'
                        f'        }}\n'
                        f'    }}\n'
                        f'\n')

def write_lib_wmask(LIB_file, num_port, type_port, name, slew_indicies, min_driver_in_cap, tsetup, thold, pindynamic) -> None:
      for i in range(int(num_port)) :
        LIB_file.write(f'    bus({type_port}{i}_wmask_in)   {{\n'
                       f'        bus_type : {name}_DATA;\n'
                       f'        memory_write() {{\n'
                       f'            address : {type_port}{i}_addr_in;\n'
                       f'            clocked_on : "{type_port}{i}_clk";\n'
                       f'        }}\n'
                       f'        direction : input;\n'
                       f'        capacitance : {min_driver_in_cap:.3f};\n'
                       f'        timing() {{\n'
                       f'            related_pin     : {type_port}{i}_clk;\n'
                       f'            timing_type     : setup_rising ;\n'
                       f'            rise_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'            fall_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}", \\\n'
                       f'                  "{tsetup:.3f}, {tsetup:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'        }} \n'
                       f'        timing() {{\n'
                       f'            related_pin     : {type_port}{i}_clk;\n'
                       f'            timing_type     : hold_rising ;\n'
                       f'            rise_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'            fall_constraint({name}_constraint_template) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                index_2 ("{slew_indicies}");\n'
                       f'                values ( \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}", \\\n'
                       f'                  "{thold:.3f}, {thold:.3f}" \\\n'
                       f'                )\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'        internal_power(){{\n'
                       f'            when : "(! ({type_port}{i}_we_in) )";\n'
                       f'            rise_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'            fall_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'        internal_power(){{\n'
                       f'            when : "({type_port}{i}_we_in)";\n'
                       f'            rise_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'            fall_power({name}_energy_template_sigslew) {{\n'
                       f'                index_1 ("{slew_indicies}");\n'
                       f'                values ("{pindynamic:.3f}, {pindynamic:.3f}")\n'
                       f'            }}\n'
                       f'        }}\n'
                       f'    }}\n')

