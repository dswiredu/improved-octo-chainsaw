import pandas as pd
import numpy as np

from palm_scripts.helpers.common import initialize_palm_dll, convert_to_generic_dict
from palm_scripts.helpers.class_utils import get_class_field_data
from palm_scripts.helpers.reader import read_security_file, read_curve_data

from System import String, Int32, Double, Boolean, Single
from System.Collections.Generic import Dictionary

import warnings

warnings.filterwarnings("ignore")

def get_class_object(class_name: str, assembly_gdn):
    return assembly_gdn["pALMSimulation"].GetType(class_name)


def get_cpr_cdr_severity_curves(df: pd.DataFrame):
    return {col: df[col].to_dict() for col in ["CPR", "CDR", "Severity"]}


def generate_Cashflows(data: pd.DataFrame, curves: pd.DataFrame):
    assembly_registry_GDN = initialize_palm_dll()

    class_name = "pALMSimulation.LifeAssets.SimpleAssets.MortgageFloating"
    MortgageFloating_GDN = get_class_object(class_name, assembly_registry_GDN)

    class_name = "pALMSimulation.LifeAssets.BondRating"
    BondRating_GDN = get_class_object(class_name, assembly_registry_GDN)

    constructor = MortgageFloating_GDN.GetConstructor(
        [
            String,
            String,
            Int32,
            Double,
            Double,
            Double,
            Double,
            Double,
            BondRating_GDN,
            Int32,
            Boolean,
            Int32,
            Double,
            Double,
            Double,
            Double,
            Double,
            Boolean,
            Int32,
            Boolean,
            Dictionary[Single, Double],
            Int32,
            Int32,
            Dictionary[Int32, Double],
            Dictionary[Int32, Double],
            Dictionary[Int32, Double],
            Dictionary[Int32, Double],
        ]
    )

    iBondRating = BondRating_GDN.GetField("AAA").GetValue(None)
    is_floating = data["Adjustable Rate Flag"] == "Y"

    cpr_cdr = get_cpr_cdr_severity_curves(curves)
    icpr = convert_to_generic_dict(cpr_cdr["CPR"])
    icdr = convert_to_generic_dict(cpr_cdr["CDR"])
    iseverity = convert_to_generic_dict(cpr_cdr["Severity"])
    empty_args = [None] * 13

    init_args = [
        String(data["Unique Identifier"]),  # icusip
        String(data["Unique Identifier"]),  # iidentifier
        Int32(int(data["Original Term"])),  # iMaturity Maybe "Months to Maturity"?
        Double(float(data["Original Note Rate"]) / 100),  # iCoupon
        Double(float(data["Current Balance"])),  # iBookValue
        Double(float(data["Original Appraisal Value"])),  # imarketValue
        Double(float(data["Original Principal Balance"])),  # iFaceValue
        Double(float(data["Current Balance"])),  # iFacecurrent
        iBondRating,  # iBondRating
        Int32(int(data["Adjustable Rate - Rate Reset Frequency"])),  # iFrequency
        Boolean(is_floating),
        empty_args,  # iStartMonth -> iCallSchedule
        icpr,
        icdr,
        iseverity,
    ]

    args = sum([x if isinstance(x, list) else [x] for x in init_args], [])

    for idx, para in enumerate(constructor.GetParameters()):
        if idx >= len(args):
            args.append(None)

    ClassInstance = constructor.Invoke(args)

    ClassInstance.initialize()
    cfs = extract_calculated_cashflows(ClassInstance)
    print(ClassInstance.WAL())

    return {
        "cfs": cfs,
        "wal": ClassInstance.WAL(),
        "original_balance": ClassInstance.OriginalBalance,
        "coupon_rate": ClassInstance.FixedRate,
        "face_value": ClassInstance.GetFace(),
    }


def extract_calculated_cashflows(ClassInstance) -> pd.DataFrame:

    data = {"timestep": list(range(ClassInstance.OriginalTerm + 1))}

    # other cashflows may be protected or private
    cf_fields = [
        "outstandingBalance_",
        "interest_",
        "default_",
        "prepayment_",
        "totalPrincipalPaid_",
        "totalCF_",
    ]
    cfs = {
        field: np.array(get_class_field_data(ClassInstance, field))
        for field in cf_fields
    }
    data.update(cfs)
    res = pd.DataFrame(data)
    num_cols = res.columns[1:]
    res[num_cols] = res[num_cols] * ClassInstance.CurrentBalance
    return res


def run(curves_file: str, security_file: str) -> dict:
    data = read_security_file(security_file)
    curves = read_curve_data(curves_file)
    res = generate_Cashflows(data, curves)
    return res


# if __name__ == "__main__":
#     main()
