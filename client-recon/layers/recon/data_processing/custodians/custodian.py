import logging
from abc import ABC, abstractmethod
import pandas as pd

import layers.recon.data_processing.d1g1t_clients as dc
from layers.recon.exceptions import FirmSpecificLogicException

logger = logging.getLogger(__name__)


class Custodian(ABC):
    def __init__(
        self,
        firm: str,
        client: str,
        custodian: str,
        feed: str,
        region: str,
        metrics: list,
    ) -> None:
        self.firm = firm
        self.client = client
        self.feed = feed
        self.region = region
        self.custodian = custodian.lower()
        self.feed_path = self.get_feed_path
        self.metrics = metrics

    @property
    def get_feed_path(self) -> str:
        return f"s3://d1g1t-custodian-data-{self.region}/{self.custodian}/{self.feed}"

    @property
    def custodian_return_cols(self) -> list:
        position_cols = ["date", "account", "instrument"]
        metric_cols = [f"custodian_{metric}" for metric in self.metrics]
        return position_cols + metric_cols

    @abstractmethod
    def read_data(self, dte: str) -> pd.DataFrame:
        """Implements retrieval of custodian data from s3
        :param: dte: date string representing dated bucket where data is read.
        """
        pass

    @abstractmethod
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        custodian data wrangling logic
        :param: df: Raw custodian dataframe
        """
        pass

    @abstractmethod
    def get_custdn_data(self, dte: str) -> pd.DataFrame:
        """
        Implements retrieval and processing of custodian data.
        :param: dte: Date string representing date on which custodian data is retireved.
        """
        pass

    def apply_firm_specific_logic(self, df: pd.DataFrame):
        res = df.copy()
        try:
            cls = getattr(dc, self.firm.title())
            client_instance = cls(self.firm, self.client)
            res = client_instance.apply_firm_specific_custodian_logic(
                self.custodian, df
            )
            return res
        except AttributeError:
            msg = (
                f"No firm-specific logic found for {self.firm} at the custodian level."
            )
            logger.info(msg)
            return res
        except Exception as e:
            msg = f"Could not apply {self.firm}-specific logic to {self.custodian} custodian data due to error: {e}"
            raise FirmSpecificLogicException(msg)
