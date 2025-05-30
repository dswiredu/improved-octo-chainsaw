from typing import List, Dict

import pandas as pd

from palm_scripts import mortgage_floating as mf
from ..models import SDACurveInputs, SDACurveRunMetrics, SDACurveCashFlows


def generate_and_save_sda_results(run: SDACurveInputs):
    try:
        results = mf.run(run.curve_file, run.security_file)

        metrics, created = SDACurveRunMetrics.objects.update_or_create(
            run=run,
            original_balance=results["original_balance"],
            coupon_rate=results["coupon_rate"],
            face_value=results["face_value"],
            WAL=results["wal"],
        )

        cfs: pd.DataFrame = results["cfs"]
        cf_objects = [
            SDACurveCashFlows(
                run_metrics=metrics,
                timestep=row["timestep"],
                balance=row["outstandingBalance_"],
                interest=row["interest_"],
                default=row["default_"],
                prepayment=row["prepayment_"],
                principal=row["totalPrincipalPaid_"],
                totalcf=row["totalCF_"],
            )
            for _, row in cfs.iterrows()
        ]
        SDACurveCashFlows.objects.bulk_create(cf_objects)
        return True
    except Exception as err:
        print(f"Failed to run SDA and save results: {err}")
    return False

def get_metric_card_context(metrics: SDACurveRunMetrics) -> List[Dict]:
    metric_cards = [
        {
            "label": "Original Balance",
            "value": metrics.original_balance,
            "suffix": "USD",
            "icon": "fas fa-wallet",
            "tooltip": "Starting balance of the loan",
            "colored": True
        },
        {
            "label": "WAL",
            "value": metrics.WAL,
            "suffix": "Years",
            "icon": "fas fa-hourglass-half",
            "tooltip": "Weighted Average Life",
            "colored": True
        },
        {
            "label": "Coupon Rate",
            "value": metrics.coupon_rate,
            "suffix": "%",
            "icon": "fas fa-percentage",
            "tooltip": "Annual coupon interest rate",
            "colored": True
        },
        {
            "label": "Face Value",
            "value": metrics.face_value,
            "suffix": "USD",
            "icon": "fas fa-money-bill-wave",
            "tooltip": "Original face value of the bond",
            "colored": True
        }
    ]
    return metric_cards

