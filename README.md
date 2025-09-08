# BSG Black-box SRAM Generator

This project is desgined to generate black-boxed SRAMs for use in CAD flows
where either an SRAM generator is not avaible or doesn't exist.

## Setup

The black-box SRAM generator depends on lightly modified version of
[Cacti](https://github.com/HewlettPackard/cacti) for area, power, and timing
modeling. To build this version of Cacti, simply run:

```
$ make tools
```

## Usage

### Process Configuration

The input to the BSG Black-box SRAM generator is a simple JSON file that
contains some information about the technology node you are targeting as well
as the size and names of SRAMs you would like to generate. Below is an example
JSON file that can be found in `./example_cfgs/asap7.cfg`:

```
{
  "tech_nm": 7,
  "voltage": 0.7,
  "metalPrefix": "M",
  "manufacturing_grid_nm": 1,
  "pinParams": {
    "x_metLayerPin": 3,
    "x_pinPitch_nm": 36,
    "x_pinWidth_nm": 18,
    "x_pinHeight_nm": 36,
    "x_pinOffset_nm": 0,
    "y_metLayerPin": 4,
    "y_pinPitch_nm": 48,
    "y_pinWidth_nm": 24,
    "y_pinHeight_nm": 48,
    "y_pinOffset_nm": 0
  },
  "powerGridParams": {
    "directionPowerGrid": "horizontal",
    "metLayerPowerGrid": 4,
    "powerGridWidth_nm": 96,
    "powerGridPitch_nm": 384
  },
  "timing": {
    "t_setup_ns": 0.050,
    "t_hold_ns": 0.050,
    "cap_input_pf": 0.005
  },
  "additionalParams": {
    "heightSnapPinPitch": false,
    "widthSnapPinPitch": true,
    "column_mux_factor": 4,
    "snapWidth_nm": 190,
    "snapHeight_nm": 1400
  },
  "use_custom_tech": true,
  "custom_tech": {
    "access_time_ns": 0.2183,
    "cycle_time_ns": 0.2566,
    "fo4_ps": 9.0632,
    "standby_leakage_per_bank_mW": 0.1289,
    "pin_dynamic_power_mW": 0.0013449,
    "finPitch_nm": 27,
    "contacted_poly_pitch_nm": 54,
    "h0_tracks": 10,
    "w0_polys": 2,
    "dh_read": 2,
    "dw_read": 0.5,
    "dh_write": 2.5,
    "dw_write": 0.5,
    "dh_rw": 1,
    "dw_rw": 0.5
  },
  "add_fakeram_extension": true,
  "srams": [
    {
      "name": "testram7_1rw_32w1024d_sram",
      "width": 32,
      "depth": 1024,
      "banks": 1,
      "column_mux_factor": 6,
      "write_mode": "write_first",
      "ports": {
        "r": 0,
        "w": 0,
        "rw": 1
      }
    },
    ...
  ]
}
```
-----
`tech_nm` - The name of the target technology node (in nm). Used in Cacti for
modeling PPA of the SRAM.

`voltage` - Nominal operating voltage for the tech node.

`metalPrefix` - The string that prefixes metal layers.

`manufacturing_grid_nm` - (Optional : Default 1) The manufacturing grid for specific technology (in nm).

-----
`pinParams`: Main Pin Parameters

`x_metLayerPin` - Metal layer for horizontal pins (top and bottom of SRAM)

`y_metLayerPin` - Metal layer for vertical pins (left and right of SRAM)

`x_pinPitch_nm` - The minimum pin pitch for signal pins (in nm) for top/bottom (horizontal) pins.

`y_pinPitch_nm` - The minimum pin pitch for signal pins (in nm) for left/right (vertical) pins.

`x_pinOffset_nm` - (Optional : Default 0) Fixed offset x pin pitch (in nm), x pin pitch + x offset. Unaffected by pinPitchFactor

`y_pinOffset_nm` - (Optional : Default 0) Fixed offset y pin pitch (in nm), y pin pitch + y offset. Unaffected by pinPitchFactor

`x_pinWidth_nm` - The width of the horizontal signal pins (in nm).

`x_pinHeight_nm` - The height of the horizontal signal pins (in nm).

`y_pinWidth_nm` - The width of the vertical signal pins (in nm).

`y_pinHeight_nm` - The height of the vertical signal pins (in nm).

-----
`powerGridParams`: Main Power Grid Parameters

`directionPowerGrid` - (Options: "vertical" or "horizontal") Specify the direction of strapes.

`metLayerPowerGrid` - (Optional : Default 4) Metal layer of of strapes.

`powerGridWidth_nm` - (Optional : Default "pinWidth_nm") Strapes width (in nm).

`powerGridPitch_nm` - (Optional : Default "y_pinPitch_nm") Strapes pitch (in nm).

`powerGridOffset_nm` - (Optional : Default 0) Strapes offset (in nm), pitch + offset.

-----
`timing`: Timing for all SRAMs

`t_setup_ns` - Arbitrary hold time (in ns).

`t_hold_ns` - Arbitrary setup time (in ns).

`cap_input_pf` - Capacitance input (in pf).

-----
`additionalParams`: Optional Additional Parameters for SRAMs

`heightSnapPinPitch` - (Optional : Default False) Snap SRAMs height to nearest pin pitch. Y pin offset will be ignored.

`widthSnapPinPitch` - (Optional : Default False) Snap SRAMs width to nearest pin pitch. X pin offset will be ignored.

`verticalPinsOnly` - (Optional : Default False) Set all pins to left and right sides of sram.

`snapWidth_nm` - (Optional : Default 1) Snap the width of the generated memory to a
multiple of the given value.

`snapHeight_nm` - (Optional : Default 1) Snap the height of the generated memory to a
multiple of the given value.

`column_mux_factor` - (Optional : Default 1) It reduces the number of sense amplifiers needed, saving area, but may increase access time. When used the height is divided by its column mux factor and width multiplied by its column mux factor for all srams. Column mux factor defaults to 1. Can be overriden for a specific sram with parameter column_mux_factor_override in "sram". If CACTI is ran, this is ignored.

`add_fakeram_extension` - (Optional : Default False) Add 'fakeram.' prefix to all SRAM names.

### Custom Tech Configuration

Setting "use_custom_tech" and defining the parameters in "custom_tech" in json would be optimal since cacti does not support below 28nm or above 180nm. This config can be found in `example_cfgs/asap7.cfg`

`hybrid` - (Optional : Default False) Overrides specific cacti values with values in yml file. Otherwise will use cacti as default.

`access_time_ns` - Access time (in ns).

`cycle_time_ns` - Cycle time (in ns).

`fo4_ps` - Fanout of 4 (in ps).

`standby_leakage_per_bank_mW` - Standby leakage per bank (in mW).

`pin_dynamic_power_mW` - All pin dynamic power (in mW).

`finPitch_nm` - (FinFET Architecture) Fin pitch (in nm).

`contacted_poly_pitch_nm` - (FinFET Architecture) Contacted poly pitch (in nm).

`h0_tracks` - (FinFET Architecture) Height Tracks.

`w0_polys` - (FinFET Architecture) Width Polys.

`dh_read` - (Optional : Default 1) Dummy read port height overhead scaling factor.

`dw_read` - (Optional : Default 1) Dummy read port width overhead scaling factor.

`dh_write` - (Optional : Default 1) Dummy write port height overhead scaling factor.

`dw_write` - (Optional : Default 1) Dummy write port width overhead scaling factor.

`dh_rw` - (Optional : Default 1) Dummy read write port height overhead scaling factor.

`dw_rw` - (Optional : Default 1) Dummy read write port width overhead scaling factor.


```
"access_time_ns": 0.2183,
"cycle_time_ns": 0.2566,
"fo4_ps": 9.0632,
"standby_leakage_per_bank_mW": 0.1289,
"pin_dynamic_power_mW": 0.0013449,

"finPitch_nm": 27,
"contacted_poly_pitch_nm": 54,

"h0_tracks": 10,
"w0_polys": 2,

// Optional params, default: 1
"dh_read": 2,
"dw_read": 0.5,
"dh_write": 2.5,
"dw_write": 0.5,
"dh_rw": 1,
"dw_rw": 0.5

```

### Memory Configuration

`srams` - A list of SRAMs to generate. Each sram should have a `name`, `width`
(or the number of bits per word), `depth` (or number of words), and `banks`.

`banks` - (Optional : Default 1 | Options "2" , "4") Specify number of banks.

`column_mux_factor` - (Optional : Default "column_mux_factor") Overrides column_mux_factor for a specific sram.

`write_mode` - (Optional : Default "write_first" | Options "read_first" , "write_first") For Read Write ports, optional to chose as read_first otherwise write_first.

`write_granularity` - (Optional : Default "width") Specifies number of bits that can be written in a single write operation.

`Ports` :
 - Read ports, address and control pins are on the left, data pins are on the top
 - Write ports, address and control pins are on the right, data pins are on the bottom.

### Running the Generator

Now that you have a configuration file, it is time to run the generator. The
main makefile target is:

```
$ make run CONFIG=<path to config file>
```

If you'd perfer, you can open up the Makefile and set `CONFIG` rather than
setting it on the command line.

All of the generated files can be found in the `./results` directory. Inside
this directory will be a directory for each SRAM which contains the .lef, .lib
and v file (as well as some intermediate files used for Cacti).

### Comparison with standard SRAMs generated with OpenRAM compiler

#### Generated Fakerams (Eg:- fakeram130_1024x8)

![](docs/images/fakeram.png)

![](docs/images/fakeram_io.png)

- The generated fakerams are 1rw RAMs 
- All pins are on the left side and they are all on Metal 3.
- Pins:
  - 1x chip enable 
  - 1x write enable
  - 1x clock 
  - 1x address-in port
  - 1x data-in-data-out port
  - 1x write-mask-in port (bit masked).

![](docs/images/fakeram_power.png)

- Power rails are vertical (can be made horizontal in the config file) - Alternate VDD and GND rails.
- Metal layers 1, 2, 3 and 4 are blocked, metal 5 is free for routing over.

#### Standard SRAMs compiled with OpenRAM (Eg:- [sky130_sram_1kbyte_1rw1r_8x1024_8](https://github.com/efabless/sky130_sram_macros/tree/main/sky130_sram_1kbyte_1rw1r_8x1024_8))

![](docs/images/openram.png)

![](docs/images/openram_pins.png)

- 1rw1r RAMs
- Pins cover all 4 sides
- I/O pins use Metal 3 (on left and right sides) & Metal 4 (on top and bottom sides)
- Pins:
  - 2x clock 
  - 2x chip select
  - 1x write enable
  - 2x address-in port
  - 1x data-out port
  - 1x data-in-data-out port
  - 1x write-mask pin/port (byte masked)

- Power pins are in a ring format along the macro edge utilizing Metal 3 (Horizontal) & Metal 4 (Vertical)
- Metal layers 1, 2, 3 and 4 are blocked, metal 5 is free for routing over.



## Feedback

Feedback is always welcome! We ask that you submit a GitHub issue for any bugs,
improvements, or new features you would like to see. We are also receptive to
outside contributions but please be mindful of sensitive information that is
commonly associated with licensed IP.

