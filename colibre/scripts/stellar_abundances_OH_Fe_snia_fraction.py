"""
Plots [O/H] vs mass fraction of Fe from SNIa
"""
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import swiftsimio
import unyt
from swiftsimio import load
from swiftpipeline.argumentparser import ScriptArgumentParser
from typing import Tuple


def read_data(data: swiftsimio.SWIFTDataset) -> Tuple[np.ndarray, np.ndarray]:
    """
    Grabs the data
    """

    mH_in_cgs = unyt.mh
    mO_in_cgs = 15.999 * unyt.mp

    # Asplund et al. (2009)
    O_H_Sun_Asplund = 8.69

    O_H_Sun = O_H_Sun_Asplund - 12.0 - np.log10(mH_in_cgs / mO_in_cgs)

    iron = data.stars.element_mass_fractions.iron
    iron_snia = data.stars.iron_mass_fractions_from_snia
    oxygen = data.stars.element_mass_fractions.oxygen
    hydrogen = data.stars.element_mass_fractions.hydrogen

    O_H = np.log10(oxygen / hydrogen) - O_H_Sun
    Fe_snia_fraction = iron_snia / iron

    O_H[oxygen == 0] = -7  # set lower limit
    O_H[O_H < -7] = -7  # set lower limit

    particles_with_iron = iron > unyt.unyt_quantity(0.0, "dimensionless")

    return O_H[particles_with_iron], Fe_snia_fraction[particles_with_iron]


arguments = ScriptArgumentParser(
    description="Creates an [O/H] - mass fraction of Fe from SNIa for stars."
)

snapshot_filenames = [
    f"{directory}/{snapshot}"
    for directory, snapshot in zip(arguments.directory_list, arguments.snapshot_list)
]

names = arguments.name_list
output_path = arguments.output_directory

plt.style.use(arguments.stylesheet_location)

simulation_lines = []
simulation_labels = []

fig, ax = plt.subplots()
ax.grid(True)

for snapshot_filename, name in zip(snapshot_filenames, names):

    snapshot_data = load(snapshot_filename)
    redshift = snapshot_data.metadata.z

    O_H, Fe_snia_fr = read_data(snapshot_data)

    # low zorder, as we want these points to be in the background
    dots = ax.plot(O_H, Fe_snia_fr, ".", markersize=0.2, alpha=0.2, zorder=-99)[0]

    # Bins along the X axis (O_H) to plot the median line
    bins = np.arange(-7.2, 1, 0.2)
    ind = np.digitize(O_H, bins)

    xm, ym = [], []
    Min_N_points_per_bin = 11

    for i in range(1, len(bins)):
        in_bin_idx = ind == i
        N_data_points_per_bin = np.sum(in_bin_idx)
        if N_data_points_per_bin >= Min_N_points_per_bin:
            xm.append(np.median(O_H[in_bin_idx]))
            ym.append(np.median(Fe_snia_fr[in_bin_idx]))

    # high zorder, as we want the simulation lines to be on top of everything else
    # we steal the color of the dots to make sure the line has the same color
    simulation_lines.append(
        ax.plot(
            xm,
            ym,
            lw=2,
            color=dots.get_color(),
            zorder=1000,
            path_effects=[pe.Stroke(linewidth=4, foreground="white"), pe.Normal()],
        )[0]
    )
    simulation_labels.append(f"{name} ($z={redshift:.1f}$)")

ax.set_xlabel("[O/H]")
ax.set_ylabel("Fe (SNIa) / Fe (Total)")

ax.set_ylim(3e-3, 3.0)
ax.set_xlim(-7.2, 2.0)
ax.set_yscale("log")

simulation_legend = ax.legend(
    simulation_lines, simulation_labels, markerfirst=False, loc="lower left"
)

ax.add_artist(simulation_legend)

plt.savefig(f"{output_path}/stellar_abundances_OH_Fe_snia_fraction.png")
