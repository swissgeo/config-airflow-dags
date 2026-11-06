from geoalchemy2 import Geometry
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.service_oa_features.models.base import Base


class OGDLocalForecastingPointMeta(Base):
    """Table for meteoschweiz_local_forecasting data"""

    __tablename__ = "tbl_ogd-local-forecasting-point-meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    point_id: Mapped[int] = mapped_column(Integer)
    point_type_id: Mapped[int] = mapped_column(Integer)
    point_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    station_abbr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    postal_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    point_type_de: Mapped[str] = mapped_column(String(64))
    point_type_fr: Mapped[str] = mapped_column(String(64))
    point_type_it: Mapped[str] = mapped_column(String(64))
    point_type_en: Mapped[str] = mapped_column(String(64))
    point_height_masl: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry: Mapped[Geometry | None] = mapped_column(
        # unsure whether srid=4326 is correct here
        Geometry("Geometry", srid=4326),
        nullable=True,
    )
