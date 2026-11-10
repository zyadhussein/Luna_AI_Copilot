import json
from datetime import date
from rag.retrieval import retrieve_policy
from openai import OpenAI
from sqlalchemy.orm import Session
from uuid import uuid4
from models import AvailabilityCheck, QuoteRequest, BookingCreate
from services.bookings import (
    get_booking,
    check_availability,
    calculate_quote,
    cancel_booking,
    create_booking,
)
from services.conversation_state import (
    get_conversation_state,
    update_state_from_tool,
)
from services.pending_actions import (
    create_pending_action,
    get_pending_action,
    mark_action_completed,
)
SENSITIVE_TOOLS = {
    "create_booking",
    "cancel_booking"
}

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

MODEL = "google/gemma-4-e4b"
TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_booking",
                "description": "Retrieve an existing booking by booking ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "integer",
                            "description": "The unique booking ID"
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": (
                    "Check whether an apartment is available "
                    "between a check-in and check-out date."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "apartment_id": {
                            "type": "integer"
                        },
                        "check_in": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "check_out": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        }
                    },
                    "required": [
                        "apartment_id",
                        "check_in",
                        "check_out"
                    ],
                    "additionalProperties": False
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "calculate_quote",
            "description": (
                "Calculate the price of a stay without creating a booking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "integer"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "guest_count": {
                        "type": "integer"
                    }
                },
                "required": [
                    "apartment_id",
                    "check_in",
                    "check_out",
                    "guest_count"
                ],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel an existing booking. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "integer"
                    }
                },
                "required": ["booking_id"],
                "additionalProperties": False
            }
        }
    },
    {
    "type": "function",
        "function": {
            "name": "create_booking",
            "description": (
                "Create a new booking. "
                "Use only after checking availability and obtaining the required booking details. "
                "This action requires user confirmation before execution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "integer"
                    },
                    "guest_name": {
                        "type": "string"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "guest_count": {
                        "type": "integer"
                    }
                },
                "required": [
                    "apartment_id",
                    "guest_name",
                    "check_in",
                    "check_out",
                    "guest_count"
                ]
            }
        }
    }
    ,{
    "type": "function",
        "function": {
            "name": "retrieve_policy",
            "description": (
                "Search hospitality policies and house rules. "
                "Use this for questions about policies, rules, "
                "refunds, pets, check-in, and similar knowledge."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    }
]

def execute_tool(
    tool_name: str,
    arguments: dict,
    db: Session
):
    
    if tool_name == "get_booking":
        booking = get_booking(
            arguments["booking_id"],
            db
        )

        return {
            "id": booking.id,
            "apartment_id": booking.apartment_id,
            "guest_name": booking.guest_name,
            "check_in": booking.check_in.isoformat(),
            "check_out": booking.check_out.isoformat(),
            "guest_count": booking.guest_count,
            "total_price": booking.total_price,
            "status": booking.status,
        }

    if tool_name == "check_availability":
        request = AvailabilityCheck(
            apartment_id=arguments["apartment_id"],
            check_in=date.fromisoformat(
                arguments["check_in"]
            ),
            check_out=date.fromisoformat(
                arguments["check_out"]
            )
        )

        result = check_availability(
            request,
            db
        )

        return {
            "apartment_id": result["apartment_id"],
            "check_in": result["check_in"].isoformat(),
            "check_out": result["check_out"].isoformat(),
            "available": result["available"],
        }
    if tool_name == "calculate_quote":
        request = QuoteRequest(
            apartment_id=arguments["apartment_id"],
            check_in=date.fromisoformat(
                arguments["check_in"]
            ),
            check_out=date.fromisoformat(
                arguments["check_out"]
            ),
            guest_count=arguments["guest_count"],
        )

        result = calculate_quote(
            request,
            db
        )

        return {
            "apartment_id": result["apartment_id"],
            "check_in": result["check_in"].isoformat(),
            "check_out": result["check_out"].isoformat(),
            "nights": result["nights"],
            "base_price": result["base_price"],
            "total_price": result["total_price"],
        }
    if tool_name == "cancel_booking":
        result = cancel_booking(
            arguments["booking_id"],
            db
        )

        return result
    if tool_name == "create_booking":
        request = BookingCreate(
            apartment_id=arguments["apartment_id"],
            guest_name=arguments["guest_name"],
            check_in=date.fromisoformat(arguments["check_in"]),
            check_out=date.fromisoformat(arguments["check_out"]),
            guest_count=arguments["guest_count"],
        )

        result = create_booking(
            request,
            db
        )

        return {
        "id": result.id,
        "apartment_id": result.apartment_id,
        "guest_name": result.guest_name,
        "check_in": result.check_in.isoformat(),
        "check_out": result.check_out.isoformat(),
        "guest_count": result.guest_count,
        "total_price": result.total_price,
        "status": result.status,
        }
    if tool_name == "retrieve_policy":

        results = retrieve_policy(
            arguments["query"],
            top_k=2
        )

        return {
            "results": [
                {
                    "title": result["title"],
                    "text": result["text"],
                    "score": result["score"]
                }
                for result in results
            ]
        }
    raise ValueError(
        f"Unknown tool: {tool_name}"
    )
def run_agent(
    user_message: str,
    db: Session,
    conversation_id: int,
    conversation_history: list[dict] | None = None,
):
    conversation_state = get_conversation_state(
        conversation_id,
        db,
    )
    messages = [
        {
            "role": "system",
            "content": (
            "You are Luna, a warm, natural and professional hospitality operations assistant. "
            "Speak conversationally, like a capable colleague helping the user with day-to-day operations. "
            "Do not sound like a database report or customer-support template unless the user explicitly asks for a formal summary. "
            "Keep responses concise and natural. "
            "Use short sentences and normal conversational language. "
            "You may use Markdown when it improves readability, but do not over-format simple answers. "
            "For booking or operational details, first answer naturally in one or two sentences, "
            "Before creating a booking, make sure the required details are known: "
            "apartment, guest name, check-in date, check-out date, and guest count. "
            "Check availability before proposing the booking. "
            "State-changing actions such as creating or cancelling bookings require user confirmation."
            "then only use a short list if several details need to be shown. "
            "Use tools whenever live booking, availability, pricing, or policy information is required. "
            "Use retrieve_policy for house rules and business policies. "
            "Never invent booking, pricing, availability, or policy information. "
            "If a tool returns an error or missing record, explain it naturally instead of exposing raw technical details. "
            "For state-changing actions, explain what you are about to do before requesting confirmation. "
            "Never substitute stale values from earlier conversation turns "
            "when newer structured state is available."
            "Your name is Luna."
        )
        },
         {
    "role": "system",
        "content": (
            "Current structured conversation state:\n"
            f"{json.dumps(conversation_state, indent=2)}\n\n"
            "IMPORTANT: This structured state is the authoritative context "
            "for resolving references in the current conversation. "
            "If conversation history conflicts with this state, ALWAYS trust "
            "the structured state. "
            "Use it to resolve references like 'it', 'him', 'her', 'them', "
            "'same booking', 'same dates', or 'rebook it'. "
            "Do not reuse older guest names, dates, booking IDs, or prices "
            "from conversation history when the structured state contains "
            "newer values."
        ),
    },
        {
            "role": "user",
            "content": user_message
        }
    ]
    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )


    tool_trace =[]
    max_steps = 8

    for step in range(max_steps):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0
        )

        assistant_message = response.choices[0].message

        messages.append(
            assistant_message
        )

        if not assistant_message.tool_calls:
            return {
                "status": "completed",
                "answer": assistant_message.content,
                "tool_trace": tool_trace
            }
        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(
                f"Step {step + 1}: "
                f"Model requested {tool_name}"
            )

            print(
                f"Arguments: {arguments}"
            )
            tool_trace.append({
                "tool": tool_name,
                "arguments": arguments
            })
            if tool_name in SENSITIVE_TOOLS:
                confirmation_id = str(uuid4())

                create_pending_action(
                    confirmation_id=confirmation_id,
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    db=db,
                )

                return {
                    "status": "confirmation_required",
                    "confirmation_id": confirmation_id,
                    "tool": tool_name,
                    "arguments": arguments,
                    "tool_trace": tool_trace,
                }
            try:
                result = execute_tool(
                    tool_name,
                    arguments,
                    db
                )
                update_state_from_tool(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    result=result,
                    db=db,
                )

            except Exception as error:
                result = {
                    "success": False,
                    "error": str(error)
                }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                }
            )


    return {
        "status": "error",
        "message": (
            "The agent reached the maximum number "
            "of steps without completing the task."
        ),
         "tool_trace": tool_trace
    }
def confirm_action(
    confirmation_id: str,
    db: Session
):
    pending = get_pending_action(
        confirmation_id,
        db,
    )

    if pending is None:
        return {
            "status": "error",
            "message": "Pending action not found or expired."
        }

    try:
        result = execute_tool(
            pending.tool_name,
            pending.arguments,
            db
        )

        mark_action_completed(
            confirmation_id,
            db,
        )


        return {
            "status": "completed",
            "tool": pending.tool_name,
            "result": result,
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }