from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting._forecast_parameter_base import (
    ForecastParameterBase,
)


class OGDLocalForecastingSre000h0(ForecastParameterBase):
    __tablename__ = "tbl_ogd-local-forecasting-sre000h0"

    value: Mapped[float] = mapped_column(Integer)
