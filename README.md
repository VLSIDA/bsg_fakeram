# Dynamic Black-box SRAM Generator (based off of [BSG_FakeRAM](https://github.com/bespoke-silicon-group/bsg_fakeram))

The intent of this project is to improve some features for the FakeRAM generator created by the folks over at [Bespoke Silicon Group](https://www.bsg.ai/). 
It also uses some of the ASAP7 timing constraints and parameters from ABKGroup's [FakeRAM2.0](https://github.com/ABKGroup/FakeRAM2.0). 
The purpose of the project is to add configurability for varying FakeRAM configs, since both generators are limited to only `rw` SRAM configs. 
Our generator allows for varying configs (i.e. `1r1w`, `2r1w`, `1rw1r`, etc.). 

## Setup

The black-box SRAM generator depends on lightly modified version of
[Cacti](https://github.com/HewlettPackard/cacti) for area, power, and timing
modeling. To build this version of Cacti, simply run:

```
$ make tools
```

## Usage

### Configuration File

The input to the BSG Black-box SRAM generator is a simple JSON file that
contains some information about the technology node you are targeting as well
as the size and names of SRAMs you would like to generate. Below is an example
JSON file that can be found in `./example_cfgs/freepdk45.cfg`:

```
{
  "tech_nm": 130,
  "voltage": 1.8,
  "metalPrefix": "met",

  "LRpinWidth_nm": 300,
  "LRpinHeight_nm": 800,
  "LRpinPitch_nm": 680,
  "TBpinWidth_nm": 140,
  "TBpinHeight_nm": 350,
  "TBpinPitch_nm": 460,

  "snapWidth_nm":   460,
  "snapHeight_nm": 2720,

  "flipPins": true,

  "srams": [
  {
     "name": "fakeram_1x256_1r1w", 
     "width": 1,
     "depth": 256,
     "banks": 1,
     "no_wmask": "true",
     "ports": {
       "r": 1,
       "w": 1,
       "rw": 0
     }
  },
  {
     "name": "fakeram_32x128_2r1w", 
     "width": 32,
     "depth": 128,
     "banks": 1,
     "no_wmask": "true",
     "ports": {
       "r": 2,
       "w": 1,
       "rw": 0
     }
  }
  ]
}
```

`tech_nm` - The name of the target technology node (in nm). Used in Cacti for
modeling PPA of the SRAM.

`voltage` - Nominal operating voltage for the tech node.

`metalPrefix` - The string that prefixes metal layers.

`LRpinWidth_nm` - The width of the signal pins on the **left** and **right** sides of the macro (in nm).

`LRpinPitch_nm` - The min. pitch of the signal pins on the **left** and **right** sides. Pins will be spaced based on a multiple of this pitch.

`LRpinHeight_nm` ***(Optional)***  - The length of the **left** and **right** signal pins. Calculated as `LRpinWidth_nm * 3` by default.

`TBpinWidth_nm` - The width of the signal pins on the **top** and **bottom** sides of the macro (in nm).

`TBpinPitch_nm` - The min. pitch of the signal pins on the **top** and **bottom** sides. Pins will be spaced based on a multiple of this pitch.

`TBpinHeight_nm` ***(Optional)*** - The length of the **top** and **bottom** signal pins. Calculated as `TBpinWidth_nm * 3` by default.

`pinPitch_nm` - The minimum pin pitch for signal pins (in nm). All pins will
have a pitch that is a multuple of this pitch. The first pin will be a
multiple of this pitch from the bottom edge of the macro too.

`snapWidth_nm` ***(Optional)*** -  Snap the width of the generated memory to a
multiple of the given value. By default, `snapWidth_nm = 1nm`.

`snapHeight_nm` ***(Optional)*** - Snap the height of the generated memory to a
multiple of the given value. By default, `snapHeight_nm = 1nm`.

`flipPins` ***(Optional)*** - Flip the pins. If set to false then metal 1 is
assumed to be vertical. This means that signal pins will be on metal 4 and the
supply straps (also on metal 4) will be horizontal. If set to true then metal 1
is assumed to be horizontal. This means that signal pins will be on metal 3 and
the supply straps (on metal 4) will be vertical. By default, `flipPins = false`.
`flipPins` continues to govern the supply-strap orientation even when
`LRpinLayer`/`TBpinLayer`/`PSpinLayer` are used to override the signal/supply
pin layers below — the two are independent knobs, so overriding the layers
does not change strap direction, and the pair must be kept mutually
consistent by hand.

`LRpinLayer` / `TBpinLayer` / `PSpinLayer` ***(Optional)*** - Explicit metal
layer name (e.g. `"M2"`) for the **left/right** signal pins, **top/bottom**
signal pins, and supply (VDD/VSS) straps, respectively. Overrides the layer
that would otherwise be derived from `flipPins`. Use this for platforms whose
pin layers can't be expressed by the `flipPins` heuristic alone (e.g. a
process that puts L/R pins on M2 and T/B pins on M3). Unset by default, in
which case the `flipPins`-derived layer is used.

`srams` - A list of SRAMs to generate. Each sram should have: 
- `name` - the name associated with the sram config in the SRAM's `.lef`, `.lib`, and `.v` files
- `width` - the number of bits per word 
- `depth` - the number of words in the SRAm
- `banks` - the number of banks the SRAM should be split into
- `no_wmask` ***(Optional)*** - `true` if the SRAM doesn't use any mask bits, `false` otherwise. Set to `true` by default. 
- `ports` - the number of `r`, `w` and `rw` ports that the SRAM macro contains (allows for the creation of various SRAM configs in a single `.cfg` file).

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

## Pin Naming Conventions

When interfacing your FakeRAM's `.v`, `.lef` and `.lib` files to a larger design, it's important to match the naming convention used by the generator.
Below is an example of the naming for the pins in a `2r1w` FakeRAM config:
- `w0_mask_in` ***(Optional)*** - write mask bus for the write port. Does not exist for a FakeRAM design if `no_wmask = True`
- `w0_wd_in` - write data bus for our single write port
- `w0_we_in` - write enable bus for our single write port
- `r0_rd_out` - read data bus for our **first** read port
- `r1_rd_out` - read data bus for our **second** read port
- `w0_addr_in` - address bus for our single write port
- `r0_addr_in` - address bus for our **first** read port
- `r1_addr_in` - address bus for our **second** read port
- `w0_ce_in` - chip enable signal for our single write port
- `r0_ce_in` - chip enable signal for our **first** read port
- `r1_ce_in` - chip enable signal for our **second** read port
- `w0_clk` - clock signal for our single write port
- `r0_clk` - clock signal for our **first** read port
- `r1_clk` - clock signal for our **second** read port

For a config using a `rw` port, the pin names would be prefixed with `rw` rather than `r` or `w`. Keep the naming convention in 
mind when interfacing your FakeRAM macro with a larger design.

## Memory Banking 

By default, if a user specifies more than one memory bank ***(which must be an even value)*** it will splice based on `width`. There is an optional 
config variable `banking_convention`, which can be used to specify banking based on `depth`:
- `"banking_convention" : "width"` ***(DEFAULT)*** - memory banks will be created by splicing based on width
- `"banking_convention" : "depth"` - memory banks will be created by splicing based on depth





