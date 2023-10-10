"""
Jobs to fit ML potentials
"""
from __future__ import annotations

import numpy as np
from ase.io import read, write
import subprocess
from pathlib import Path
import re
import os
from jobflow import Flow, Response, job
from dataclasses import dataclass, field
from autoplex.fitting.utils import (
    load_gap_hyperparameter_defaults,
    gap_hyperparameter_constructor,
)

CurrentDir = Path(__file__).absolute().parent


@job
def gapfit(
    fitinput: dict,
    isolatedatoms,
    isolatedatomsenergy,
    gap_input=CurrentDir / "gap-defaults.json",
    twobody: bool = True,
    threebody: bool = False,
    soap: bool = True,
    fit_kwargs: dict = field(default_factory=dict),
):
    """
    job that prepares GAP fit input and fits the data using GAP. More ML methods (e.g. ACE) to follow.

    """
    flattened_input = lambda x: [
        y
        for z in x
        for y in (flattened_input(z) if isinstance(z, list) else [z])  # type:ignore
    ]
    fit = flattened_input(
        [
            dirs
            for data in fitinput.values()
            for datatype, dirs in data.items()
            if datatype != "phonon_data"
        ]
    )  # uniform data structure
    for entry in fit:
        file = read(re.sub(r"^.*?/", "/", entry, count=1) + "/OUTCAR.gz", index=":")
        for (
            i
        ) in (
            file
        ):  # credit goes to http://home.ustc.edu.cn/~lipai/scripts/ml_scripts/outcar2xyz.html
            xx, yy, zz, yz, xz, xy = -i.calc.results["stress"] * i.get_volume()
            i.info["virial"] = np.array([(xx, xy, xz), (xy, yy, yz), (xz, yz, zz)])
            del i.calc.results["stress"]
            i.pbc = True
        write("trainGAP.xyz", file, append=True)

    # with open(gap_input, "r") as infile:
    #     inputs = json.load(infile)

    gap_default_hyperparameters = load_gap_hyperparameter_defaults(
        gap_fit_parameter_file_path=gap_input
    )

    e0: str = "{"

    for isoatom, isoenergy in zip(isolatedatoms, isolatedatomsenergy):
        if isoatom == isolatedatoms[-1]:
            e0 += str(isoatom) + ":" + str(isoenergy) + "}"
        else:
            e0 += str(isoatom) + ":" + str(isoenergy) + ":"
    # Updating the isolated atom energy
    gap_default_hyperparameters["general"].update({"e0": e0})
    # Overwriting the default gap_fit settings with user settings  # TODO XPOT support
    for key in gap_default_hyperparameters:
        for key2 in fit_kwargs:
            if key == key2:
                gap_default_hyperparameters[key].update(fit_kwargs[key2])

    gap = gap_hyperparameter_constructor(
        gap_parameter_dict=gap_default_hyperparameters,
        two_body=twobody,
        three_body=threebody,
        soap=soap,
    )
    # gap: str = GAPHyperparameterParser(
    #     inputs=inputs, twobody=twobody, threebody=threebody, soap=soap
    # )
    general = [
        str(key) + "=" + str(gap_default_hyperparameters["general"][key])
        for key in gap_default_hyperparameters["general"]
    ]

    with open("std_out.log", "w") as file_std, open("std_err.log", "w") as file_err:
        subprocess.call(["gap_fit"] + general + [gap], stdout=file_std, stderr=file_err)

        directory = Path.cwd()

    return Response(
        output=str(
            os.path.join(directory, gap_default_hyperparameters["general"]["gp_file"])
        )
    )


#
# def GAPHyperparameterParser(
#     inputs, twobody: bool = True, threebody: bool = False, soap: bool = True
# ):
#     twob: str = " ".join(
#         [f"{key}={value}" for key, value in inputs["twob"].items() if twobody is True]
#     )
#     threeb: str = " ".join(
#         [
#             f"{key}={value}"
#             for key, value in inputs["threeb"].items()
#             if threebody is True
#         ]
#     )
#     SOAP: str = str(":soap " if soap is True else "") + " ".join(
#         [f"{key}={value}" for key, value in inputs["soap"].items() if soap is True]
#     )
#     gap: str = "gap={" + (twob + threeb + SOAP) + "}"
#
#     return gap
