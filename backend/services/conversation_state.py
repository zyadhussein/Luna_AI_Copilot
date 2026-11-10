from sqlalchemy.orm import Session

from db_models import ConversationDB

def update_state_from_tool(
    conversation_id: int,
    tool_name: str,
    result: dict,
    db: Session,
):
    state = get_conversation_state(
        conversation_id,
        db,
    )

    if tool_name == "get_booking":
        state["active_booking"] = result
        state.pop("last_quote", None)
        state.pop("last_availability", None)

    elif tool_name == "check_availability":
        state["last_availability"] = result

    elif tool_name == "calculate_quote":
        state["last_quote"] = result

    elif tool_name == "create_booking":
        state["active_booking"] = result

    elif tool_name == "cancel_booking":
        active_booking = state.get(
            "active_booking"
        )

        if active_booking:
            active_booking["status"] = "Cancelled"

    save_conversation_state(
        conversation_id,
        state,
        db,
    )
def get_conversation_state(
    conversation_id: int,
    db: Session,
) -> dict:
    conversation = db.get(
        ConversationDB,
        conversation_id,
    )

    if conversation is None:
        return {}

    return conversation.state or {}


def save_conversation_state(
    conversation_id: int,
    state: dict,
    db: Session,
):
    conversation = db.get(
        ConversationDB,
        conversation_id,
    )

    if conversation is None:
        raise ValueError(
            f"Conversation {conversation_id} not found"
        )

    conversation.state = state

    db.commit()
    db.refresh(conversation)