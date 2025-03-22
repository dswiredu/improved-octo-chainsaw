"""Base Engine that supports interacting with PS API."""

import json
import logging
import time
from typing import Dict
import urllib.parse as url_parse

from drf_client.connection import Api as RestApi
from drf_client.connection import RestResource
from drf_client.exceptions import HttpClientError
from drf_client.helpers.base_main import BaseMain
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class D1G1TPSRestResource(RestResource):
    """d1g1t custom rest resource."""

    def get_options(self):
        """Overwrite to use SET_DASHES=True."""
        options = super().get_options()
        options["USE_DASHES"] = True
        return options

    def post(self, data=None, **kwargs):
        """Overwrite RestResource 'post' method to handle d1g1t 202 'waiting' response status."""
        if data:
            payload = json.dumps(data)
        else:
            payload = None

        url = self.url()
        headrs = self._get_headers()
        resp = requests.post(url, data=payload, headers=headrs)

        counter = 200
        while resp.status_code in [202, 502] and counter > 0:
            time.sleep(3)
            resp = requests.post(url, data=payload, headers=headrs)
            counter -= 1

        return self._process_response(resp)

class D1g1tApi(RestApi):
    """d1g1t custom rest api."""

    def _get_resource(self, **kwargs):
        """Overwrite to use custom D1g1tResource class."""
        return D1G1TPSRestResource(**kwargs)


class PSMain(BaseMain):
    """
    A D1G1T wrapper around django-rest-framework-client BaseMain.

    Use D1G1TPSApi to handle d1g1t waiting response.
    """

    PAGE_SIZE: int = 1000

    payload: Dict = {
        "data": {
            "pagination": {
                "parent_path": "root",
                "offset": 0,
                "size": 200,
            }
        }
    }

    def main(self):
        """Overwrite main in BaseMain to use D1g1tApi."""
        self.domain = self.get_domain()
        self.options["DOMAIN"] = self.domain
        self.api = D1g1tApi(self.get_options())
        self.before_login()
        ok = self.login()
        if ok:
            self.after_login()
        else:
            raise HttpClientError("Your login attempt was unsuccessful!")

    @staticmethod
    def add_items(map_obj: Dict, items: Dict) -> None:
        """Add items to a mapped object."""
        for item in items:
            map_obj[item["id"]] = {
                category["category_id"]: category["value"]
                for category in item["data"]
                if "value" in category
            }

    @staticmethod
    def get_offset(response: dict) -> int:
        """Get offset from response object."""
        if "next" in response:
            next_url = response["next"]
            offset = url_parse.urlparse(next_url).query
        else:
            offset = response.get("next_offset")
        return offset

    @staticmethod
    def set_offset(offset, payload, filters=""):
        """Set pagination offset."""
        if isinstance(offset, int):
            payload["data"]["pagination"]["offset"] = offset
        else:
            payload["extra"] = "&".join(filter(None, (offset, filters)))

    @staticmethod
    def get_count(response: dict) -> int:
        """Get count from a response object."""
        return response.get("count", 0)

    def paginate(
        self, api, payload=None, method="post", result_key="items", filters=""
    ):
        """Set pagination."""
        if not payload:
            payload = self.payload

        # set initial page size / offset
        payload["data"]["pagination"]["size"] = self.PAGE_SIZE
        self.set_offset(
            payload=payload, offset=f"limit={self.PAGE_SIZE}", filters=filters
        )

        url_path = url_parse.urlparse(api.url()).path
        resp = getattr(api, method)(**payload)
        count = self.get_count(resp)
        offset = self.get_offset(resp)
        logger.debug(
            f"Total {url_path}: count={count}, offset={offset}, num_results={len(resp.get(result_key))}"
        )
        yield resp.get(result_key, [])

        while offset:
            self.set_offset(payload=payload, offset=offset)
            resp = getattr(api, method)(**payload)
            offset = self.get_offset(resp)
            logger.debug(
                f"Total {url_path}: count={count}, offset={offset}, num_results={len(resp.get(result_key))}"
            )
            yield resp.get(result_key, [])

    def get_calculation(self, calc_string: str, payload: dict):
        """
        Return a json calculation result.

        :param: <calc_string> in <API_DOMAIN>/api/v1/calc/<calc_string> eg 'trend-aum', 'present-exposure'
        :param: payload: Calculation payload (json)
        :returns: json response object.

        See https://github.com/d1g1tinc/python-services/blob/72fcfb8742835c1dec075afff59627580d630bf2/
        src/d1g1t/maestro/calculations/constants.py#L98 for all avaialble calc_strings
        """
        calc_call = self.api.calc(calc_string)
        response = calc_call.post(data=payload)
        if not response:
            raise ValueError("Request returned no result!")
        return response

    def get_data(self, data_type) -> pd.DataFrame:
        """
        Return a response object as a DataFrame given data type.

        :param data_type: eg. 'households','investment-mandate',etc
        :returns: json response object or dataframe

        See https://api-rc.d1g1tdev.com/api/v1/data/ for all data api endpoints!
        """
        dfs = []
        resource = getattr(self.api.data, data_type)
        for items in self.paginate(
            resource, method="get", result_key="results"
        ):
            df = pd.DataFrame(items)
            dfs.append(df)
        return pd.concat(dfs)

    def get_fx_data(self,fx_params: dict):
        extra_url = '?base=' + fx_params['base'] + '&foreign=' + fx_params['foreign'] + '&date=' + fx_params['date']
        resource = getattr(self.api, "fxrates")
        response = getattr(resource, "get")(extra = extra_url)
        fx_rate = 1
        try:
            fx_rate = response["results"][0]["close"]
        except:
            raise ValueError("No FX Rate for the date provided")
        return fx_rate
