import logging
from abc import ABC, abstractmethod
import pandas as pd

logger = logging.getLogger(__name__)


class D1g1tClient(ABC):
    def __init__(self, firm: str, client: str) -> None:
        self.firm = firm
        self.client = client

    @abstractmethod
    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        """Implements firm-specific logic for processed d1g1t data
        :param: d1g1t_df: processed d1g1t data
        """
        return d1g1t_df

    @abstractmethod
    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Implements firm-specific logic for processed custodians data
        :param: custodian: custodian name since there may be seperate logic for each custodians
        :param: custodian_df: processed d1g1t data
        """
        return custodian_df

    @abstractmethod
    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Implements client-specific recon prost-processing logic after recon is complete.
        :param: df: processed recon frame
        """
        return df
