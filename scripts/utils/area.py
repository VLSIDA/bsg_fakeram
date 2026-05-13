## FakeRAM2.0 (ABKGroup) area calculation for asap7 tech ##
import math


# Calibrated against the published ASAP7 6T SRAM bitcell (Clark et al.,
# "ASAP7: A 7-nm finFET predictive PDK", Microelectronics Journal 2016).
# The bitcell is 0.108 x 0.27 um (2 contacted-poly-pitches wide x 10 fin-pitches
# tall = 0.0292 um^2). Total SRAM area = bitcell_array * PERIPHERY_MULT_PER_DIM
# in each dimension, where PERIPHERY_MULT_PER_DIM ~= 2.5 covers the row decoder,
# wordline drivers, sense amps, write drivers, column muxes, and control logic
# typical of embedded SRAMs at 1-256 Kb sizes. (~6.25x bitcell-array area.)
PERIPHERY_MULT_PER_DIM = 2.5

# Target aspect ratio (longer/shorter side) of the bitcell array.
# A real SRAM compiler picks column_mux to land near 1-2x; we pick the
# {1,2,4,8,16,32} value that minimises distance to 1.5x.
TARGET_ASPECT = 1.5
COL_MUX_CANDIDATES = (1, 2, 4, 8, 16, 32)

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
  fin_pitch_um            = process.fin_pitch_nm / 1000
  contacted_poly_pitch_um = process.contacted_poly_pitch_nm / 1000
  width_in_bits           = int(sram_data['width'])
  depth                   = int(sram_data['depth'])

  # ASAP7 6T SRAM bitcell (Clark et al., 2016).
  bitcell_width  = 2 * contacted_poly_pitch_um  # 0.108 um
  bitcell_height = 10 * fin_pitch_um            # 0.270 um

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