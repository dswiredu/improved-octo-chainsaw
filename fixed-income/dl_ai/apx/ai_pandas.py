"""
The functions are developed according to:
https://en.wikipedia.org/wiki/Day_count_convention
"""

import pandas as pd


def gen_coupons(row):
    """
    generate coupon dates
    """
    freq = 12 // row.freq
    # find which day of the month the first coupon is issued
    offset = int(row.first_coupon_date[-2:])
    # generate a Month Start (MS) for all the coupons
    ms = pd.date_range(
        row.first_coupon_date[:-3], row.maturity_date[:-3], freq=f"{freq}MS"
    )
    # shift the coupons MS by days, this can push some coupons to next month if offset is 31
    off = ms + pd.DateOffset(days=offset - 1)
    me = ms + pd.offsets.MonthEnd()
    # make sure the coupon date stays in the same month and is not pushed to the next month
    coupons = pd.DataFrame([off, me]).min()
    # Ensure the final maturity date is included if it is not already
    if coupons.iloc[-1] < pd.to_datetime(row.maturity_date):
        coupons = pd.concat(
            [coupons, pd.Series(pd.to_datetime(row.maturity_date))],
            ignore_index=True,
        )
    return coupons


def gen_dates(issue_date, coupons, pm):
    """
    generate all dates between issue and maturity, and find the accrued start and end for each day.
    """

    # generate all the dates that a bond is alive
    dates = pd.date_range(issue_date, coupons.iloc[-1])
    # dt1, dt2, and dt3 are wikipedia nomenclature:
    #   dt1: the date interest starts to accrued (coupon or issue date)
    #   dt2: the date the AI is calculated at (current date)
    #   dt3: the date of the next payment (coupon or maturity date)
    starts = pd.concat([pd.Series(dates[0]), coupons])
    starts.name = "dt1"
    coupons.name = "dt3"
    # am/pm means when the bond interest is paid.
    #   am: the bond payment is in the morning, so that day does not accrued anymore
    #   pm: the bond payment is at the EOD, so you are entitled to all the AI if you sell it
    # if pm:
    #   pm is like shifting the end day forward by one, to capture
    #   the need for BoD on start date to EoD on end date
    df = pd.DataFrame(
        {"dates": dates, "dt2": dates + pd.DateOffset(days=1) if pm else dates}
    )
    df = df.merge(starts, how="left", left_on="dates", right_on="dt1").ffill()
    df = df.merge(coupons, how="left", left_on="dates", right_on="dt3").bfill()
    return df


def day_count_30_360_us(dfi, EOM):
    """
    30/360 US convention of the wikipedia page
    https://en.wikipedia.org/wiki/Day_count_convention#30/360_US
    """
    df = dfi.copy()
    df["d1"], df["d2"] = df.dt1.dt.day, df.dt2.dt.day
    df["m1"], df["m2"] = df.dt1.dt.month, df.dt2.dt.month
    df["y1"], df["y2"] = df.dt1.dt.year, df.dt2.dt.year
    if EOM:
        # NOT TESTED
        idx_d1_feb_end = (df.dt1.dt.is_month_end) & (df.m1 == 2)
        idx_d2_feb_end = (df.dt2.dt.is_month_end) & (df.m2 == 2)
        # If the investment is EOM and (Date1 is the last day of February)
        # and (Date2 is the last day of February), then change D2 to 30.
        df.loc[(idx_d1_feb_end) & idx_d2_feb_end, "d2"] = 30
        # If the investment is EOM and (Date1 is the last day of February), then change D1 to 30.
        df.loc[idx_d1_feb_end, "d1"] = 30
    # If D2 is 31 and D1 is 30 or 31, then change D2 to 30.
    df.loc[(df.d2 == 31) & (df.d1 >= 30), "d2"] = 30
    # If D1 is 31, then change D1 to 30.
    df.loc[df.d1 == 31, "d1"] = 30
    day_count_factor = (
        360 * (df.y2 - df.y1) + 30 * (df.m2 - df.m1) + (df.d2 - df.d1)
    ) / 360
    return day_count_factor


def calc_ai(row, EOM=False, pm=False):
    # Have to fix the row due to bad database model
    row["freq"] = int(row["freq"])
    row = pd.Series(row)
    coupons = gen_coupons(row)
    df = gen_dates(row.issue_date, coupons, pm)
    df["day_count_factor"] = day_count_30_360_us(df, EOM)
    df["ai"] = df.day_count_factor * row.coupon_rate
    return df
