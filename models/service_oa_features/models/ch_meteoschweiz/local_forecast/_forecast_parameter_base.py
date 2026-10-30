from datetime import datetime as _datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.service_oa_features.models.base import Base


class ForecastParameterBase(Base):
    """The base for creating models for meteoschweiz's forecasting data

      Since most fields are the same across all the different parameters, we pack them
    into this base model here. The actual model implementations can then specify the concrete
    data type for the field "value"
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Value data
    datetime: Mapped[_datetime] = mapped_column(DateTime(timezone=True))
    feature_id: Mapped[str] = mapped_column(String(64))

    # Point data
    point_id: Mapped[int] = mapped_column(Integer)
    point_type_id: Mapped[int] = mapped_column(Integer)
    point_type_de: Mapped[str] = mapped_column(String(64))
    point_type_fr: Mapped[str] = mapped_column(String(64))
    point_type_it: Mapped[str] = mapped_column(String(64))
    point_type_en: Mapped[str] = mapped_column(String(64))
    station_abbr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    postal_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    point_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    point_height_masl: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry: Mapped[Geometry | None] = mapped_column(
        # unsure whether srid=4326 is correct here
        Geometry("Geometry", srid=4326),
        nullable=True,
    )

    # Paramater meta data
    parameter_shortname: Mapped[str] = mapped_column(String(64))
    parameter_description_de: Mapped[str] = mapped_column(String(256))
    parameter_description_fr: Mapped[str] = mapped_column(String(256))
    parameter_description_it: Mapped[str] = mapped_column(String(256))
    parameter_description_en: Mapped[str] = mapped_column(String(256))

    parameter_group_de: Mapped[str] = mapped_column(String(64))
    parameter_group_fr: Mapped[str] = mapped_column(String(64))
    parameter_group_it: Mapped[str] = mapped_column(String(64))
    parameter_group_en: Mapped[str] = mapped_column(String(64))

    parameter_granularity: Mapped[str] = mapped_column(String(64))
    parameter_decimals: Mapped[int] = mapped_column(Integer)
    parameter_datatype: Mapped[str] = mapped_column(String(64))

    parameter_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
