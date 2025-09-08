# Memory Initialization System

A Python-based memory initialization system that integrates CACTI (Cache Access and Cycle Time Information) modeling with custom memory parameters to generate complete SRAM configurations.

## Overview

This system takes memory specifications and generates detailed memory objects with timing, power, and area characteristics. It supports three modes:
- **CACTI-only**: Uses CACTI for all parameters
- **Custom-only**: Uses only user-provided parameters  
- **Hybrid**: Combines CACTI with custom overrides

## Project Structure

```
utils/mem_init/
├── mem_init.py              # Main initialization entry point
├── mem_area.py              # Area and dimension calculations
├── mem_globals.py           # Global utilities and CACTI integration
└── modules/                 # Core classes
    ├── __init__.py          # Module exports
    ├── class_memory.py      # Main Memory class
    ├── class_cacti.py       # CACTI data parsing
    └── class_custom.py      # Custom parameter handling
```

## Core Modules

### Main Entry Point
- **`mem_init.py`** - Main memory initialization function
  - Orchestrates the entire initialization process
  - Sets up output directories and CACTI integration
  - Handles mode selection (CACTI/Custom/Hybrid)

### Area Calculations
- **`mem_area.py`** - Memory dimension and area calculations
  - **`get_macro_dimensions()`** - Calculates memory height/width from bitcell parameters
  - **`final_area()`** - Applies snapping to manufacturing grid and track pitch
  - Handles banking and column multiplexing effects

### Global Utilities
- **`mem_globals.py`** - Shared utilities and CACTI integration
  - **`run_cacti()`** - Executes CACTI tool with generated config
  - **`print_init_sram()`** - Comprehensive memory parameter summary
  - **`round_up_to_multiple()`** - Precise decimal rounding for layout
  - **`get_custom()`** - Parameter selection logic for hybrid mode
  - Banking and column mux dimension helpers

## Core Classes

### Memory Class
- **`class_memory.py`** - Main memory configuration object
  - Stores all memory parameters (width, depth, ports, timing)
  - Calculates derived properties (address width, total size)
  - Supports multiple port types (read, write, read-write)
  - Handles write masking and granularity

### CACTI Integration
- **`class_cacti.py`** - CACTI result parsing and processing
  - **`CactiData`** - Parses CACTI CSV output into typed fields
  - **`HybridData`** - Container for timing/power parameters in hybrid mode
  - Extracts timing, power, and area data from CACTI results

### Custom Parameters
- **`class_custom.py`** - User-defined memory parameters
  - Technology parameters (fin pitch, poly pitch)
  - Timing parameters (access time, cycle time)
  - Power parameters (leakage, dynamic power)
  - Area scaling factors for different port types
