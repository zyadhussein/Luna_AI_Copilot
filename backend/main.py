from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import BookingCreate, BookingResponse, AvailabilityCheck, AvailabilityResponse,QuoteResponse, QuoteRequest,BookingStatusResponse, AgentRequest,ConfirmationRequest
from services.bookings import create_booking, get_booking, check_availability,calculate_quote, cancel_booking
from database import get_db
from ai.agent import run_agent,confirm_action
from models import AgentRequest, AgentResponse,ConversationCreate
from fastapi.middleware.cors import CORSMiddleware
from services.analytics import log_agent_interaction, get_agent_metrics
import time
from services.conversations import (
    create_conversation,
    get_conversations,
    get_conversation_messages,add_message
)
from services.pending_actions import (
    mark_action_rejected,
    mark_action_completed
)
app = FastAPI(
    title="AI Operations Copilot API",
    version="0.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
@app.get(
    "/bookings/{booking_id}",
    response_model=BookingResponse
)
def get_booking_endpoint(
    booking_id: int,
    db: Session = Depends(get_db)
):
    return get_booking(
        booking_id,
        db
    )

@app.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=201
)
def create_booking_endpoint(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    return create_booking(booking, db)
@app.post(
    "/availability/check",
    response_model=AvailabilityResponse
)
def check_availability_endpoint(
    request: AvailabilityCheck,
    db: Session = Depends(get_db)
):
    return check_availability(
        request,
        db
    )
@app.post(
    "/quotes",
    response_model=QuoteResponse
)
def calculate_quote_endpoint(
    request: QuoteRequest,
    db: Session = Depends(get_db)
):
    return calculate_quote(
        request,
        db
    )
@app.patch(
    "/bookings/{booking_id}/cancel",
    response_model=BookingStatusResponse
)
def cancel_booking_endpoint(
    booking_id: int,
    db: Session = Depends(get_db)
):
    return cancel_booking(
        booking_id,
        db
    )
@app.post("/agent/chat")
def agent_chat_endpoint(
    request: AgentRequest,
    db: Session = Depends(get_db)
):
    conversation_id = request.conversation_id

    if conversation_id is None:
        conversation = create_conversation(
            db,
            request.message[:50]
        )

        conversation_id = conversation.id
    stored_messages = get_conversation_messages(
        conversation_id,
        db,
    )

    conversation_history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in stored_messages
    ]
    add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        db=db,
    )
    start_time = time.perf_counter()
    
    result = run_agent(
        request.message,
        db,
        conversation_id=conversation_id,
        conversation_history=conversation_history,
    )

    latency = (
        time.perf_counter() - start_time
    )
    if result["status"] == "completed":
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
            db=db,
        )
    log_agent_interaction(
        user_message=request.message,
        status=result["status"],
        tool_count=len(
            result.get("tool_trace", [])
        ),
        latency_seconds=latency,
        db=db,
    )
    result["conversation_id"] = conversation_id
    return result
@app.post("/agent/confirm")
def confirm_agent_action(
    request: ConfirmationRequest,
    db: Session = Depends(get_db)
):
    return confirm_action(
        request.confirmation_id,
        db
    )
@app.post("/agent/reject")
def reject_agent_action(
    request: ConfirmationRequest,
    db: Session = Depends(get_db),
):
    action = mark_action_rejected(
        request.confirmation_id,
        db,
    )

    if action is None:
        return {
            "status": "error",
            "message": "Confirmation request not found.",
        }

    return {
        "status": "rejected",
        "confirmation_id": request.confirmation_id,
    }
@app.get("/analytics/agent")
def agent_metrics_endpoint(
    db: Session = Depends(get_db)
):
    return get_agent_metrics(db)
@app.post("/conversations")
def create_conversation_endpoint(
    request: ConversationCreate,
    db: Session = Depends(get_db)
):
    conversation = create_conversation(
        db,
        request.title
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }
@app.get("/conversations")
def conversations_endpoint(
    db: Session = Depends(get_db)
):
    conversations = get_conversations(db)

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
        }
        for conversation in conversations
    ]
@app.get(
    "/conversations/{conversation_id}/messages"
)
def conversation_messages_endpoint(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    messages = get_conversation_messages(
        conversation_id,
        db
    )

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]