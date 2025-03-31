from datetime import datetime

import pandas.tseries.holiday as pdh
from pandas.tseries.offsets import CustomBusinessDay
from layers.recon.exceptions import InputValidationException


# CA holidays: 2021
# --------------------------
# (datetime.date(2021, 1, 1), "New Year's Day")
# (datetime.date(2021, 2, 15), 'Family Day')
# (datetime.date(2021, 4, 2), 'Good Friday')
# (datetime.date(2021, 5, 24), 'Victoria Day')
# (datetime.date(2021, 7, 1), 'Canada Day')
# (datetime.date(2021, 8, 2), 'Civic pdh.Holiday')
# (datetime.date(2021, 9, 6), 'Labour Day')
# (datetime.date(2021, 10, 11), 'Thanksgiving')
# (datetime.date(2021, 12, 25), 'Christmas Day')
# (datetime.date(2021, 12, 24), 'Christmas Day (Observed)')
# (datetime.date(2021, 12, 27), 'Boxing Day (Observed)')
# (datetime.date(2021, 12, 31), "New Year's Day (Observed)")


# Observance rules
# ---------------------------
class CanadianBusinessCalendar(pdh.AbstractHolidayCalendar):
    rules = [
        pdh.Holiday("New Year's Day", month=1, day=1, observance=pdh.sunday_to_monday),
        pdh.Holiday("Family Day", month=2, day=15, observance=pdh.nearest_workday),
        pdh.Holiday("Good Friday", month=4, day=2, offset=[pdh.Easter(), pdh.Day(-2)]),
        pdh.Holiday("Victoria Day", month=5, day=24, observance=pdh.nearest_workday),
        pdh.Holiday("Canada Day", month=7, day=1, observance=pdh.nearest_workday),
        pdh.Holiday("Civic Holiday", month=8, day=2, observance=pdh.nearest_workday),
        pdh.Holiday("Labour Day", month=9, day=9, observance=pdh.nearest_workday),
        pdh.Holiday("Thanksgiving", month=10, day=11, observance=pdh.nearest_workday),
        pdh.Holiday("Christmas Day", month=12, day=25, observance=pdh.nearest_workday),
        pdh.Holiday("Boxing Day", month=12, day=26, observance=pdh.nearest_workday),
    ]


STD_DATE_FORMAT = "%Y-%m-%d"
SHRT_DATE_FORMAT = "%Y%m%d"
HM_DATE_FORMAT = "%H%M"


class DateUtils:
    @staticmethod
    def get_last_cob_date(dt=datetime.today()):
        cob_dt = dt - CustomBusinessDay(calendar=CanadianBusinessCalendar())
        return cob_dt

    @staticmethod
    def get_last_n_cob_date(dt=datetime.today(), n=1):
        cob_dt = dt - CustomBusinessDay(n, calendar=CanadianBusinessCalendar())
        return cob_dt

    @staticmethod
    def is_valid_date_input(date_string: str, valid_format=STD_DATE_FORMAT) -> bool:
        try:
            datetime.strptime(date_string, valid_format)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def get_custodian_date(dt):
        return dt.strftime(SHRT_DATE_FORMAT)

    def get_recon_date(self, dte: str, n=1):
        if dte == self.get_last_cob_date().strftime(STD_DATE_FORMAT):
            today = datetime.strptime(
                self.get_last_n_cob_date(datetime.today(), n).strftime(STD_DATE_FORMAT),
                STD_DATE_FORMAT,
            )
        else:
            if self.is_valid_date_input(dte):
                today = datetime.strptime(dte, STD_DATE_FORMAT)
            else:
                message = f"The input {dte} is incorrect! Expected {STD_DATE_FORMAT}"
                raise InputValidationException(message)
        return today
