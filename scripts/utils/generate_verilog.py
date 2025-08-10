import os
import math

################################################################################
# GENERATE VERILOG VIEW
#
# Generate a .v file based on the given SRAM.
################################################################################

def generate_verilog( mem ):

    name              = str(mem.name)
    depth             = int(mem.depth)
    bits              = int(mem.width_in_bits)
    addr_width        = math.ceil(math.log2(depth))
    num_rport         = mem.r
    num_wport         = mem.w
    num_rwport        = mem.rw
    num_wmask         = mem.wmask
    write_mode        = mem.write_mode
    has_wmask         = mem.has_write_mask
    write_granularity = mem.write_granularity
    

    V_file = open(os.sep.join([mem.results_dir, name + '.v']), 'w')

    V_file.write('module %s\n' % name)
    V_file.write('(\n')

    ########################################
    # Init IO
    ########################################
    if num_rport > 0:
      write_init_port_names( V_file, num_rport, num_wmask, has_wmask, 'r')
    if num_wport > 0:
      write_init_port_names( V_file, num_wport, num_wmask, has_wmask, 'w')
    if num_rwport > 0:
      write_init_port_names( V_file, num_rwport, num_wmask, has_wmask, 'rw')
  
    V_file.write(');\n')
    V_file.write('   parameter BITS = %s;\n' % str(bits))
    V_file.write('   parameter WORD_DEPTH = %s;\n' % str(depth))
    V_file.write('   parameter ADDR_WIDTH = %s;\n' % str(addr_width))
    V_file.write('   parameter corrupt_mem_on_X_p = 1;\n')
    V_file.write('\n')
    
  
    if num_rport > 0:
      write_ports( V_file, num_rport, num_wmask, has_wmask,'r')
    if num_wport > 0:
      write_ports( V_file, num_wport, num_wmask, has_wmask,'w')
    if num_rwport > 0:
      write_ports( V_file, num_rwport, num_wmask, has_wmask,'rw')
    V_file.write(f'\n'
                 f'   reg    [BITS-1:0]        mem [0:WORD_DEPTH-1];\n'
                 f'   integer j;\n\n')

    ########################################
    # Port Logic
    ########################################
    if num_rport > 0:
      write_logic( V_file, name, num_rport, write_mode, num_wmask, has_wmask, write_granularity, 'r' )
    if num_wport > 0:
      write_logic( V_file, name, num_wport, write_mode, num_wmask, has_wmask, write_granularity, 'w' )
    if num_rwport > 0:
      write_logic( V_file, name, num_rwport, write_mode, num_wmask, has_wmask, write_granularity, 'rw' )
    V_file.write('\n')


    ########################################
    # Timing Checks
    ########################################
    V_file.write(f'   // Timing check placeholders (will be replaced during SDF back-annotation)\n'
                 f'   `ifdef SRAM_TIMING'
                 f'   reg notifier;\n'
                 f'   specify\n')

    if num_rport > 0:
      write_timing_checks( V_file, num_rport, has_wmask, 'r')
    if num_wport > 0:
      write_timing_checks( V_file, num_wport, has_wmask, 'w')
    if num_rwport > 0:
      write_timing_checks( V_file, num_rwport, has_wmask, 'rw')
    V_file.write(f'   endspecify\n'
                 f'   `endif\n'
                 f'\n'
                 f'endmodule\n')

    V_file.close()

################################################################################
# GENERATE VERILOG BLACKBOX VIEW
#
# Generate a .bb.v file based on the given SRAM. This is the same as the
# standard verilog view but only has the module definition and port
# declarations (no internal logic).
################################################################################

def generate_verilog_bb( mem ):

    name       = str(mem.name)
    depth      = int(mem.depth)
    bits       = int(mem.width_in_bits)
    num_rport  = mem.r
    num_wport  = mem.w
    num_rwport = mem.rw
    write_mode = mem.write_mode
    addr_width = math.ceil(math.log2(depth))
    num_wmask  = mem.wmask
    has_wmask  = mem.has_write_mask


    V_file = open(os.sep.join([mem.results_dir, name + '.bb.v']), 'w')

    V_file.write('module %s\n' % name)
    V_file.write('(\n')

    ########################################
    # Init IO
    ########################################
    if num_rport > 0:
      write_init_port_names( V_file, num_rport, num_wmask, has_wmask, 'r' )
    if num_wport > 0:
      write_init_port_names( V_file, num_wport, num_wmask, has_wmask, 'w' )
    if num_rwport > 0:
      write_init_port_names( V_file, num_rwport, num_wmask, has_wmask,'rw' )

    V_file.write(');\n')
    V_file.write('   parameter BITS = %s;\n' % str(bits))
    V_file.write('   parameter WORD_DEPTH = %s;\n' % str(depth))
    V_file.write('   parameter ADDR_WIDTH = %s;\n' % str(addr_width))
    V_file.write('   parameter corrupt_mem_on_X_p = 1;\n')
    V_file.write('\n')

    if num_rport > 0:
      write_ports( V_file, num_rport, num_wmask, has_wmask, 'r')
    if num_wport > 0:
      write_ports( V_file, num_wport, num_wmask, has_wmask, 'w')
    if num_rwport > 0:
      write_ports( V_file, num_rwport, num_wmask, has_wmask, 'rw')

    V_file.write('\n')
    V_file.write('endmodule\n')
    V_file.close()

########################################
# Helper functions
########################################

def write_init_port_names( V_file, num_port, num_wmask, has_wmask, type_port) -> None:
    for i in range(int(num_port)):
      if type_port in ('w', 'rw'):
        V_file.write(f'   {type_port}{i}_wd_in,\n'
                     f'   {type_port}{i}_we_in,\n')
        if has_wmask:
           V_file.write(f'   {type_port}{i}_wmask_in,\n')
    
      if type_port in ('r', 'rw'):
        V_file.write(f'   {type_port}{i}_rd_out,\n')

      V_file.write(f'   {type_port}{i}_clk,\n'
                   f'   {type_port}{i}_ce_in,\n'
                   f'   {type_port}{i}_addr_in,\n')


def write_ports( V_file, num_port, num_wmask, has_wmask, type_port) -> None:
    for i in range(num_port):
      V_file.write(f'   input                    {type_port}{i}_clk;\n'
                   f'   input                    {type_port}{i}_ce_in;\n'
                   f'   input  [ADDR_WIDTH-1:0]  {type_port}{i}_addr_in;\n')
      
      if type_port in ('r', 'rw'):
        V_file.write(f'   output reg [BITS-1:0]    {type_port}{i}_rd_out;\n')

      if type_port in ('w', 'rw'):
        V_file.write(f'   input                    {type_port}{i}_we_in;\n'
                     f'   input  [BITS-1:0]        {type_port}{i}_wd_in;\n')
        if has_wmask:
          V_file.write(f'   input  [{num_wmask-1}:0]             {type_port}{i}_wmask_in;\n')

def write_logic( V_file, name, num_port, write_mode, num_wmask, has_wmask, write_granularity, type_port):
  for i in range(int(num_port)):
    V_file.write(f'   always @(posedge {type_port}{i}_clk) begin\n'
                 f'      if ({type_port}{i}_ce_in) begin\n')
    # Read Logic (read_first)
    if type_port in ('r', 'rw') and write_mode == 'read_first':
        V_file.write(f'         // Read-first\n'
                     f'         {type_port}{i}_rd_out <= mem[{type_port}{i}_addr_in];\n')
    # Write Logic
    if type_port in ('w', 'rw'):
        V_file.write(
                    #  f"         //if (({type_port}{i}_we_in !== 1'b1 && {type_port}{i}_we_in !== 1'b0) && corrupt_mem_on_X_p)\n"
                     f"         // Write Port\n"
                     f"         if (corrupt_mem_on_X_p &&\n"
                     f"             ((^{type_port}{i}_we_in === 1'bx) || (^{type_port}{i}_addr_in === 1'bx))) begin\n"
                     f"            // WEN or ADDR is unknown, so corrupt entire array (using unsynthesizeable for loop)\n"
                     f"            for (j = 0; j < WORD_DEPTH; j = j + 1) begin\n"
                     f"               mem[j] <= 'x;\n"
                     f'            end\n'
                     f'            $display("warning: {type_port}{i}_ce_in=1, {type_port}{i}_we_in is %b, '
                     f'{type_port}{i}_addr_in = %x in {name}", {type_port}{i}_we_in, {type_port}{i}_addr_in);\n'
                     f"         end\n"
                     f"         else if ({type_port}{i}_we_in) begin \n")
        if has_wmask:
            for j in range(num_wmask):
              V_file.write(f"            if ({type_port}{i}_wmask_in[{j}])\n")
              V_file.write(f"               mem[{type_port}{i}_addr_in][{(j+1)*write_granularity-1}:{j*write_granularity}] <= ({type_port}{i}_wd_in[{(j+1)*write_granularity-1}:{j*write_granularity}]);\n")
        else:
              V_file.write(f"            mem[{type_port}{i}_addr_in] <= {type_port}{i}_wd_in;\n")
            
        V_file.write(f"         end\n")
    
    # Read Logic (write_first)
    if type_port in ('r', 'rw') and write_mode == 'write_first':
        V_file.write(f'         // Read Port\n'
                     f'         {type_port}{i}_rd_out <= mem[{type_port}{i}_addr_in];\n')
    V_file.write(f'      end\n')
    # Read Corruption Logic
    if type_port in ('r', 'rw'):
      V_file.write(f'      else begin\n'
                   f'         // Make sure read fails if {type_port}{i}_ce_in is low\n'
                   f"         {type_port}{i}_rd_out <= 'x;\n"
                   f'      end\n')
    V_file.write(f'   end\n')
    V_file.write(f'\n')

def write_timing_checks( V_file, num_port, has_wmask, type_port) -> None:
    for i in range(num_port):
      V_file.write(f'      (posedge {type_port}{i}_clk *> {type_port}{i}_rd_out) = (0, 0);\n')
    # V_file.write('\n')
    # V_file.write('      // Timing checks\n')

    for i in range(num_port):
      V_file.write(f'      $width     (posedge {type_port}{i}_clk,            0, 0, notifier);\n'
                   f'      $width     (negedge {type_port}{i}_clk,            0, 0, notifier);\n'
                   f'      $period    (posedge {type_port}{i}_clk,            0,    notifier);\n')
  
      if type_port in ('w','rw'):
        V_file.write(f'      $setuphold (posedge {type_port}{i}_clk, {type_port}{i}_we_in,     0, 0, notifier);\n'
                     f'      $setuphold (posedge {type_port}{i}_clk, {type_port}{i}_wd_in,     0, 0, notifier);\n')
        if has_wmask:
          V_file.write(f'      $setuphold (posedge {type_port}{i}_clk, {type_port}{i}_wmask_in,     0, 0, notifier);\n')


      V_file.write(f'      $setuphold (posedge {type_port}{i}_clk, {type_port}{i}_ce_in,     0, 0, notifier);\n'
                   f'      $setuphold (posedge {type_port}{i}_clk, {type_port}{i}_addr_in,   0, 0, notifier);\n'
                   f'\n')
