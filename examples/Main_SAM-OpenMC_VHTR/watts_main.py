# SPDX-FileCopyrightText: 2022 UChicago Argonne, LLC
# SPDX-License-Identifier: MIT

"""
This example just uses the workflow in `MultiApp_SAM-OpenMC_VHTR`
and applies it in a procedure for re-use in optimization and
sensitivity analyses.
"""

from pathlib import Path
from math import cos, pi
import os
import watts
from statistics import mean
from openmc_template import build_openmc_model

params = watts.Parameters()
# TH params
params['He_inlet_temp'] = 600 + 273.15  # K
params['He_outlet_temp'] = 850 + 273.15 # K
params['He_cp'] = 5189.2 # J/kg-K
params['He_K'] =  0.32802   # W/m-K
params['He_density'] = 3.8815   # kg/m3
params['He_viscosity'] = 4.16e-5 # Pa.s
params['He_Pressure'] = 7e6    # Pa
params['Tot_assembly_power'] = 250000 # W

# power fractions coming from example 3
params['Init_P_1'] = 0.26567586383363173
params['Init_P_2'] = 0.2905585465106731
params['Init_P_3'] = 0.29676571959449854
params['Init_P_4'] = 0.24839580939676342
params['Init_P_5'] = 0.17495310589992397

# Core design params
params['ax_ref'] = 20 # cm
params['num_cool_pins'] = 1*6+2*6+6*2/2
params['num_fuel_pins'] = 6+6+6+3*6+2*6/2+6/3
params['Height_FC'] = 2.0 # m
params['Lattice_pitch'] = 2.0
params['Assembly_pitch'] = 7.5 * 2 * params['Lattice_pitch'] / (cos(pi/6) * 2)
params['lbp_rad'] = 0.25 # cm
params['mod_ext_rad'] = 0.90 # cm
params['shell_thick'] = 0.05   # FeCrAl
params['liner_thick'] = 0.007  # Cr
params['control_pin_rad'] = 0.99 # cm
# Control use of S(a,b) tables
params['use_sab'] = True
params['use_sab_BeO'] = True
params['use_sab_YH2'] = False
# OpenMC params
params['cl'] = params['Height_FC']*100 - 2 * params['ax_ref'] # cm
params['pf'] = 40 # percent
params['num_cpu'] = 60

def calc_workflow(X):
    """ example of workflow calculation that includes SAM and OpenMC """

    # params to optimize
    params['FuelPin_rad'] = X[0] # cm
    params['cool_hole_rad'] = X[1] # cm
    params['Coolant_channel_diam'] = (params['cool_hole_rad'] * 2)/100 # in m
    params['Graphite_thickness'] = (params['Lattice_pitch'] - params['FuelPin_rad'] - params['cool_hole_rad']) # cm

    print("FuelPin_rad / cool_hole_rad", X[0], X[1])

    # MOOSE Workflow
    # set your SAM directory as SAM_DIR
    app_dir = Path(os.environ["SAM_DIR"])
    sam_plugin = watts.PluginMOOSE(
        '../1App_SAM_VHTR/sam_template',
        executable=app_dir / 'sam-opt',
        show_stderr=False
    )
    sam_result = sam_plugin(params)
    max_Tf = max(sam_result.csv_data[f'max_Tf_{i}'][-1] for i in range(1, 6))
    avg_Tf = mean(sam_result.csv_data[f'avg_Tf_{i}'][-1] for i in range(1, 6))
    print("MaxTfuel / AvgTfuel= ", max_Tf, avg_Tf)

    # get temperature from SAM results
    params['temp'] = mean([sam_result.csv_data[f'avg_Tgraphite_{i}'][-1] for i in range(1, 6)])
    for i in range(1, 6):
        params[f'temp_F{i}'] = sam_result.csv_data[f'avg_Tf_{i}'][-1]

    # Run OpenMC plugin
    openmc_plugin = watts.PluginOpenMC(build_openmc_model, show_stderr=False) # does not show anything
    openmc_result = openmc_plugin(params)
    print("KEFF = ", openmc_result.keff)

    return (openmc_result.keff.n, max_Tf, avg_Tf)

