"""
Complete AutoPLEX -- Automated machine-learned Potential Landscape explorer -- jobs
"""

from pathlib import Path
from pymatgen.core.structure import Structure
from jobflow import Flow, job, Response
from atomate2.forcefields.jobs import GAPRelaxMaker, GAPStaticMaker
from atomate2.forcefields.flows.phonons import PhononMaker


@job
def PhononMLCalculationJob(
        structure: Structure,
        ml_dir: str | Path | None = None,
):
    jobs = []
    GAPPhonons = PhononMaker(
        bulk_relax_maker=GAPRelaxMaker(potential_param_file_name=ml_dir, relax_cell=True,
                                       relax_kwargs={"interval": 500}),
        phonon_displacement_maker=GAPStaticMaker(potential_param_file_name=ml_dir),
        static_energy_maker=GAPStaticMaker(potential_param_file_name=ml_dir),
        store_force_constants=False,
        generate_frequencies_eigenvectors_kwargs={"units": "THz"}).make(
        structure=structure)
    jobs.append(GAPPhonons)

    flow = Flow(jobs, GAPPhonons.output)  # output for calculating RMS/benchmarking
    return Response(replace=flow)

@job
def CollectBenchmark(
            structure_list: list[Structure],
            mpids,
            rms
    ):
        with open("results_" + ".txt", 'a') as f:
            f.write("Pot Structure mpid RMS RMS2 imagmodes(pot) imagmodes(dft) \nGAP" + ' ')
            # TODO include which pot. method has been used (GAP, ACE, etc.)

        for struc_i, structure in structure_list:
            with open("results_" + ".txt", 'a') as f:
                f.write(str(structure.composition.reduced_formula) + ' ' + str(rms[struc_i]) + str(mpids[struc_i]))
                # TODO has img modes + ' ' + ' ' + str(ml.has_imag_modes(0.1)) + ' ' + str(dft.has_imag_modes(0.1))

        return Response