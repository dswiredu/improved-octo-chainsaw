import os

import pALMPy as pp

from System import Int32, Double
from System.Collections.Generic import Dictionary

from django.conf import settings

def initialize_palm_dll(
    solution_dir: str = settings.PALM_DLL_PATH,
    version: str = settings.PALM_VERSION,
    build: bool = settings.PALM_BUILD,
) -> dict:
    solution_file = os.path.join(solution_dir, "pALM.sln")

    dll_directory = os.path.join(
        solution_dir, "pALMLiability", "pALMLauncher", "bin", "Release", f"net{version}"
    )

    dll = pp.DLLManager()
    if build:
        dll.build_dlls(solution_file)
    dll.load_dlls(dll_directory)
    return dll.assembly_registry


def convert_to_generic_dict(dct: dict):
    net_dict = Dictionary[Int32, Double]()
    for k, v in dct.items():
        net_dict[Int32(k)] = Double(v)
    return net_dict
