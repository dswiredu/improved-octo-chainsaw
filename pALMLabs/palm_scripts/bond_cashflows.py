import os
import sys

import numpy as np
import pandas as pd

import json

from copy import deepcopy
from datetime import datetime, timedelta


import pALMPy as pp
import subprocess

from System import String, Int32, Double, Boolean, Nullable, Single, Array
from System.Collections.Generic import Dictionary

import warnings

warnings.filterwarnings("ignore")


def main():
    # Define paths
    solution_dir = r"C:\Users\dwiredu\Documents\pALM2.1_guardian_corpModel - Copy"  # Change to your location
    solution_file = os.path.join(solution_dir, "pALM.sln")
    asset_tape_file = r"C:\Users\dwiredu\Documents\pALM2.1_guardian_corpModel - Copy\pALMLiability\pALMLauncher\bin\Release\net5.0\data\data_guardian_2025\assets\pALM_asset_tape_20250331_v4_trad_corp.csv"
    assembly_registry_GDN = {}
    dll_directory = os.path.join(
        solution_dir, r"pALMLiability/pALMLauncher/bin/Release/net5.0"
    )  # Change

    dll = pp.DLLManager()
    dll.build_dlls(solution_file)
    dll.load_dlls(dll_directory)
    assembly_registry_GDN = dll.assembly_registry

    class_name = "pALMSimulation.LifeAssets.SimpleAssets.FixedRateBond"
    FixedRateBond_GDN = assembly_registry_GDN["pALMSimulation"].GetType(class_name)

    BondRating_GDN = assembly_registry_GDN["pALMSimulation"].GetType(
        "pALMSimulation.LifeAssets.BondRating"
    )
    Frequency_GDN = assembly_registry_GDN["pALMSimulation"].GetType(
        "pALMSimulation.LifeAssets.SimpleAssets.FREQUENCY"
    )

    class_name = "pALMSimulation.Assets.SimulationEnvironment"
    SimulationEnvironment_GDN = assembly_registry_GDN["pALMSimulation"].GetType(
        class_name
    )

    class_name = "pALMSimulation.Curves.SwapCurve"
    SwapCurve_GDN = assembly_registry_GDN["pALMSimulation"].GetType(class_name)

    class_name = "pALMSimulation.Curves.RateCurve"
    RateCurve_GDN = assembly_registry_GDN["pALMSimulation"].GetType(class_name)

    asst_tpe = pd.read_csv(asset_tape_file, dtype=str)

    bond_idx = 3307
    icusip = String(str(asst_tpe["cusip"].iloc[bond_idx]))
    # icusip = String("AA")
    iidentifier = String("Private")
    iMaturity = Double(int(asst_tpe["maturity_in_months"].iloc[bond_idx]))
    iCoupon = Double(float(asst_tpe["coupon_fixedrate"].iloc[bond_idx]))

    iBookValue = Double(float(asst_tpe["bookprice"].iloc[bond_idx]))
    imarketValue = Double(float(asst_tpe["marketprice"].iloc[bond_idx]))
    iFaceValue = Double(float(asst_tpe["par"].iloc[bond_idx]))
    iBondRating = BondRating_GDN.GetField(asst_tpe["rating"].iloc[bond_idx]).GetValue(
        None
    )
    freq = pp.get_frequency((int(asst_tpe["frequency"].iloc[bond_idx])), Frequency_GDN)
    # is_floating = Boolean(bool(asst_tpe['is_floating'].iloc[idx]))
    is_floating = Boolean(bool(1))
    ifloating_margin = Double(float(asst_tpe["floating_margin"].iloc[bond_idx]))

    ifloating_floor = Double(float(asst_tpe["floating_floor"].iloc[bond_idx]))
    ifloating_cap = Double(float(asst_tpe["floating_cap"].iloc[bond_idx]))

    constructor = FixedRateBond_GDN.GetConstructor(
        [
            String,
            String,
            Double,
            Double,
            Double,
            Double,
            Double,
            BondRating_GDN,
            Frequency_GDN,
            Int32,
            Boolean,
            Double,
            Double,
            Double,
            Boolean,
            Boolean,
            Dictionary[Single, Double],
            Dictionary[Int32, Double],
        ]
    )

    args = [
        icusip,
        iidentifier,
        iMaturity,
        iCoupon,
        iBookValue,
        imarketValue,
        iFaceValue,
        iBondRating,
        freq,
        Int32(0),
        is_floating,
        ifloating_margin,
        ifloating_floor,
        ifloating_cap,
    ]

    for idx, para in enumerate(constructor.GetParameters()):
        # if idx >= len(args): args.append(getDotNETSystemType(para.ParameterType, para.DefaultValue))
        if idx >= len(args):
            args.append(None)

    FixedRateBond_GDN = constructor.Invoke(args)
    book_price = float(iBookValue) / float(iFaceValue)
    bkyield = FixedRateBond_GDN.getOASYield(Double(book_price), Int32(0))
    FixedRateBond_GDN.set_BookYield(bkyield)

    cashflow_dict = FixedRateBond_GDN.cashflows_.leg
    res_dict = {}
    for key in cashflow_dict.Keys:
        res_dict[key] = cashflow_dict[key].Rate

    df = pd.DataFrame(list(res_dict.items()), columns=["t", "C_t"])
    df.to_csv(f"Cashflows-{bond_idx}.csv", index=False)


if __name__ == "__main__":
    main()
