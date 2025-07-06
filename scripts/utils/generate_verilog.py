import os
import math

################################################################################
# GENERATE VERILOG VIEW - ACCURATE TO SPECIALIZED LOGIC
#
# Generate a .v file based on the given SRAM matching the exact interface
# used in the specialized logic examples.
################################################################################

def generate_verilog(mem, tmChkExpand=False):
  '''Generate a verilog view for the RAM'''
  name  = str(mem.name)
  depth = int(mem.depth)
  bits  = int(mem.width_in_bits)
  addr_width = math.ceil(math.log2(depth))
  
  # Check configuration
  has_rport = hasattr(mem, 'r_ports') and mem.r_ports > 0
  has_byte_write = hasattr(mem, 'write_granularity') and mem.write_granularity == 8
  num_bytes = bits // 8 if has_byte_write else 0
  write_mode = mem.write_mode if hasattr(mem, 'write_mode') else 'write_first'

  # Generate the 'setuphold' timing checks for the specialized interface
  setuphold_checks = ''
  if tmChkExpand: # per-bit checks
    setuphold_checks += '      $setuphold (posedge clk0, csb0, 0, 0, notifier);\n'
    setuphold_checks += '      $setuphold (posedge clk0, web0, 0, 0, notifier);\n'
    for i in range(addr_width): 
      setuphold_checks += f'      $setuphold (posedge clk0, addr0[{i}], 0, 0, notifier);\n'
    for i in range(bits): 
      setuphold_checks += f'      $setuphold (posedge clk0, din0[{i}], 0, 0, notifier);\n'
    if has_byte_write:
      for i in range(num_bytes): 
        setuphold_checks += f'      $setuphold (posedge clk0, wmask0[{i}], 0, 0, notifier);\n'
    if has_rport:
      setuphold_checks += '      $setuphold (posedge clk1, csb1, 0, 0, notifier);\n'
      for i in range(addr_width): 
        setuphold_checks += f'      $setuphold (posedge clk1, addr1[{i}], 0, 0, notifier);\n'
  else: # per-signal checks
    setuphold_checks += '      $setuphold (posedge clk0, csb0, 0, 0, notifier);\n'
    setuphold_checks += '      $setuphold (posedge clk0, web0, 0, 0, notifier);\n'
    setuphold_checks += '      $setuphold (posedge clk0, addr0, 0, 0, notifier);\n'
    setuphold_checks += '      $setuphold (posedge clk0, din0, 0, 0, notifier);\n'
    if has_byte_write:
      setuphold_checks += '      $setuphold (posedge clk0, wmask0, 0, 0, notifier);\n'
    if has_rport:
      setuphold_checks += '      $setuphold (posedge clk1, csb1, 0, 0, notifier);\n'
      setuphold_checks += '      $setuphold (posedge clk1, addr1, 0, 0, notifier);\n'

  fout = os.sep.join([mem.results_dir, name + '.v'])
  with open(fout, 'w') as f:
    if has_rport:
      # Prepare byte-write parameters
      if has_byte_write:
        byte_write_port = f'    wmask0,\n'
        byte_write_decl = f'   input  [{num_bytes-1}:0]    wmask0;\n'
        byte_write_logic = generate_byte_write_logic(True, num_bytes)
        num_bytes_param = f'   parameter NUM_BYTES = {num_bytes};\n'
      else:
        byte_write_port = ''
        byte_write_decl = ''
        byte_write_logic = 'mem[addr0] <= din0;'
        num_bytes_param = ''
      
      # Generate RW port logic based on write mode
      rw_port_logic = generate_rw_port_logic(write_mode, has_byte_write)
      # Replace the byte_write_logic placeholder in the RW port logic
      rw_port_logic = rw_port_logic.format(byte_write_logic=byte_write_logic,
                                             data_width=bits,
                                             BITS=bits,
                                             ADDR_WIDTH=addr_width)
      
      f.write(VLOG_SPECIALIZED_1RW1R_TEMPLATE.format(
        name=name, 
        data_width=bits, 
        depth=depth, 
        addr_width=addr_width,
        setuphold_checks=setuphold_checks,
        byte_write_port=byte_write_port,
        byte_write_decl=byte_write_decl,
        byte_write_logic=byte_write_logic,
        num_bytes_param=num_bytes_param,
        rw_port_logic=rw_port_logic,
        write_mode_comment=f'// Write mode: {write_mode}'
      ))
    else:
      # For 1RW only (though not used in specialized logic examples)
      write_mode = mem.write_mode if hasattr(mem, 'write_mode') else 'write_first'
      # Generate RW port logic for 1RW case
      rw_port_logic_1rw = generate_rw_port_logic_1rw(write_mode)
      
      f.write(VLOG_SPECIALIZED_1RW_TEMPLATE.format(
        name=name, 
        data_width=bits, 
        depth=depth, 
        addr_width=addr_width,
        setuphold_checks=setuphold_checks,
        rw_port_logic=rw_port_logic_1rw,
        write_mode_comment=f'// Write mode: {write_mode}'
      ))

def generate_rw_port_logic(write_mode, has_byte_write):
  '''Generate the RW port logic based on write mode'''
  if write_mode == 'write_first':
    # Write-first: register address, read from registered address
    return '''   // Port 0: Read-Write Port with Write-First behavior
   reg [ADDR_WIDTH-1:0] addr0_reg;
   
   always @(posedge clk0) begin
      if (!csb0 && !web0) begin  // Active low chip select
         if (BITS == {data_width}) begin  // Active low write enable - writing when web0=0
            {byte_write_logic}
         end
         // Always register the address (for write-first behavior)
         addr0_reg <= addr0;
      end
   end
   
   // Write-first read: output data from registered address
   assign dout0 = mem[addr0_reg];'''
  
  elif write_mode == 'read_first':
    # Read-first: read old data before write
    return '''   // Port 0: Read-Write Port with Read-First behavior
   reg [BITS-1:0] dout0_reg;
   
   always @(posedge clk0) begin
      if (!csb0) begin  // Active low chip select
         // Read-first: capture data before potential write
         dout0_reg <= mem[addr0];
         
         if (!web0) begin  // Active low write enable - writing when web0=0
            {byte_write_logic}
         end
      end
   end
   
   // Read-first: output registered old data
   assign dout0 = dout0_reg;'''
  
  else:  # write_through (combinational read)
    # Write-through: combinational read path
    return '''   // Port 0: Read-Write Port with Write-Through behavior
   reg [BITS-1:0] dout0_reg;
   
   always @(posedge clk0) begin
      if (!csb0) begin  // Active low chip select
         if (!web0) begin  // Active low write enable - writing when web0=0
            {byte_write_logic}
         end
      end
   end
   
   // Write-through: combinational read from current address
   always @(*) begin
      if (!csb0)
         dout0_reg = mem[addr0];
      else
         dout0_reg = {BITS{1'bx}};
   end
   
   assign dout0 = dout0_reg;'''

def generate_rw_port_logic_1rw(write_mode):
  '''Generate the RW port logic for single-port SRAM based on write mode'''
  if write_mode == 'write_first':
    return '''   // Read-Write Port with Write-First behavior
   reg [ADDR_WIDTH-1:0] addr0_reg;
   
   always @(posedge clk0) begin
      if (!csb0) begin  // Active low chip select
         if (!web0) begin  // Active low write enable
            mem[addr0] <= din0;
         end
         addr0_reg <= addr0;
      end
   end
   
   assign dout0 = mem[addr0_reg];'''
  
  elif write_mode == 'read_first':
    return '''   // Read-Write Port with Read-First behavior
   reg [BITS-1:0] dout0_reg;
   
   always @(posedge clk0) begin
      if (!csb0) begin  // Active low chip select
         dout0_reg <= mem[addr0];  // Read first
         if (!web0) begin
            mem[addr0] <= din0;
         end
      end
   end
   
   assign dout0 = dout0_reg;'''
  
  else:  # write_through
    return '''   // Read-Write Port with Write-Through behavior
   reg [BITS-1:0] dout0_reg;
   
   always @(posedge clk0) begin
      if (!csb0) begin
         if (!web0) begin
            mem[addr0] <= din0;
         end
      end
   end
   
   always @(*) begin
      if (!csb0)
         dout0_reg = mem[addr0];
      else
         dout0_reg = {BITS{1'bx}};
   end
   
   assign dout0 = dout0_reg;'''

def generate_byte_write_logic(has_byte_write, num_bytes):
  '''Generate the byte-write logic for memories that support it'''
  if not has_byte_write:
    return 'mem[addr0] <= din0;'
  
  logic = ''
  logic += f'''if (wmask0[0])
               mem[addr0][7:0] <= din0[7:0];\n'''
  for i in range(1, num_bytes):
    logic += f'''            if (wmask0[{i}])
              mem[addr0][{i*8+7}:{i*8}] <= din0[{i*8+7}:{i*8}];\n'''
  return logic.rstrip()

def generate_verilog_bb(mem):
  '''Generate a verilog black-box view for the RAM'''
  name  = str(mem.name)
  depth = int(mem.depth)
  bits  = int(mem.width_in_bits)
  addr_width = math.ceil(math.log2(depth))
  
  has_rport = hasattr(mem, 'r_ports') and mem.r_ports > 0
  has_byte_write = hasattr(mem, 'write_granularity') and mem.write_granularity == 8
  num_bytes = bits // 8 if has_byte_write else 0

  fout = os.sep.join([mem.results_dir, name + '.bb.v'])
  with open(fout, 'w') as f:
    if has_rport:
      # Prepare byte-write parameters for black box
      if has_byte_write:
        bb_byte_write_params = f'   parameter NUM_BYTES = {num_bytes};\n'
        bb_byte_write_port = f'    wmask0,\n'
        bb_byte_write_decl = f'   input  [{num_bytes-1}:0]    wmask0;\n'
      else:
        bb_byte_write_params = ''
        bb_byte_write_port = ''
        bb_byte_write_decl = ''
        
      f.write(VLOG_BB_SPECIALIZED_1RW1R_TEMPLATE.format(
        name=name, 
        data_width=bits, 
        depth=depth, 
        addr_width=addr_width,
        byte_write_params=bb_byte_write_params,
        byte_write_port=bb_byte_write_port,
        byte_write_decl=bb_byte_write_decl
      ))

    else:
       bb_byte_write_params = ''
       bb_byte_write_port = ''
       bb_byte_write_decl = ''

# Template for specialized 1RW+1R SRAM matching buffered_liteeth SRAMs
VLOG_SPECIALIZED_1RW1R_TEMPLATE = '''\
module {name} (
`ifdef USE_POWER_PINS
    vdd,
    gnd,
`endif
    // Port 0: RW (Write/Read Port)
    clk0,
    csb0,
    web0,
{byte_write_port}    addr0,
    din0,
    dout0,
    // Port 1: R (Read-Only Port)
    clk1,
    csb1,
    addr1,
    dout1
);

   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};
{num_bytes_param}
`ifdef USE_POWER_PINS
   inout vdd;
   inout gnd;
`endif

   // Port 0: RW
   input                    clk0;
   input                    csb0;  // Active low chip select
   input                    web0;  // Active low write enable
{byte_write_decl}   input  [ADDR_WIDTH-1:0]  addr0;
   input  [BITS-1:0]        din0;
   output [BITS-1:0]        dout0;
   
   // Port 1: R
   input                    clk1;
   input                    csb1;  // Active low chip select
   input  [ADDR_WIDTH-1:0]  addr1;
   output [BITS-1:0]        dout1;

   // Memory array
   reg    [BITS-1:0]        mem [0:WORD_DEPTH-1];

   integer i;

{write_mode_comment}
{rw_port_logic}

   // Port 1: Read-Only Port
   reg [BITS-1:0] dout1_reg;
   
   always @(posedge clk1) begin
      if (!csb1) begin  // Active low chip select
         dout1_reg <= mem[addr1];
      end
   end
   
   assign dout1 = dout1_reg;

   // X-propagation and debug logic (optional)
   `ifdef SRAM_MONITOR
   always @(posedge clk0) begin
      if (!csb0 && !web0) begin
         $display("%t: %m writing addr0=%h din0=%h", $time, addr0, din0);
      end
   end
   `endif

   // Timing check placeholders
   `ifdef SRAM_TIMING_CHECK
   reg notifier;
   specify
      // Delays from clk to outputs (registered outputs)
      (posedge clk0 *> dout0) = (0, 0);
      (posedge clk1 *> dout1) = (0, 0);

      // Timing checks
      $width     (posedge clk0,              0, 0, notifier);
      $width     (negedge clk0,              0, 0, notifier);
      $period    (posedge clk0,              0,    notifier);
      $width     (posedge clk1,              0, 0, notifier);
      $width     (negedge clk1,              0, 0, notifier);
      $period    (posedge clk1,              0,    notifier);
{setuphold_checks}
   endspecify
   `endif

endmodule
'''

# Template for specialized 1RW SRAM (if needed)
VLOG_SPECIALIZED_1RW_TEMPLATE = '''\
module {name} (
`ifdef USE_POWER_PINS
    vdd,
    gnd,
`endif
    clk0,
    csb0,
    web0,
    addr0,
    din0,
    dout0
);

   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};

`ifdef USE_POWER_PINS
   inout vdd;
   inout gnd;
`endif

   input                    clk0;
   input                    csb0;  // Active low chip select
   input                    web0;  // Active low write enable
   input  [ADDR_WIDTH-1:0]  addr0;
   input  [BITS-1:0]        din0;
   output [BITS-1:0]        dout0;

   // Memory array
   reg    [BITS-1:0]        mem [0:WORD_DEPTH-1];

{write_mode_comment}
{rw_port_logic}

endmodule
'''

# Black box template for specialized 1RW+1R
VLOG_BB_SPECIALIZED_1RW1R_TEMPLATE = '''\
module {name} (
`ifdef USE_POWER_PINS
    vdd,
    gnd,
`endif
    // Port 0: RW
    clk0,
    csb0,
    web0,
{byte_write_port}    addr0,
    din0,
    dout0,
    // Port 1: R
    clk1,
    csb1,
    addr1,
    dout1
);

   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};
{byte_write_params}
`ifdef USE_POWER_PINS
   inout vdd;
   inout gnd;
`endif

   // Port 0: RW
   input                    clk0;
   input                    csb0;
   input                    web0;
{byte_write_decl}   input  [ADDR_WIDTH-1:0]  addr0;
   input  [BITS-1:0]        din0;
   output [BITS-1:0]        dout0;
   
   // Port 1: R
   input                    clk1;
   input                    csb1;
   input  [ADDR_WIDTH-1:0]  addr1;
   output [BITS-1:0]        dout1;

endmodule
'''

# Black box template for specialized 1RW
VLOG_BB_SPECIALIZED_1RW_TEMPLATE = '''\
module {name} (
`ifdef USE_POWER_PINS
    vdd,
    gnd,
`endif
    clk0,
    csb0,
    web0,
    addr0,
    din0,
    dout0
);

   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};

`ifdef USE_POWER_PINS
   inout vdd;
   inout gnd;
`endif

   input                    clk0;
   input                    csb0;
   input                    web0;
   input  [ADDR_WIDTH-1:0]  addr0;
   input  [BITS-1:0]        din0;
   output [BITS-1:0]        dout0;

endmodule
'''