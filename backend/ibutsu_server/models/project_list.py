# coding: utf-8
from __future__ import absolute_import

from typing import List

from ibutsu_server import util
from ibutsu_server.models.base_model_ import Model
from ibutsu_server.models.pagination import Pagination
from ibutsu_server.models.project import Project


class ProjectList(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, projects=None, pagination=None):  # noqa: E501
        """ProjectList - a model defined in OpenAPI

        :param projects: The projects of this ProjectList.  # noqa: E501
        :type projects: List[Project]
        :param pagination: The pagination of this ProjectList.  # noqa: E501
        :type pagination: Pagination
        """
        self.openapi_types = {"projects": List[Project], "pagination": Pagination}

        self.attribute_map = {"projects": "projects", "pagination": "pagination"}

        self._projects = projects
        self._pagination = pagination

    @classmethod
    def from_dict(cls, dikt) -> "ProjectList":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ProjectList of this ProjectList.  # noqa: E501
        :rtype: ProjectList
        """
        return util.deserialize_model(dikt, cls)

    @property
    def projects(self):
        """Gets the projects of this ProjectList.


        :return: The projects of this ProjectList.
        :rtype: List[Project]
        """
        return self._projects

    @projects.setter
    def projects(self, projects):
        """Sets the projects of this ProjectList.


        :param projects: The projects of this ProjectList.
        :type projects: List[Project]
        """

        self._projects = projects

    @property
    def pagination(self):
        """Gets the pagination of this ProjectList.


        :return: The pagination of this ProjectList.
        :rtype: Pagination
        """
        return self._pagination

    @pagination.setter
    def pagination(self, pagination):
        """Sets the pagination of this ProjectList.


        :param pagination: The pagination of this ProjectList.
        :type pagination: Pagination
        """

        self._pagination = pagination
