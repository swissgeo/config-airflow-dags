from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting.nprohihs import (
    OGDLocalForecastingNprohihs,
)
from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting.point import (
    OGDLocalForecastingPointMeta,
)
from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting.sre000h0 import (
    OGDLocalForecastingSre000h0,
)
from models.service_oa_features.models.org_meteoschweiz.dat_ogd_local_forecasting.tre200px import (
    OGDLocalForecastingTre200px,
)

from .base import Base

__all__ = [
    "Base",
    "OGDLocalForecastingNprohihs",
    "OGDLocalForecastingPointMeta",
    "OGDLocalForecastingSre000h0",
    "OGDLocalForecastingTre200px",
]
