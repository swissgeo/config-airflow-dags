from sqlalchemy import Float
from sqlalchemy.orm import Mapped, mapped_column

from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting._forecast_parameter_base import (
    ForecastParameterBase,
)


class OGDLocalForecastingTre200px(ForecastParameterBase):
    __tablename__ = "tbl_ogd-local-forecasting-tre200px"

    value: Mapped[float] = mapped_column(Float)
