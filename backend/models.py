from datetime import date

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    apartment_id: int
    guest_name: str
    check_in: date
    check_out: date
    guest_count: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    apartment_id: int
    guest_name: str
    check_in: date
    check_out: date
    guest_count: int
    total_price: float
    status: str
class AvailabilityCheck(BaseModel):
    apartment_id: int
    check_in: date
    check_out: date


class AvailabilityResponse(BaseModel):
    apartment_id: int
    check_in: date
    check_out: date
    available: bool
class QuoteRequest(BaseModel):
    apartment_id: int
    check_in: date
    check_out: date
    guest_count: int = Field(gt=0)


class QuoteResponse(BaseModel):
    apartment_id: int
    check_in: date
    check_out: date
    nights: int
    base_price: float
    total_price: float
class BookingStatusResponse(BaseModel):
    id: int
    status: str
class AgentRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class AgentResponse(BaseModel):
    answer: str
    conversation_id: int | None = None

class ConfirmationRequest(BaseModel):
    confirmation_id: str
class ConversationCreate(BaseModel):
    title: str = "New conversation"

