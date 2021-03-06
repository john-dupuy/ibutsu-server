# coding: utf-8
from __future__ import absolute_import

from ibutsu_server import util
from ibutsu_server.models.base_model_ import Model


class ReportParameters(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, type=None, filter=None, source=None):  # noqa: E501
        """ReportParameters - a model defined in OpenAPI

        :param type: The type of this ReportParameters.  # noqa: E501
        :type type: str
        :param filter: The filter of this ReportParameters.  # noqa: E501
        :type filter: str
        :param source: The source of this ReportParameters.  # noqa: E501
        :type source: str
        """
        self.openapi_types = {"type": str, "filter": str, "source": str}

        self.attribute_map = {"type": "type", "filter": "filter", "source": "source"}

        self._type = type
        self._filter = filter
        self._source = source

    @classmethod
    def from_dict(cls, dikt) -> "ReportParameters":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ReportParameters of this ReportParameters.  # noqa: E501
        :rtype: ReportParameters
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        """Gets the type of this ReportParameters.

        The type of report to generate  # noqa: E501

        :return: The type of this ReportParameters.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this ReportParameters.

        The type of report to generate  # noqa: E501

        :param type: The type of this ReportParameters.
        :type type: str
        """

        self._type = type

    @property
    def filter(self):
        """Gets the filter of this ReportParameters.

        A regular expression to filter test results by  # noqa: E501

        :return: The filter of this ReportParameters.
        :rtype: str
        """
        return self._filter

    @filter.setter
    def filter(self, filter):
        """Sets the filter of this ReportParameters.

        A regular expression to filter test results by  # noqa: E501

        :param filter: The filter of this ReportParameters.
        :type filter: str
        """

        self._filter = filter

    @property
    def source(self):
        """Gets the source of this ReportParameters.

        The source of the test results  # noqa: E501

        :return: The source of this ReportParameters.
        :rtype: str
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this ReportParameters.

        The source of the test results  # noqa: E501

        :param source: The source of this ReportParameters.
        :type source: str
        """

        self._source = source
