# =========================================================================
# MOOSE cohesive-zone input-parameter TEMPLATE  --  NOT A VERIFIED INPUT FILE
#
# DO NOT RUN until the MOOSE security review is complete (repo rule, AGENTS.md).
# Nothing in fracture_bridge/ executes or installs MOOSE; this file only carries
# the physics parameters the tissue-scale model needs, in MOOSE input syntax.
#
# CHECK KEYWORDS: blocks below follow the MOOSE Solid Mechanics cohesive-zone
# interface (DomainBoundaryCohesiveZone mesh generator, CohesiveZone action,
# PWL / triangular cohesive-law materials). Parameter names DRIFT between MOOSE
# versions. Before running, diff every keyword against the header files of the
# approved MOOSE checkout (modules/solid_mechanics).
# =========================================================================

# Condition: synthetic-triangular
# Units: SYNTHETIC TEST DATA (Pa, m, J/m^2) — not a physical collagen calibration
#
# Cohesive-zone parameters extracted by fracture_bridge/extract_cohesive.py
# from notched-network traction-separation curves (mean ± sd over realizations):
#   G_cI   [energy/area] = 15.1041 ± 1.35625 (sd, n=8 realizations)
#   Tn_max [force/area] = 1.540074e+6 ± 88579.1 (sd, n=8 realizations)
#   delta_n,peak [length] = 9.899458e-6 ± 7.948679e-7 (sd, n=8 realizations)
#   delta_n,f    [length] = 1.958417e-5 ± 1.530152e-6 (sd, n=8 realizations)
#   K_n     [Pa/m] = 1.566307e+11 ± 1.840992e+10 (sd, n=8 realizations)
#   G_cII / G_cI: UNAVAILABLE (mode-II data absent)
#   mode-I: all realizations complete.

# Consistency check (triangular law): G_c = 0.5 * T_max * delta_f.
#   mode I : 0.5*1.54007e+06*1.95842e-05 = 15.0805 vs G_cI = 15.1041

[Mesh]
  # Insert cohesive-zone interface elements on the controlled notch plane.
  [./czm_interface]
    type = DomainBoundaryCohesiveZone
    boundary = 'CRACK_INTERFACE'
    # input = 'notch_specimen.e'   # notched specimen mesh (controlled-notch first; see README)
    # NOTE: check this block against the approved MOOSE version's
    # modules/solid_mechanics mesh generators before running.
  [../]
[]

[GlobalParams]
    displacements = 'disp_x disp_y disp_z'
[]

# CZM action: assembles interface kernels + cohesive material on the crack surface.
[CohesiveZone]
  [./interface]
    boundary = 'CRACK_INTERFACE'
    cohesive_law = 'PWL'          # piece-wise-linear: can carry the raw network T(delta) shape
    displacements = 'disp_x disp_y disp_z'
    large_kinematics = true       # collagen tissue works at large strain
  [../]
[]

# ---- Cohesive law parameters ----
# Option A (faithful): piece-wise-linear tables of the normalized network
# curve delta/delta_f vs T/T_max. Export per condition with
# extract_cohesive.py (one table per mode) and point the material at them.
[Materials]
  [./cohesive_pwl]
    type = PWL
    boundary = 'CRACK_INTERFACE'
    normal_table = 'PLACEHOLDER_norm_T_delta_modeI.csv'   # delta_n/delta_n,f vs T_n/Tn_max
    # CHECK the table-parameter keyword names in the approved MOOSE version.
  [../]

  # Option B (analytic): triangular cohesive law, parameters from the adapter.
  # For a triangular law G_c = 0.5 * T_max * delta_f, so the three numbers
  # below are not independent; MOOSE variants that take (T_max, delta_f)
  # or (T_max, G_c) should be given the pair quoted here.
  [./cohesive_triangular]
    type = PLACEHOLDER_TRIANGLE_CZM_CLASS          # e.g. TriangleCZM-family; verify name
    boundary = 'CRACK_INTERFACE'
    G_cI = 15.1041                # mode-I energy release rate  [energy/area]
    normal_strength = 1.540074e+6         # Tn_max [force/area]
    normal_stiffness = 1.566307e+11         # K_n [Pa/m]  (= Tn_max / delta_n,peak)
    # delta_n,f and delta_t,f (failure separations) for reference:
    #   delta_n,f = 1.958417e-5   delta_t,f = UNAVAILABLE
  [../]

# ---- Bulk material: NONLINEAR ANISOTROPIC VISCOELASTIC CALIBRATION ----
# The CZM law above only describes the crack plane. The surrounding tissue
# bulk must come from the lower scales of the fracture pipeline:
#   * fibril scale (LAMMPS, remote/lammps/*.in): G'(w), G''(w) -> Prony
#     relaxation spectrum (g_i, k_i, tau_i);
#   * fiber network (oxt, other agent): modulus, anisotropy (fiber
#     orientation tensor / orientation distribution), damage-free response;
#   * physical calibration: convert dimensionless network/LAMMPS output to
#     Pa and m using the length/force/thickness scales in README.md.
# Everything below marked PLACEHOLDER must be filled by that calibration.
  [./bulk_matrix]
    type = PLACEHOLDER_BULK_nonlinear_anisotropic_viscoelastic
    # --- elasticity (nonlinear, large strain) ---
    # candidate base laws to evaluate at review time: neo-Hookean /
    # Mooney-Rivlin hyperelastic; REQUIRED inputs:
    Youngs_modulus = PLACEHOLDER_E          # [Pa] from network G' x thickness
    Poissons_ratio = PLACEHOLDER_nu
    large_kinematics = true
    # --- anisotropy (fiber-reinforced) ---
    # candidate: fiber-direction / orthotropic term with orientation tensor A
    fiber_orientation_tensor = PLACEHOLDER_A_11_A_12_A_13_A_22_A_23_A_33
    fiber_stiffness = PLACEHOLDER_E_f        # [Pa] fibril-scale axial modulus
    fiber_direction = 'PLACEHOLDER_unit_vector'
    # --- viscoelasticity (Prony) ---
    # Prony series fitted to fibril G'(w), G''(w) and network relaxation:
    prony_moduli = 'PLACEHOLDER_g1 PLACEHOLDER_g2 PLACEHOLDER_g3'
    prony_times = 'PLACEHOLDER_tau1 PLACEHOLDER_tau2 PLACEHOLDER_tau3'
    # --- mesh coupling ---
    displacements = 'disp_x disp_y disp_z'
  [../]

[]
[BCs]
  # PLACEHOLDER: specimen grip loading from the tissue-scale experiment protocol.
  # Mixed-mode loading: prescribe normal and shear displacement components on the
  # grips; keep the notch plane as the only pre-defined crack path (see README).
[]

[Executioner]
  type = Transient
  solve_type = 'PJFNK'
  petsc_options_iname = '-pc_type -pc_factor_shift_type'
  petsc_options_value = 'lu nonzero'
  dt = PLACEHOLDER_dt          # PLACEHOLDER: choose from K_n and mesh size (stability)
  dtmin = PLACEHOLDER_dtmin
  end_time = PLACEHOLDER_end_time
[]

[Outputs]
  exodus = true
  csv = true
[]

# End of template. Postprocess: J-integral / energy-release-rate comparison
# against the network-scale G_c is the acceptance test for the bridge.