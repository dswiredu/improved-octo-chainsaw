from datetime import datetime
import os
import pathlib
import collections

import pandas as pd

from mapper import get_fixed_income
import ai

SECFILE = "s3://d1g1t-custodian-data-ca-central-1/apx/claret/20250409/Security.csv"# "Security_20240730_d1g1tEdit.csv"
RESETFILE = "s3://d1g1t-custodian-data-ca-central-1/apx/claret/20250409/ResetRateSchedule.csv" # "ResetRateSchedule.csv"
START_DATE = "2019-12-31"  # POC start date
TODAY = datetime.today().strftime("%Y-%m-%d")
DIR = pathlib.Path(__file__).parent.resolve()


def get_securities():
    secfile = os.path.join(DIR, "..", SECFILE)
    df = pd.read_csv(SECFILE, dtype=str, encoding="ISO-8859-1")
    return df


def get_reset_rates():
    reset_file = os.path.join(DIR, "..", RESETFILE)
    df = pd.read_csv(RESETFILE, dtype=str)
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
    col_rename = {"SecurityID": "key", "AsOfDate": "date", "Rate": "rate"}
    df.rename(columns=col_rename, inplace=True)

    ai_rates = collections.defaultdict(list)
    reset_rate_securities = set(df["key"])
    for key in reset_rate_securities:
        key_rate = df[df["key"] == key]
        ai_rates[key].append(
            (key_rate["date"].values, key_rate["rate"].values)
        )
    return ai_rates


def parse_accrued_interest(df: pd.DataFrame) -> None:
    print("Getting fixed income from Securities...")
    fi = get_fixed_income(df)
    ai_reset_rates = get_reset_rates()

    # Only calculate AI starting from POC period
    calc_fi = fi[fi["maturity_date"] >= START_DATE]
    ai_out, bad_ai = dict(), list()

    if not calc_fi.empty:
        for idx, row in calc_fi.iterrows():
            try:
                key = row["key"]
                print(f"Building ai for {key}...")

                if row["is_vrs"] and (key in ai_reset_rates):
                    ai_out[key] = ai.gen_floating_ai(row, ai_reset_rates[key])
                elif row["coupon_rate"] != 0:
                    ai_out[key] = ai.gen_fixed_ai(row)

            except Exception as e:
                print(f"Error building ai for {key} - {e}")
                bad_ai.append(key)

        if ai_out:
            dfs = []
            for key, (dates, values) in ai_out.items():
                df = pd.DataFrame(
                    list(zip(dates, values)), columns=["Date", "Value"]
                )
                df["InstrumentID"] = key
                df["Date"] = pd.to_datetime(df["Date"])
                df = df[df.Date >= START_DATE]
                dfs.append(df)
            result = pd.concat(dfs)

            savefile = os.path.join(DIR, f"accruedinterest_{TODAY}.csv")
            print(f"Saving {len(result)} ai...")
            result.to_csv(savefile, index=False)
            print("Done!")
        else:
            print(
                "Could not find any accrued fixed income to compute accrued interest!"
            )

        if bad_ai:
            print(
                f"The following instruments have bad accrued interest and thus could not be computed {bad_ai}!"
            )


def main():
    df = get_securities()
    parse_accrued_interest(df)


if __name__ == "__main__":
    main()
