from __future__ import annotations

import pytest
from autoplex.benchmark.phonons.flows import PhononBenchmarkMaker
from pymatgen.io.phonopy import get_ph_bs_symm_line


def test_benchmark(test_dir, clean_dir):
    import os
    from pathlib import Path
    from jobflow import run_locally
    from monty.serialization import loadfn
    from atomate2.common.schemas.phonons import PhononBSDOSDoc

    # test with two different band-structures

    dft_data = loadfn(test_dir / "benchmark" / "PhononBSDOSDoc_LiCl.json")
    dft_doc: PhononBSDOSDoc = dft_data["output"]
    ml_doc: PhononBSDOSDoc = dft_data["output"]  # TODO put ML PhononBSDOSDoc

    parent_dir = os.getcwd()

    os.chdir(test_dir / "benchmark")

    benchmark_flow = PhononBenchmarkMaker().make(
        structure=dft_doc.structure,
        ml_phonon_task_doc =ml_doc,
        dft_phonon_task_doc =dft_doc,
        benchmark_mp_id="test",
    )
    assert len(benchmark_flow.jobs) == 1

    responses = run_locally(benchmark_flow, create_folders=False, ensure_success=True)

    assert responses[benchmark_flow.output.uuid][1].output == pytest.approx(
        0.0  #0.5716963823412201, abs=0.02
    )

    # get list of generated plot files
    test_files_dir = Path(test_dir / "benchmark").resolve()
    path_to_plot_files = list(test_files_dir.glob("LiCl*.eps"))

    # ensure two plots are generated
    assert len(path_to_plot_files) == 2
    # remove the plot files from directory
    for file in path_to_plot_files:
        file.unlink()

    os.chdir(parent_dir)
