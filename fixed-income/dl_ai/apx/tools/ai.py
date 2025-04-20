import calendar
import datetime

import numpy

from tools import tseries
from driver import START_DATE

EOM_DATES = {
    "0131",
    "0228",
    "0229",
    "0331",
    "0430",
    "0531",
    "0630",
    "0731",
    "0831",
    "0930",
    "1031",
    "1130",
    "1231",
}

EOM_SERIES = [
    "0131",
    "0229",
    "0331",
    "0430",
    "0531",
    "0630",
    "0731",
    "0831",
    "0930",
    "1031",
    "1130",
    "1231",
]


def as_years(dates):
    return (
        dates.astype("datetime64[Y]", copy=False).astype(int, copy=False)
        + 1970
    )


def as_months(dates):
    return (
        dates.astype("datetime64[M]", copy=False).astype(int, copy=False) % 12
        + 1
    )


def as_days(dates):
    return (dates - dates.astype("datetime64[M]", copy=False) + 1).astype(
        int, copy=False
    )


def gen_cdates_for_year(cdate, freq):
    """generates coupon dates for a single year given date and freq"""
    init = cdate[4:]
    if freq == 1 or freq == 12:
        return [init]
    else:
        init_date = datetime.datetime.strptime(cdate, "%Y%m%d")
        if (
            init_date.day
            == calendar.monthrange(init_date.year, init_date.month)[1]
        ):
            dates = EOM_SERIES
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


def gen_all_dates(start, maturity):
    """generates complete date series given start/stop)"""
    return numpy.arange(
        start,
        f"{maturity[:4]}-{maturity[4:6]}-{maturity[6:]}",
        dtype="datetime64[D]",
    )


def gen_coupon_dates(start, maturity, freq, cdates, accrue_on_start=True):
    if freq == 0:
        series = numpy.array([], dtype="datetime64[D]")
    elif freq == 12 and cdates[0] in EOM_DATES:
        series = (
            numpy.arange(
                f"{start[:4]}-{start[4:6]}",
                f"{maturity[:4]}-{maturity[4:6]}",
                dtype="datetime64[M]",
            )
            + numpy.timedelta64(1, "M")
        ).astype(dtype="datetime64[D]", copy=False) - numpy.timedelta64(1, "D")
    else:
        if freq == 12:
            cdates = [
                f"{str(month + 1).zfill(2)}{cdates[0][2:]}"
                for month in range(12)
            ]

        gen_cdates = []
        for year in range(int(f"{start[:4]}"), int(f"{maturity[:4]}") + 1):
            for cdate in cdates:
                if f"{year}{cdate[:2]}{cdate[2:]}" >= maturity:
                    continue
                try:
                    gen_cdates.append(
                        datetime.datetime(year, int(cdate[:2]), int(cdate[2:]))
                    )
                except ValueError:
                    # 0230 is a date given by nbin. meh.
                    if cdate in ("0229", "0230", "0231"):
                        gen_cdates.append(datetime.datetime(year, 2, 28))
                    elif cdate.endswith("31"):
                        gen_cdates.append(
                            datetime.datetime(year, int(cdate[:2]), 30)
                        )
                    else:
                        raise ValueError(f"Invalid coupon date: '{cdate}'")
        series = numpy.array(gen_cdates, dtype="datetime64[D]")
    # add coupon on day before start so accrual begins on start date
    starter_coupon = datetime.datetime.strptime(
        start, "%Y%m%d"
    ).date() - datetime.timedelta(days=1 if accrue_on_start else 0)
    return numpy.concatenate(
        (
            numpy.array([starter_coupon], dtype="datetime64[D]"),
            series[series > starter_coupon],
        )
    )


def gen_coupon_dates_for_all_period(
    start, maturity, freq, cdates, accrue_on_start=True
):
    if freq == 0:
        series = numpy.array([], dtype="datetime64[D]")
    elif freq == 12 and cdates[0] in EOM_DATES:
        series = (
            numpy.arange(
                f"{start[:4]}-{start[4:6]}",
                f"{maturity[:4]}-{maturity[4:6]}",
                dtype="datetime64[M]",
            )
            + numpy.timedelta64(1, "M")
        ).astype(dtype="datetime64[D]", copy=False) - numpy.timedelta64(1, "D")
    else:
        if freq == 12:
            cdates = [
                f"{str(month + 1).zfill(2)}{cdates[0][2:]}"
                for month in range(12)
            ]

        gen_cdates = []
        for year in range(int(f"{start[:4]}"), int(f"{maturity[:4]}") + 2):
            for cdate in cdates:
                try:
                    gen_cdates.append(
                        datetime.datetime(year, int(cdate[:2]), int(cdate[2:]))
                    )
                except ValueError:
                    if cdate in ("0229", "0230", "0231"):
                        gen_cdates.append(datetime.datetime(year, 2, 28))
                    elif cdate.endswith("31"):
                        gen_cdates.append(
                            datetime.datetime(year, int(cdate[:2]), 30)
                        )
                    else:
                        raise ValueError(f"Invalid coupon date: '{cdate}'")
        series = numpy.array(gen_cdates, dtype="datetime64[D]")

    return numpy.sort(series)


def calc_notional_dates_for_irregular_periods(
    start, maturity, freq, cdates, first_coupon, last_coupon
):
    coupon_dates = gen_coupon_dates_for_all_period(
        START_DATE, maturity, freq, cdates
    )
    start_date = numpy.datetime64(
        datetime.datetime.strptime(start, "%Y%m%d").date()
    )
    maturity_date = numpy.datetime64(
        datetime.datetime.strptime(maturity, "%Y%m%d").date()
    )
    first_coupon_date = numpy.datetime64(first_coupon.date())
    coupon_dates = coupon_dates[
        (coupon_dates <= coupon_dates[coupon_dates >= maturity_date][0])
    ]

    # Calculate the front notional date range
    if check_if_front_stubs(start_date, first_coupon_date, coupon_dates):
        front_notional_start = coupon_dates[coupon_dates <= start_date][-1]
        front_notional_dates = coupon_dates[
            (coupon_dates >= front_notional_start)
            & (coupon_dates < first_coupon_date)
        ]
    else:
        front_notional_dates = []

    # Calculate the back notional date
    if check_if_back_stubs(maturity_date, coupon_dates):
        if last_coupon:
            last_coupon = numpy.datetime64(last_coupon.date())
            back_notional_start = coupon_dates[coupon_dates >= last_coupon][0]
            back_notional_dates = coupon_dates[
                (coupon_dates >= back_notional_start)
            ]
        else:
            back_notional_start = coupon_dates[coupon_dates < maturity_date][
                -1
            ]
            back_notional_dates = coupon_dates[
                (coupon_dates >= back_notional_start)
            ]
    else:
        back_notional_dates = []

    return front_notional_dates, back_notional_dates


def check_if_front_stubs(start_date, first_coupon_date, coupon_dates):
    filtered_dates = coupon_dates[coupon_dates < first_coupon_date]
    last_date = filtered_dates[-1] if filtered_dates.size > 0 else None
    if (
        start_date < first_coupon_date
        and last_date
        and start_date != last_date
        and start_date >= coupon_dates[0]
    ):
        return True
    else:
        return False


def check_if_back_stubs(maturity_date, coupon_dates):
    last_date = coupon_dates[-1]
    if last_date != maturity_date:
        return True
    else:
        return False


def base_series(start, maturity, freq, cdates):
    all_coupons = gen_coupon_dates(start, maturity, int(freq), sorted(cdates))
    all_dates = gen_all_dates(all_coupons[0], maturity)
    coupon_series = numpy.zeros(len(all_dates))
    coupon_series[numpy.searchsorted(all_dates, all_coupons)] = all_coupons
    coupon_series = tseries.ffill(coupon_series).astype(
        "datetime64[D]", copy=False
    )
    return all_dates, coupon_series


def gen_act360(start, maturity, freq, cdates):
    dates, coupons = base_series(start, maturity, freq, cdates)
    return dates, (dates - coupons).astype(int, copy=False) / 360


def gen_act365(start, maturity, freq, cdates):
    dates, coupons = base_series(start, maturity, freq, cdates)
    return dates, (dates - coupons).astype(int, copy=False) / 365


def gen_30_360(start, maturity, freq, cdates):
    # https://www.isda.org/2008/12/22/30-360-day-count-conventions/ (Eurobond Basis)
    dates, coupons = base_series(start, maturity, freq, cdates)
    values = (
        360 * (as_years(dates) - as_years(coupons))
        + 30 * (as_months(dates) - as_months(coupons))
        + (
            numpy.minimum(as_days(dates), 30)
            - numpy.minimum(as_days(coupons), 30)
        )
    )
    return dates, values / 360


def gen_30_360_isda(start, maturity, freq, cdates):
    # https://www.isda.org/2008/12/22/30-360-day-count-conventions/ (Bond Basis)
    dates, coupons = base_series(start, maturity, freq, cdates)
    d1 = numpy.minimum(as_days(coupons), 30)
    d2 = as_days(dates)
    d2[(d2 == 31) & (d1 == 30)] = 30
    values = (
        360 * (as_years(dates) - as_years(coupons))
        + 30 * (as_months(dates) - as_months(coupons))
        + (d2 - d1)
    )
    return dates, values / 360


def get_actact_denoms(dates):
    denoms = numpy.full_like(dates, 365, dtype=int)
    years = as_years(dates)
    # detect leap years
    denoms[(years % 400 == 0) | ((years % 4 == 0) & (years % 100 > 0))] = 366
    return denoms


def gen_actact(start, maturity, freq, cdates):
    dates, coupons = base_series(start, maturity, freq, cdates)
    denoms = get_actact_denoms(dates)
    return dates, (dates - coupons).astype(int, copy=False) / denoms


def gen_gic(start, maturity, freq, rate):
    sdate = datetime.datetime.strptime(start, "%Y%m%d").date()
    mdate = datetime.datetime.strptime(maturity, "%Y%m%d").date()
    years_diff = mdate.year - sdate.year
    days_diff = (mdate - sdate).days
    dates = gen_all_dates(sdate, maturity)
    values = (
        (dates - dates[0]).astype(int, copy=False) / days_diff
    ) * years_diff
    values = 100 * ((1 + (rate / 100) / freq) ** (freq * values) - 1)
    return dates, values


def gen_couponless_ai(start, maturity, rate):
    sdate = datetime.datetime.strptime(start, "%Y%m%d").date()
    dates = gen_all_dates(sdate, maturity)
    values = (
        dates - numpy.datetime64(sdate).astype(dtype="datetime64[D]")
    ).astype(int)
    return dates, values / 365 * rate
