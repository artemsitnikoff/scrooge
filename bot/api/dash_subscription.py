from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

PLANS = {
    "month": {"days": 30, "price": 2900, "label": "Месяц"},
    "year": {"days": 365, "price": 29000, "label": "Год"},
}


class SubscriptionObjectResponse(BaseModel):
    id: int
    name: str
    object_id: str
    expires_at: str | None = None
    active: bool = False
    days_left: int | None = None


class PayRequest(BaseModel):
    object_db_id: int
    plan: str


class PayResponse(BaseModel):
    payment_url: str
    payment_id: str


class PaymentStatusResponse(BaseModel):
    status: str
    paid: bool


@router.get("", response_model=list[SubscriptionObjectResponse])
async def list_subscriptions(user: dict = Depends(get_current_user)):
    rows = await db.get_subscriptions_for_user(user["user_id"])
    now = datetime.utcnow()
    result = []
    for r in rows:
        expires_at = r["expires_at"]
        active = bool(expires_at and expires_at > now.isoformat())
        days_left = None
        if active and expires_at:
            delta = datetime.fromisoformat(expires_at) - now
            days_left = max(0, delta.days)
        result.append(SubscriptionObjectResponse(
            id=r["id"],
            name=r["name"],
            object_id=r["object_id"],
            expires_at=expires_at,
            active=active,
            days_left=days_left,
        ))
    return result


@router.post("/pay", response_model=PayResponse)
async def create_payment(req: PayRequest, user: dict = Depends(get_current_user)):
    if req.plan not in PLANS:
        raise HTTPException(status_code=422, detail="Неверный тариф")

    obj = await db.get_object(req.object_db_id)
    if not obj or obj["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Объект не найден")

    plan_info = PLANS[req.plan]

    from services.yukassa_client import YukassaClient
    client = YukassaClient()
    try:
        payment = await client.create_payment(
            amount=plan_info["price"],
            description=f"SCROOGE — {plan_info['label']}, объект: {obj['name']}",
            user_id=user["user_id"],
            object_db_id=req.object_db_id,
            plan=req.plan,
        )
    finally:
        await client.close()

    await db.create_web_payment(
        yukassa_payment_id=payment["id"],
        user_id=user["user_id"],
        object_db_id=req.object_db_id,
        plan=req.plan,
        amount=plan_info["price"],
    )

    return PayResponse(
        payment_url=payment["confirmation_url"],
        payment_id=payment["id"],
    )


@router.get("/payment-status/{payment_id}", response_model=PaymentStatusResponse)
async def check_payment_status(payment_id: str, user: dict = Depends(get_current_user)):
    wp = await db.get_web_payment_by_yukassa_id(payment_id)
    if not wp or wp["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    return PaymentStatusResponse(
        status=wp["status"],
        paid=wp["status"] == "succeeded",
    )
