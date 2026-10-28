"""Request models (contracts/tools.openapi.yaml). Unknown fields are rejected (422)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ConversationId = Field(default=None, max_length=128)
Phone = Field(max_length=32)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GetProductRequest(Strict):
    query: str = Field(min_length=1, max_length=120)
    conversation_id: str | None = ConversationId


class GetStoreInfoRequest(Strict):
    # hours | location | delivery | returns | phone; anything else -> error_code unknown_topic.
    topic: str = Field(min_length=1, max_length=20)
    day: Literal["sat", "sun", "mon", "tue", "wed", "thu", "fri"] | None = None
    conversation_id: str | None = ConversationId


class ItemIn(Strict):
    product_id: str = Field(max_length=16)
    # 1-20 is a business rule (error_code invalid_qty), not a schema rule.
    qty: int


class QuoteOrderRequest(Strict):
    items: list[ItemIn] = Field(min_length=1, max_length=10)
    fulfillment: Literal["pickup", "delivery"]
    area: str | None = Field(default=None, max_length=40)
    time_slot: str = Field(max_length=40)
    now: str | None = Field(default=None, max_length=64)
    conversation_id: str | None = ConversationId


class CreateOrderRequest(Strict):
    quote_id: str = Field(max_length=64)
    customer_name: str = Field(min_length=1, max_length=40)
    phone: str = Phone
    conversation_id: str | None = ConversationId


class CheckOrderStatusRequest(Strict):
    order_id: str | None = Field(default=None, pattern=r"^\d{4}$")
    phone: str | None = Field(default=None, max_length=32)
    conversation_id: str | None = ConversationId

    @model_validator(mode="after")
    def exactly_one(self):
        if (self.order_id is None) == (self.phone is None):
            raise ValueError("give exactly one of order_id or phone")
        return self


class EscalateRequest(Strict):
    reason: Literal["asked_for_human", "angry", "not_understood", "cancel_request", "other"]
    summary: str = Field(min_length=1, max_length=300)
    customer_name: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=32)
    conversation_id: str | None = ConversationId
