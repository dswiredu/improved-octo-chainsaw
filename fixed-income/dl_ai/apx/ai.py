import calendar as pycalendar
import datetime

import numpy

import ai_pandas
from tools import ai, calendar
from tools import tseries

ISO_DATE = "%Y-%m-%d"


def gen_cdates_for_year(cdate, freq, pay_monthend):
    """generates coupon dates for a single year given date and freq"""
    init = cdate[4:]
    if freq == 1 or freq == 12:
        return [init]
    else:
        init_date = datetime.datetime.strptime(cdate, "%Y%m%d")
        if pay_monthend:
            dates = ai.EOM_SERIES
        else:
            # will generate 0230 as option but there's logic later to handle it.
            dates = [
                str(i + 1).zfill(2) + str(init_date.day).zfill(2)
                for i in range(12)
            ]
        month_idx = init_date.month - 1
        if freq == 2:
            return [dates[month_idx], dates[(month_idx + 6) % 12]]
        elif freq == 4:
            return [
                dates[month_idx],
                dates[(month_idx + 3) % 12],
                dates[(month_idx + 6) % 12],
                dates[(month_idx + 9) % 12],
            ]


def backfill_ai(dates, values):
    """
    Back-fill single-day ai back by
    a month but only for bonds with 1-yr maturity. Per Darcy!
    """
    start, bfill_date, end = (
        dates[0].astype(datetime.datetime),
        dates[0] - numpy.timedelta64(30, "D"),
        dates[-1],
    )
    if (
        datetime.date(
            start.year + 1,
            start.month,
            min(
                start.day,
                pycalendar.monthrange(start.year + 1, start.month)[1],
            ),
        )
        >= end
    ):
        backfill_range = numpy.arange(bfill_date, start, dtype="datetime64[D]")
        backfill_values = numpy.full(30, values[0])
        final_dates = numpy.concatenate((backfill_range, dates))
        final_values = numpy.concatenate((backfill_values, values))
        return final_dates, final_values
    else:
        return dates, values


def ffill_prerefunded_date(dates, values, prerefunded_date):
    """
    If prerefunded_date exists:
        ffill prerefunded_date - 1 ai
        till 7 days after maturityDate
    else:
        ffill maturityDate-1 ai till
        7 days after
    """
    maturity = dates[-1] + 1  # last date is day before maturity
    extended = maturity + numpy.timedelta64(8, "D")
    prerefunded_date = (
        numpy.datetime64(prerefunded_date) if prerefunded_date else None
    )
    start = (
        prerefunded_date
        if prerefunded_date and dates[0] <= prerefunded_date <= dates[-1]
        else maturity
    )
    extended_range = numpy.arange(start, extended, dtype="datetime64[D]")
    ffill_idx = numpy.searchsorted(dates, start)
    extended_values = numpy.full(len(extended_range), values[ffill_idx - 1])
    return (
        numpy.arange(dates[0], extended, dtype="datetime64[D]"),
        numpy.concatenate((values[:ffill_idx], extended_values)),
    )


def gen_fixed_ai(sec):
    method = AI_RULES.get(sec["calendar_code"], "30_360_us")
    if method == "30_360_us":
        df = ai_pandas.calc_ai(sec, pm=True)
        return df.dates.dt.date.values, df.ai.values
    first_coupon = datetime.datetime.strptime(
        sec["first_coupon_date"], ISO_DATE
    )
    last_coupon = (
        datetime.datetime.strptime(sec["last_coupon_date"], ISO_DATE)
        if sec["last_coupon_date"]
        else None
    )
    enforce_monthend = (  # Change recently made based on discussions with GG: See https://github.com/d1g1tinc/data-loaders/blob/ddd2b8753fec83b0494fd7fe3319140705dd6140/dataloader/drivers/crestone/ai.py#L83-L86 for original logic
        calendar.is_monthend(first_coupon) and sec["pay_month_end"]
    )
    freq = int(sec["freq"])
    cdates = gen_cdates_for_year(
        sec["first_coupon_date"].replace("-", ""), freq, enforce_monthend
    )
    dates, values = method(
        sec["issue_date"].replace("-", ""),
        sec["maturity_date"].replace("-", ""),
        freq,
        cdates,
        first_coupon,
        last_coupon,
        sec["interest_pays_at_maturity"],
    )
    values = values * float(sec["coupon_rate"]) / freq

    dates, values = backfill_ai(dates, values)
    dates, values = ffill_prerefunded_date(
        dates, values, sec["prerefund_date"]
    )
    return dates, values


def base_series(start, maturity, freq, cdates, first_coupon=None):
    # don't accrue on start date as it'll be handled by that eod logic
    all_coupons = ai.gen_coupon_dates(
        start, maturity, int(freq), sorted(cdates), False
    )
    if first_coupon:
        all_coupons[all_coupons < first_coupon.date()] = all_coupons[0]
    all_dates = ai.gen_all_dates(all_coupons[0], maturity)
    coupon_series = numpy.zeros(len(all_dates))
    coupon_series[numpy.searchsorted(all_dates, all_coupons)] = all_coupons
    coupon_series = tseries.ffill(coupon_series).astype(
        "datetime64[D]", copy=False
    )
    return all_dates, coupon_series


def gen_act360(
    start,
    maturity,
    freq,
    cdates,
    first_coupon,
    last_coupon,
    interest_pays_at_maturity=False,
):
    dates, coupons = base_series(start, maturity, freq, cdates, first_coupon)
    dates_eod = dates + 1
    day_count = tseries.bfill((dates_eod - coupons).astype(int, copy=False))
    day_count_fraction = day_count / (360 / freq)
    if interest_pays_at_maturity:
        period_index_series = get_coupon_period_indices(dates, coupons)
        day_count_fraction += period_index_series
    return dates, day_count_fraction


def gen_act365(
    start,
    maturity,
    freq,
    cdates,
    first_coupon,
    last_coupon,
    interest_pays_at_maturity=False,
):
    dates, coupons = base_series(start, maturity, freq, cdates, first_coupon)
    dates_eod = dates + 1
    day_count = tseries.bfill((dates_eod - coupons).astype(int, copy=False))
    day_count_fraction = day_count / (365 / freq)
    if interest_pays_at_maturity:
        period_index_series = get_coupon_period_indices(dates, coupons)
        day_count_fraction += period_index_series
    return dates, day_count_fraction


def is_fc_long(start, first_coupon, coupon_periods):
    max_period = numpy.max(coupon_periods.astype(int))
    return (
        max_period
        < (first_coupon - datetime.datetime.strptime(start, "%Y%m%d")).days
        < 2 * max_period
    )


def get_coupon_period_indices(dates, coupons):
    # Get an array of the current coupon period on a given date
    unique_coupons = numpy.unique(coupons)
    period_indices = list(range(len(unique_coupons)))
    period_index_series = numpy.zeros(len(dates))
    period_index_series[numpy.searchsorted(dates, unique_coupons)] = (
        period_indices
    )
    period_index_series = tseries.ffill(period_index_series)
    return period_index_series


def gen_actact(
    start,
    maturity,
    freq,
    cdates,
    first_coupon,
    last_coupon,
    interest_pays_at_maturity=False,
):
    dates, coupons = base_series(start, maturity, freq, cdates, first_coupon)

    # compute days between coupon (add coupon to maturity), include coupons before first coupon.
    unique_coupons = ai.gen_coupon_dates(
        start, maturity, int(freq), sorted(cdates), False
    )
    coupon_periods = numpy.diff(
        numpy.concatenate((unique_coupons, [dates[-1] + 1]))
    )
    period_series = numpy.zeros(len(dates))
    period_series[numpy.searchsorted(dates, unique_coupons)] = coupon_periods
    period_series = tseries.ffill(period_series)

    dates_eod = dates + 1
    day_count = tseries.bfill((dates_eod - coupons).astype(int, copy=False))
    day_count_fraction = day_count / period_series

    front_notional_dates, back_notional_dates = (
        ai.calc_notional_dates_for_irregular_periods(
            start, maturity, freq, cdates, first_coupon, last_coupon
        )
    )

    # Adjust for front stub
    if any(front_notional_dates) and first_coupon:
        front_stub_indices = (dates < numpy.datetime64(first_coupon)) & (
            dates >= front_notional_dates[0]
        )
        front_stub_day_count = numpy.zeros_like(day_count)
        front_stub_fraction = numpy.zeros_like(day_count_fraction)

        # Calculate the front stub fraction over multiple periods, to nsure accumulation to do
        last_fraction = 0

        # Long Front Stubs
        for i in range(len(front_notional_dates) - 1):
            period_start = front_notional_dates[i]
            period_end = front_notional_dates[i + 1]
            period_length = period_end - period_start
            period_indices = (
                dates
                >= max(
                    period_start,
                    numpy.datetime64(f"{start[:4]}-{start[4:6]}-{start[6:]}"),
                )
            ) & (dates < period_end)
            front_stub_day_count[period_indices] = (
                dates_eod[period_indices] - period_start
            )
            front_stub_fraction[period_indices] = (
                front_stub_day_count[period_indices]
                / period_length.astype(int)
            ) + last_fraction
            last_fraction = front_stub_fraction[period_indices][-1]

        # Short front stubs
        period_start = front_notional_dates[-1]
        period_end = numpy.datetime64(first_coupon.strftime("%Y-%m-%d"))
        period_length = period_end - numpy.datetime64(front_notional_dates[-1])
        period_indices = (
            dates
            >= max(
                period_start,
                numpy.datetime64(f"{start[:4]}-{start[4:6]}-{start[6:]}"),
            )
        ) & (dates < period_end)
        front_stub_day_count[period_indices] = (
            dates_eod[period_indices] - period_start
        )
        front_stub_fraction[period_indices] = (
            front_stub_day_count[period_indices] / period_length.astype(int)
            + last_fraction
        )

        day_count_fraction = numpy.where(
            front_stub_indices, front_stub_fraction, day_count_fraction
        )

    # Adjust for back stub
    if any(back_notional_dates):
        back_stub_indices = (dates <= numpy.datetime64(maturity)) & (
            dates >= back_notional_dates[0]
        )
        back_stub_day_count = numpy.zeros_like(day_count)
        back_stub_fraction = numpy.zeros_like(day_count_fraction)

        # Calculate the back stub fraction over multiple periods, to nsure accumulation to do
        last_fraction = 0

        # Long Back Stubs
        for i in range(len(back_notional_dates) - 2):
            period_start = back_notional_dates[i]
            period_end = back_notional_dates[i + 1]
            period_length = period_end - period_start
            period_indices = (dates >= period_start) & (dates < period_end)
            back_stub_day_count[period_indices] = (
                dates_eod[period_indices] - period_start
            )
            back_stub_fraction[period_indices] = (
                back_stub_day_count[period_indices] / period_length.astype(int)
            ) + last_fraction
            last_fraction = back_stub_fraction[period_indices][-1]

        # Short back stubs
        period_start = back_notional_dates[-2]
        period_end = back_notional_dates[-1]
        maturity_date = numpy.datetime64(
            f"{maturity[:4]}-{maturity[4:6]}-{maturity[6:]}"
        )
        period_length = period_end - period_start
        period_indices = (dates >= period_start) & (dates < maturity_date)
        back_stub_day_count[period_indices] = (
            dates_eod[period_indices] - period_start
        )
        back_stub_fraction[period_indices] = (
            back_stub_day_count[period_indices] / period_length.astype(int)
            + last_fraction
        )

        day_count_fraction = numpy.where(
            back_stub_indices, back_stub_fraction, day_count_fraction
        )

    if interest_pays_at_maturity:
        period_index_series = get_coupon_period_indices(dates, coupons)
        day_count_fraction += period_index_series

    return dates, day_count_fraction


AI_RULES = {
    "a": gen_actact,
    "3": "30_360_us",
    "5": "30_360_us",
    "b": gen_act365,
    "c": gen_act360,
}


def gen_floating_ai(sec, rates):
    start = sec["issue_date"]
    maturity = sec["maturity_date"]
    first_coupon = datetime.datetime.strptime(
        sec["first_coupon_date"], ISO_DATE
    )
    last_coupon = (
        datetime.datetime.strptime(sec["last_coupon_date"], ISO_DATE)
        if sec["last_coupon_date"]
        else None
    )

    enforce_monthend = (  # Did not relax this cos there was no need
        calendar.is_monthend(first_coupon)
        and (
            calendar.is_monthend(
                datetime.datetime.strptime(maturity, ISO_DATE)
            )
            or (last_coupon and calendar.is_monthend(last_coupon))
        )
        and sec["pay_month_end"]
    )
    freq = int(sec["vrs_freq"]) if sec["vrs_rule"] == "7" else 12
    cdates = gen_cdates_for_year(
        sec["first_coupon_date"].replace("-", ""), freq, enforce_monthend
    )
    denominator = FLOATING_AI_DENOM.get(sec["calendar_code"])
    if sec["vrs_rule"] == "7":
        dates, coupons = base_series(
            start.replace("-", ""),
            maturity.replace("-", ""),
            freq,
            cdates,
            first_coupon,
        )
    else:
        dates = numpy.arange(start, maturity, dtype="datetime64[D]")
        if sec["vrs_rule"] == "12" and sec["vrs_freq"] == "3":
            coupons = calendar.get_nth_dow(start, maturity, 1, "Thu")
        elif sec["vrs_rule"] == "13" and sec["vrs_freq"] == "14":
            coupons = calendar.get_nth_day(start, maturity, 15)
        elif sec["vrs_rule"] == "14":
            coupons = calendar.get_nth_busday(
                start, maturity, int(sec["vrs_freq"]) + 1
            )
        coupons[coupons < first_coupon.date()] = coupons[0]

    # adjust for holidays
    if not sec["vrs_holiday_rule"] or sec["vrs_holiday_rule"] == "x":
        delayed_coupons = calendar.ensure_busday(coupons)
    elif sec["vrs_holiday_rule"] == "u":
        delayed_coupons = coupons
    else:
        delayed_coupons = calendar.ensure_busday(coupons, direction="backward")

    years = ai.as_years(dates)
    is_leap = (years % 400 == 0) | ((years % 4 == 0) & (years % 100 > 0))

    # accrual numerator
    numerator = numpy.full(len(dates), 1)
    if sec["calendar_code"] in ("3", "5"):
        numerator[(ai.as_months(dates) == 2) & (ai.as_days(dates) == 29)] = 2
        numerator[ai.as_days(dates) == 31] = 0
        numerator[
            (~is_leap) & (ai.as_months(dates) == 2) & (ai.as_days(dates) == 28)
        ] = 3

    # accrual denominator
    if not denominator and sec["vrs_rule"] in {"12", "13", "14"}:
        denominator = numpy.full(len(dates), 365)
        denominator[is_leap] = 366
        denominator = denominator / freq
    elif denominator:
        denominator = denominator / freq
    else:
        unique_coupons = numpy.concatenate((coupons, [dates[-1] + 1]))
        coupon_periods = numpy.diff(unique_coupons)
        denominator = numpy.zeros(len(dates))
        denominator[numpy.searchsorted(dates, delayed_coupons)] = (
            coupon_periods
        )
        denominator = tseries.ffill(denominator)

    # rates
    rates_dt, rates_rate = zip(*rates)
    rates_dt = numpy.array(rates_dt, dtype="datetime64[D]")[0]
    rates_rate = rates_rate[0]
    rate_crop_idx = numpy.searchsorted(rates_dt, dates[-1])
    if rates_dt[0] > dates[0]:
        # the dates before first rate is 0 so just limit that range
        start_idx = numpy.searchsorted(dates, rates_dt[0]) - 1
        dates = dates[start_idx:]
        numerator = numerator[start_idx:]
        if isinstance(denominator, numpy.ndarray):
            denominator = denominator[start_idx:]
    rates = numpy.zeros(len(dates))
    rates[numpy.searchsorted(dates, rates_dt[:rate_crop_idx])] = rates_rate[
        :rate_crop_idx
    ]
    rates = tseries.ffill(rates)

    # cumsum and reset each coupon
    values = numpy.cumsum(numerator / denominator * rates / freq)
    reset_values = numpy.zeros(len(values))
    coupon_indices = numpy.searchsorted(dates, delayed_coupons)
    # ignore first coupon and coupons past maturity
    coupon_indices = coupon_indices[
        slice(*numpy.searchsorted(coupon_indices, [1, len(dates)]))
    ]
    reset_values[coupon_indices] = values[numpy.maximum(coupon_indices - 1, 0)]
    reset_values = tseries.ffill(reset_values)
    values -= reset_values

    dates, values = backfill_ai(dates, values)
    dates, values = ffill_prerefunded_date(
        dates, values, sec["prerefund_date"]
    )
    return dates, values


FLOATING_AI_DENOM = {"b": 365, "3": 360, "5": 360, "c": 360}
