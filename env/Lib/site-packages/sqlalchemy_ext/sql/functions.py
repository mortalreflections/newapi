# -*- coding: utf-8 -*-

from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.types import DateTime


# https://stackoverflow.com/questions/7075828/make-sqlalchemy-use-date-in-filter-using-postgresql
class convert_tz(GenericFunction):
    """
    Sqlalchemy shortcut to SQL convert timezone function

    :param DateTime datetime
    :param str from_tz: The timezone the datetime will be converted from
    :param str to_tz: The timezone the datetime will be converted from
    :returns: Datetime in another timezone
    :rtype: DateTime or None if timezones are invalid
    """
    type = DateTime
