import os
import re

import pALMPy as pp

from System import String, Int32, Double, Boolean, Nullable, Single, Array
from System.Collections.Generic import Dictionary


CUSTOM_TYPE_MAP = {
    "String": String,
    "Int32": Int32,
    "Double": Double,
    "Boolean": Boolean,
    "Single": Single,
}


class PALMpyBase:
    def __init__(self, solution_dir: str, build: bool = True) -> None:
        self.solution_dir = solution_dir
        self.build = build
        self._solution_file = os.path.join(solution_dir, "pALM.sln")
        self.assembly_registry_GDN = self.get_assembly_registry()

    def get_assembly_registry(self):
        dll = pp.DLLManager()
        if self.build:
            dll.build_dlls(self._solution_file)
        dll_directory = self.__dll_directory()
        dll.load_dlls(dll_directory)
        return dll.assembly_registry

    def __dll_directory(self) -> str:
        dll_directory = os.path.join(
            self.solution_dir,
            "pALMLiability",
            "pALMLauncher",
            "bin",
            "Release",
            f"net{self.__palm_version}",
        )
        return dll_directory

    def __palm_version(self):
        """
        Resolve palm version from solution directory
        """
        return "net5.0"

    def get_class_object(self, class_name: str):
        return self.assembly_registry_GDN["pALMSimulation"].GetType(class_name)

    @staticmethod
    def convert_to_generic_dict(dct: dict, key_type, value_type):
        net_dict = Dictionary[key_type, value_type]()
        for k, v in dct.items():
            net_dict[key_type(k)] = value_type(v)
        return net_dict

    def main(self): ...


#     def initialize_palm_dll(self) -> dict:
#         solution_file = os.path.join(solution_dir, "pALM.sln")

#         dll_directory = os.path.join(
#             solution_dir, "pALMLiability", "pALMLauncher", "bin", "Release", f"net{version}"
#         )

#         dll = pp.DLLManager()
#         if build:
#             dll.build_dlls(solution_file)
#         dll.load_dlls(dll_directory)
#         return dll.assembly_registry
