from models.ch_meteoschweiz.local_forecast._forecast_parameter_base import ForecastParameterBase
from sqlalchemy import Float
from sqlalchemy.orm import Mapped, mapped_column


class ChMeteoschweizLocalForecastTre200px(ForecastParameterBase):
    __tablename__ = "ch_meteoschweiz_local_forecast_tre200px"

    value: Mapped[float] = mapped_column(Float)
