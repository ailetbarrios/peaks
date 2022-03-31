from datetime import datetime

import self as self

class Peak:
    # _from_date: str
    # _to_date: str
    # _load: float
    # _pv: float
    # _price: float
    # _emission: float

    def __init__(self):
        self._from_date = ''
        self._to_date = ''
        self._price = 0.0
        self._emission = 0.0
        self._pv = 0.0
        self._load = 0.0

    @property
    def from_date(self):
        return self._from_date

    @from_date.setter
    def from_date(self, value):
        self._from_date = value

    @property
    def to_date(self):
        return self._to_date

    @to_date.setter
    def to_date(self, value):
        self._to_date = value

    @property
    def load(self):
        return self._load

    @load.setter
    def load(self, value):
        self._load = value

    @property
    def pv(self):
        return self._pv

    @pv.setter
    def pv(self, value):
        self._pv = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = value

    @property
    def emission(self):
        return self._emission

    @emission.setter
    def emission(self, value):
        self._emission = value

    def __str__(self):
        return "  fromDate: " +self._from_date + "  toDate: " + self._to_date + "  price: " + str(self._price) + "  emission: " + str(
            self._emission) + "  pv: " + str(self._pv) + "  load: " + str(self._load)
