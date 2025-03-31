class FirmNotConfiguredException(Exception):
    """class to handle missing firm input exceptions"""

    pass


class CustodianFeedException(Exception):
    """class to handle missing cutodian setup in custodian_setup.py"""

    pass


class CustodianMetricException(Exception):
    """class to handle missing custodian metric configurations"""

    pass


class ClientDataNotFoundException(Exception):
    """Class to handle missing client data exceptions"""

    pass


class InputValidationException(Exception):
    """Class to handle function input exceptions"""

    pass


class FirmSpecificLogicException(Exception):
    """Class to handle exceptions from applying logic specific to firms"""

    pass


class MissingMetricException(Exception):
    """Class to handle exceptions from missing metrics on the d1g1t side."""

    pass
