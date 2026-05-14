## Originally FakeRAM2.0 (ABKGroup) area calculation for asap7 tech;
## extended here for sky130hd using OpenRAM bitcell data.
import math


# Per-technology 6T SRAM bitcell dimensions (width_um, height_um).
#  - asap7   : 0.108 x 0.270 um — published in Clark et al.,
#              "ASAP7: A 7-nm finFET predictive PDK",
#              Microelectronics Journal 2016 (2 contacted-poly-pitches x
#              10 fin-pitches; 0.0292 um^2 bitcell).
#  - sky130hd: 1.070 x 1.740 um — published bitcell from the
#              skywater-pdk OpenRAM 6T SRAM (~1.86 um^2 bitcell).
TECH_BITCELL_UM = {
    7:   (0.108, 0.270),
    130: (1.070, 1.740),
}

# Total SRAM area = bitcell_array * PERIPHERY_MULT_PER_DIM in each
# dimension, where PERIPHERY_MULT_PER_DIM ~= 2.5 covers the row decoder,
# wordline drivers, sense amps, write drivers, column muxes, and control
# logic typical of embedded SRAMs at 1-256 Kb sizes. (~6.25x bitcell-array
# area.) The same multiplier is used at every tech we support analytically.
PERIPHERY_MULT_PER_DIM = 2.5

# Target aspect ratio (longer/shorter side) of the bitcell array.
# A real SRAM compiler picks column_mux to land near 1-2x; we pick the
# K value that minimises distance to 1.5x. The range covers narrow-word
# deep memories — e.g. 16x32768 needs K=64 to get the array to ~square.
TARGET_ASPECT = 1.5
COL_MUX_CANDIDATES = (1, 2, 4, 8, 16, 32, 64, 128, 256)

# Minimum macro dimension: below this the PDN ring cannot close.
MIN_DIM_UM = 6.221


def _pick_column_mux(width_in_bits, depth, bitcell_w, bitcell_h):
  """Choose column_mux K that minimises aspect-ratio error vs TARGET_ASPECT."""
  best_k = 1
  best_diff = float("inf")
  for k in COL_MUX_CANDIDATES:
    if k > depth:
      break
    rows = math.ceil(depth / k)
    cols = width_in_bits * k
    h = rows * bitcell_h
    w = cols * bitcell_w
    aspect = max(h, w) / min(h, w)
    diff = abs(aspect - TARGET_ASPECT)
    if diff < best_diff:
      best_diff = diff
      best_k = k
  return best_k


def get_macro_dimensions(process, sram_data):
  width_in_bits = int(sram_data['width'])
  depth         = int(sram_data['depth'])

  # Bitcell size is technology-determined; fall back to the asap7 fin /
  # poly-pitch derivation if a tech-specific value isn't tabulated.
  if process.tech_nm in TECH_BITCELL_UM:
    bitcell_width, bitcell_height = TECH_BITCELL_UM[process.tech_nm]
  else:
    fin_pitch_um            = process.fin_pitch_nm / 1000
    contacted_poly_pitch_um = process.contacted_poly_pitch_nm / 1000
    bitcell_width  = 2 * contacted_poly_pitch_um
    bitcell_height = 10 * fin_pitch_um

  # Dynamically pick column_mux factor so the bitcell array lands near
  # TARGET_ASPECT instead of being slaved to process.column_mux_factor.
  k    = _pick_column_mux(width_in_bits, depth, bitcell_width, bitcell_height)
  rows = math.ceil(depth / k)
  cols = width_in_bits * k

  bitcell_array_w = cols * bitcell_width
  bitcell_array_h = rows * bitcell_height

  # Same multiplier on both dimensions: periphery scales with the corresponding
  # array edge (row-decoder on rows, sense-amps/wmask on cols).
  total_width  = max(MIN_DIM_UM, bitcell_array_w * PERIPHERY_MULT_PER_DIM)
  total_height = max(MIN_DIM_UM, bitcell_array_h * PERIPHERY_MULT_PER_DIM)
  return total_height, total_width