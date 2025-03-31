import pandas as pd
import logging

from datetime import datetime
from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU

logger = logging.getLogger(__name__)


class TripleA(Custodian):
    def __init__(
        self,
        firm: str,
        client: str,
        custodian: str,
        feed: str,
        region: str,
        metrics: list,
    ) -> None:
        super().__init__(firm, client, custodian, feed, region, metrics)
        self.triplea_holdings_cols = {
            "instr_symb": "Instrument Symbol",
            "instr_name": "Instrument Name",
            "nature": "Nature",
            "instr_currency": "Instrument Curr",
            "price_currency": "Price Curr",
            "quote_date": "Price Date",
            "accrued_interest": "custodian_ai",
            "portfolio_name": "Portfolio Name",
            "ips_code": "IPS_Code",
            "ips_name": "IPS_Name",
            "pcm_code": "IC_Code",
            "pcm_name": "IC_Name",
            "advisor_code": "Advisor_Code",
            "advisor_name": "Advisor_Name",
            "company": "Company",
            "pos_exch_rate": "Pos_FX_Rate",
        }

    def lookup_triplea_date(self, triplea_dte):
        res = triplea_dte
        date_timestamp = datetime.strptime(triplea_dte, "%Y%m%d")
        if date_timestamp.weekday() == 6:
            triplea_dte_timestamp = dtU.get_last_cob_date(date_timestamp)
            res = dtU.get_custodian_date(triplea_dte_timestamp)
        return res

    def read_data(self, dte):
        recon_dte = dtU().get_recon_date(dte)
        triplea_dte = dtU.get_custodian_date(recon_dte)
        triplea_dte = self.lookup_triplea_date(triplea_dte)
        data_pos = self.read_data_pos(triplea_dte)
        data_fx = self.read_data_fx(triplea_dte)
        return data_pos, data_fx

    def read_data_pos(self, dte):
        position_file = f"{self.feed_path}/{dte}/POSITIONS_B1.txt"
        position_data = pd.read_csv(
            position_file,
            sep="|",
            parse_dates=["calc_from_date", "quote_date"],
            dtype={"quantity": float, "portfolio": str, "instrument": str},
            encoding="ISO-8859-1",
        )
        return position_data

    def processing_fx(self, position_data, fx_data):
        ci_positions_with_fx = position_data.merge(
            fx_data[["Currency", "CAD_fx_rate"]],
            left_on=["Instrument Curr"],
            right_on=["Currency"],
            how="left",
        )
        ci_positions_with_fx = ci_positions_with_fx.rename(
            columns={"CAD_fx_rate": "CAD_fx_rate_x"}
        )
        ci_positions_with_fx = ci_positions_with_fx.merge(
            fx_data[["Currency", "CAD_fx_rate_aux"]],
            left_on=["Price Curr"],
            right_on=["Currency"],
            how="left",
        )
        # ci_positions_with_fx = ci_positions_with_fx.rename(columns={'CAD_fx_rate':'CAD_fx_rate_x'})
        ci_positions_with_fx["CAD_fx_rate"] = ci_positions_with_fx[
            "CAD_fx_rate_x"
        ].fillna(1)
        ci_positions_with_fx["CAD_fx_rate"] = ci_positions_with_fx[
            "CAD_fx_rate_x"
        ].where(ci_positions_with_fx["Instrument Curr"] != "CAD", other=1)
        ci_positions_with_fx["CAD_fx_rate"] = ci_positions_with_fx["CAD_fx_rate"].where(
            (ci_positions_with_fx["Instrument Curr"] != "CAD")
            | (ci_positions_with_fx["Price Curr"] == "CAD"),
            other=ci_positions_with_fx["CAD_fx_rate_aux"],
        )
        ci_positions_with_fx.loc[:, "CAD_fx_rate"] = ci_positions_with_fx[
            "CAD_fx_rate_x"
        ].replace(0, 1, regex=True)
        ci_positions_with_fx.loc[:, "CAD_fx_rate"] = ci_positions_with_fx[
            "CAD_fx_rate_x"
        ].fillna(1)
        return ci_positions_with_fx

    def read_data_fx(self, dte):
        fx_file = f"{self.feed_path}/{dte}/FX_RATE_B1.txt"
        fx_data = pd.read_csv(fx_file, sep="|", parse_dates=["Date"])
        fx_data["CAD_fx_rate_aux"] = fx_data["CAD_fx_rate"]
        return fx_data

    def process_data(self, triplea_raw_pos, triplea_fx_data):
        triplea_raw_pos.fillna(0, inplace=True)
        triplea_raw_pos["Stale Price"] = (
            triplea_raw_pos["instr_currency"] != triplea_raw_pos["price_currency"]
        ) & (triplea_raw_pos["quote_date"] != triplea_raw_pos["calc_from_date"])
        triplea_raw_pos["instrument"] = triplea_raw_pos["instrument"].str.replace(
            r"\.", "-", regex=True
        )

        triplea_raw_pos = triplea_raw_pos.rename(columns=self.triplea_holdings_cols)
        triplea_raw_pos["calc_from_date"] = pd.to_datetime(
            triplea_raw_pos["calc_from_date"], errors="coerce"
        )
        triplea_raw_pos["Price Date"] = pd.to_datetime(
            triplea_raw_pos["Price Date"], errors="coerce"
        )
        triplea_raw_pos[["calc_from_date", "Price Date"]] = triplea_raw_pos[
            ["calc_from_date", "Price Date"]
        ].fillna(pd.NaT)

        triplea_raw_pos = (
            triplea_raw_pos.groupby(
                [
                    "portfolio",
                    "instrument",
                    "price",
                    "Pos_FX_Rate",
                    "calc_from_date",
                    "Instrument Symbol",
                    "Instrument Name",
                    "Nature",
                    "Instrument Curr",
                    "Price Curr",
                    "Price Date",
                    "Portfolio Name",
                    "IPS_Code",
                    "IPS_Name",
                    "IC_Code",
                    "IC_Name",
                    "Advisor_Code",
                    "Advisor_Name",
                    "Company",
                ]
            )
            .sum()
            .reset_index()
        )

        final_ci_data = self.processing_fx(triplea_raw_pos, triplea_fx_data)
        final_ci_data.loc[
            final_ci_data["Instrument Curr"] != final_ci_data["Price Curr"], "price"
        ] = (final_ci_data["price"] * final_ci_data["CAD_fx_rate"])
        final_ci_data.rename(
            columns={
                "portfolio": "account",
                "quantity": "custodian_units",
                "calc_from_date": "date",
                "price": "custodian_price",
                "market_value_cad": "custodian_mv_dirty",
            },
            inplace=True,
        )
        final_ci_data = final_ci_data.astype(
            {"custodian_units": float, "account": str, "instrument": str}
        )
        final_ci_data.drop(columns=["custodian"], inplace=True)
        return final_ci_data

    def get_custdn_data(self, dte) -> pd.DataFrame:
        pos, fx = self.read_data(dte)
        res = self.process_data(pos, fx)
        return res
