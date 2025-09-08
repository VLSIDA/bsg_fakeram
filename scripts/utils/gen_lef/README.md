# LEF Generator for SRAM

A Python-based Library Exchange Format (LEF) generator for creating FakeRAM macro files used in ASIC design flows.

## Project Structure

```
utils/gen_lef/
├── lef_core.py                 # Main entry point
├── lef_globals.py              # Global utilities
├── decimal_helpers.py          # Decimal arithmetic utilities
├── logic/                      # Core generation logic
│   ├── gen_ports.py            # Port pin placement
│   ├── gen_pinlist.py          # Pin list generation
│   ├── lef_writers.py          # LEF file writing
│   └── pin_wrappers.py         # Pin operation wrappers
├── modules/                    # Base classes
│   ├── class_lefparameters.py  # LEF parameters
│   └── class_pingrid.py        # Pin grid management
└── coordinates/                # Coordinate utilities
    └── snap_height.py          # Track alignment
```

## Core Modules

### Main Entry Point
- **`lef_core.py`** - Main function that orchestrates LEF generation

### Logic Layer
- **`gen_ports.py`** - Handles SRAM port pin placement (control, address, data)
  - Manages read/write/read-write ports
  - Handles pin assignment across multiple sides
  - Validates pin overlap and placement

- **`gen_pinlist.py`** - Generates equidistant pin lists
  - Creates sectioned pin distributions
  - Handles whole-side pin placement
  - Manages pin pitch and spacing

- **`lef_writers.py`** - Writes LEF file content
  - Generates LEF header and properties
  - Creates power grid straps (VDD/VSS)
  - Writes pin rectangles and obstruction layers

- **`pin_wrappers.py`** - Wrapper classes for pin operations
  - `PinListWrapper`: Manages pin placement parameters
  - `PinIndexWrapper`: Writes pins by index with safety checks

### Base Classes
- **`class_lefparameters.py`** - Centralizes LEF generation parameters
  - Process technology settings
  - Pin dimensions and pitches
  - Metal layer configurations

- **`class_pingrid.py`** - Manages pin grid creation and validation
  - Creates per-edge pin slots (top/bottom/left/right)
  - Validates manufacturing grid alignment
  - Handles pin pitch constraints

### Utilities
- **`decimal_helpers.py`** - Float-safe arithmetic using Decimal
  - Prevents floating-point drift
  - Provides consistent rounding for layout calculations

- **`snap_height.py`** - Track alignment utilities
  - Aligns pins to routing tracks
  - Snaps macro height to manufacturing grid

- **`lef_globals.py`** - Global utility functions
  - Grid snapping functions