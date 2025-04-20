import pandas as pd


def get_fixed_income(df: pd.DataFrame) -> pd.DataFrame:
    """Gets all fixed income securities that need ai calculated"""

    is_fixed_income_idx: pd.Series = (
        df["IsFixedIncome"].str.upper() == "TRUE"
    ) & (df["IsZeroCouponFlag"].str.upper() == "FALSE")

    invalid_fixed_income_idx: pd.Series = (
        df["IssueDate"].isna()
        | df["MaturityDate"].isna()
        | df["FirstCouponDate"].isna()
    )

    invalid_fi: pd.DataFrame = df[
        is_fixed_income_idx & invalid_fixed_income_idx
    ]
    if not invalid_fi.empty:
        invalid_fixed_income_securities = set(invalid_fi["SecurityID"])
        print(
            f"The following securities have invalid fixed income information: {invalid_fixed_income_securities}!"
        )

    valid_fi: pd.DataFrame = df[
        is_fixed_income_idx & ~(invalid_fixed_income_idx)
    ]

    if not valid_fi.empty:
        data = {
            "key": valid_fi["SecurityID"],
            "issue_date": valid_fi["IssueDate"],
            "maturity_date": valid_fi["MaturityDate"],
            "first_coupon_date": valid_fi["FirstCouponDate"],
            "last_coupon_date": valid_fi["LastCouponDate"],
            "prerefund_date": "",
            "pay_month_end": valid_fi["PayOnMonthEnd"].str.upper() == "TRUE",
            "calendar_code": valid_fi["AccrualCalendarCode"],
            "freq": valid_fi["PaymentFrequencyID"],
            "coupon_rate": pd.to_numeric(
                valid_fi["InterestOrDividendRate"], errors="coerce"
            ).fillna(0),
            "is_vrs": valid_fi["IsVRS"].str.upper() == "TRUE",
            "vrs_rule": valid_fi["CouponPaymentRuleID"],
            "vrs_freq": valid_fi["CouponPaymentFrequency"],
            "vrs_holiday_rule": valid_fi["CouponPaymentHolidayRuleCode"],
            "interest_pays_at_maturity": valid_fi[
                "PaysInterestAtMaturity"
            ].str.upper()
            == "TRUE",
        }
        return pd.DataFrame(data=data).fillna("")
    print("could not find any securities to compute AI on!")
