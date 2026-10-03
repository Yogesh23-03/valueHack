"""Engine-only routes.

Added to the app with a single ``include_router`` line in ``main.py`` so the
change stays additive.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from ..db import get_session
from ..engine.adapters import business_from_db
from ..engine.pricing import price_whatif

router = APIRouter(prefix="/api/pricing", tags=["engine"])


class PriceWhatIfParams(BaseModel):
    product_id: str
    price_change_pct: float
    elasticity: float = -0.7
    horizon_days: int = 30


@router.post("/whatif")
def api_price_whatif(params: PriceWhatIfParams, session: Session = Depends(get_session)):
    business = business_from_db(session)
    return price_whatif(
        business,
        params.product_id,
        params.price_change_pct,
        elasticity=params.elasticity,
        horizon_days=params.horizon_days,
    )
