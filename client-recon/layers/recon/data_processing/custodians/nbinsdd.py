import pandas as pd
import logging
from datetime import datetime
from pandas.tseries.offsets import BusinessDay

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class NBINSDD(Custodian):
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

        nbin_client_short_map = {
            "bloomridge": "BLMCP",
            "bloomridge-b": "Q2KO",
            "granite": "GRNAM",
            "ginsler-a": "A45R",
            "ginsler-b": "A45B",
            "ginsler-c": "A6SD",
            "medici": "MEDI",
            "medici-b": "GDPMD",
            "omg": "OMGWM",
            "sunlife": "SUNLF",
            "stewardship-a": "A46R",
            "stewardship-b": "A46P",
        }
        self.client_short = nbin_client_short_map[feed]
        self.client = client
        self.currency_map = self.get_currency_map
        self.nbinsdd_position_cols = {
            "A/C ID": "account",
            "TI Alternate ID": "instrument",
            "Tran Summ Trade Qty": "custodian_units",
            "Tran Summ Curr Mkt Value": "custodian_mv_clean_ac_cad_usd",
            "B/V Security Position Val": "custodian_bv_ac_cad_usd",
        }
        self.nbinsdd_cash_cols = {
            "A/C ID": "account",
            "A/C Summ TD Net Amt": "custodian_units",
        }
        self.feed = feed

    def get_feed_file(self, nbin_dte: str, file_type: str):
        if self.client == "omg":
            feed_path = "d1g1t-custodian-data-ca/nbin"
        else:
            feed_path = "d1g1t-nbin-custodian-data-ca-central-1"
        file = f"s3://{feed_path}/{self.feed}/{nbin_dte}/{file_type}.CSV"
        return file

    @property
    def get_currency_map(self) -> dict:
        file_date = DateUtils.get_custodian_date(datetime.today() - BusinessDay(1))
        client_file = f"{self.client_short}ACT01"
        feed_file = self.get_feed_file(file_date, client_file)
        df = pd.read_csv(
            feed_file,
            index_col="A/C ID",
            encoding="ISO-8859-1",
            dtype=str,
        )
        df.index = df.index.str.strip()
        res = self.currency_map_to_dict(df)
        return res

    @staticmethod
    def currency_map_to_dict(df: pd.DataFrame) -> dict:
        return df.to_dict()["A/C Currency"]

    def get_cash_currency(self, df: pd.DataFrame) -> pd.Series:
        """df: custodian dataframe
        Missing secids represent cash in the account.
        Map all missing secIDs to a currency based on the account name
        in currency map lookup"""

        res = df["stripped_instrument"].copy()
        iscash_idx = df["stripped_instrument"].isna()
        accounts = df["account"].str.strip()
        res.loc[iscash_idx] = accounts.map(self.currency_map)
        return res

    @staticmethod
    def process_cash_amounts_adhoc(df: pd.DataFrame) -> pd.Series:
        iscash_idx = df["instrument"].isin(["CAD", "USD"])
        res = df["custodian_units"].copy()
        res.loc[iscash_idx] = df["custodian_units"] * -1
        bv_cash_adj = df["custodian_bv_ac_cad_usd"].copy()
        bv_cash_adj.loc[iscash_idx] = res.loc[iscash_idx]
        mv_clean_cash_adj = df["custodian_mv_clean_ac_cad_usd"].copy()
        mv_clean_cash_adj.loc[iscash_idx] = res.loc[iscash_idx]
        return res, bv_cash_adj, mv_clean_cash_adj

    def read_feed_file(self, nbin_dte, file_type: str) -> pd.DataFrame:
        client_file = f"{self.client_short}{file_type}"
        s3_file = self.get_feed_file(nbin_dte, client_file)
        try:
            df = pd.read_csv(s3_file, encoding="ISO-8859-1")
        except FileNotFoundError:
            msg = f"No data found for {self.firm}'s {file_type} file!"
            raise ClientDataNotFoundException(msg)
        if file_type in ["PSN01", "POS01"]:
            df = df[self.nbinsdd_position_cols.keys()]
            df = df.rename(columns=self.nbinsdd_position_cols)
            df["instrument"] = df["instrument"].astype(str)

            # check for PSN02, if available, read and merge into df
            if file_type == "PSN01":
                client_file2 = f"{self.client_short}PSN02"
            elif file_type == "POS01":
                client_file2 = f"{self.client_short}POS02"
            s3_file_2 = self.get_feed_file(nbin_dte, client_file2)
            try:
                df2 = pd.read_csv(s3_file_2, encoding="ISO-8859-1")
                df2 = df2[self.nbinsdd_position_cols.keys()]
                df2 = df2.rename(columns=self.nbinsdd_position_cols)
                df2["instrument"] = df2["instrument"].astype(str)
                df = pd.concat([df, df2])
            except FileNotFoundError:
                msg = f"No data found for {self.firm}'s PSN02 file!"
        else:
            df = df[self.nbinsdd_cash_cols.keys()]
            df = df.rename(columns=self.nbinsdd_cash_cols)
        return df

    def read_data(self, dte: str) -> pd.DataFrame:
        recon_dte = DateUtils().get_recon_date(dte)
        nbin_dte = DateUtils.get_custodian_date(recon_dte)

        if self.client == "omg":
            positions = self.read_feed_file(nbin_dte, "POS01")
        else:
            positions = self.read_feed_file(nbin_dte, "PSN01")
        cash = self.read_feed_file(nbin_dte, "VAL01")

        df = pd.concat([positions, cash], axis=0, ignore_index=True)

        df["date"] = pd.to_datetime(nbin_dte)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["account"] = df["account"].str.strip()
        df["stripped_instrument"] = df["instrument"].str.strip()
        df["instrument"] = self.get_cash_currency(df)
        (
            df["custodian_units"],
            df["custodian_bv_ac_cad_usd"],
            df["custodian_mv_clean_ac_cad_usd"],
        ) = self.process_cash_amounts_adhoc(df)
        # Remember to undo this if we start pulling price from custodian
        df = df.groupby(["date", "account", "instrument"]).sum().reset_index()
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
