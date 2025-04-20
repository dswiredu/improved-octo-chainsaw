import numpy as np

issue = "2017-08-18"
maturity = "2024-08-19"
fc_dtate = "2017-09-09"


def get_ai_dates(issue: str, maturity: str) -> np.array:
    start, stop = np.datetime64(issue), np.datetime64(maturity)
    return np.arange(start, stop+1, dtype='datetime64[D]')

def get_coupon_dates(first_coupon_date: str, maturity: str) -> np.array:
    start = np.datetime64(first_coupon_date)
    stop = np.datetime64(maturity)

    days = int(first_coupon_date.split("-")[-1])

    start_month = start.astype('datetime64[M]')
    stop_month = stop.astype('datetime64[M]')

    coupon_mnths = np.arange(start_month, stop_month + 1, step=np.timedelta64(6, 'M'))
    coupon_dates  = coupon_mnths.astype('datetime64[D]') + np.timedelta64(days-1, 'D')
    return coupon_dates[coupon_dates < stop]

def __generate_indexed_coupon_dates(all_dates: np.array, coupon_dates: np.array) -> np.array:
    next_coupon_date_idx = np.searchsorted(all_dates, coupon_dates)
    coupon_series = np.full(len(all_dates), np.datetime64('NaT') , dtype='datetime64')# np.zeros(len(all_dates))
    coupon_series[next_coupon_date_idx] = coupon_dates
    coupon_series[0] = all_dates[0]
    mask = np.isnat(coupon_series)
    coupon_series[mask] = np.maximum.accumulate(coupon_series)
    return coupon_series.astype('datetime64[D]')

def main():
    dtes = get_ai_dates(issue, maturity)
    cdtes = get_coupon_dates(fc_dtate, maturity)
    coupon_series  = __generate_indexed_coupon_dates(dtes, cdtes)
    day_counts = (dtes - coupon_series).astype(int)
    res = day_counts/360/2
    return res

if __name__ == "__main__":
    main()