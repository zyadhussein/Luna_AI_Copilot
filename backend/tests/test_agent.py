from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ai.agent import run_agent


def make_tool_response(
    tool_name: str,
    arguments: str,
    tool_call_id: str = "call_123",
):
    tool_call = SimpleNamespace(
        id=tool_call_id,
        function=SimpleNamespace(
            name=tool_name,
            arguments=arguments,
        ),
    )

    message = SimpleNamespace(
        content=None,
        tool_calls=[tool_call],
    )

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=message
            )
        ]
    )


def make_final_response(content: str):
    message = SimpleNamespace(
        content=content,
        tool_calls=None,
    )

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=message
            )
        ]
    )


@patch("ai.agent.update_state_from_tool")
@patch("ai.agent.execute_tool")
@patch("ai.agent.get_conversation_state")
@patch("ai.agent.client.chat.completions.create")
def test_agent_executes_get_booking(
    mock_llm,
    mock_get_state,
    mock_execute_tool,
    mock_update_state,
):
    db = MagicMock()

    mock_get_state.return_value = {}

    mock_llm.side_effect = [
        make_tool_response(
            "get_booking",
            '{"booking_id": 2}',
        ),
        make_final_response(
            "Booking 2 belongs to Kareem."
        ),
    ]

    mock_execute_tool.return_value = {
        "id": 2,
        "apartment_id": 1204,
        "guest_name": "Kareem",
        "check_in": "2026-10-26",
        "check_out": "2026-10-28",
        "guest_count": 2,
        "total_price": 700,
        "status": "cancelled",
    }

    result = run_agent(
        user_message="Tell me about booking 2",
        db=db,
        conversation_id=1,
        conversation_history=[],
    )

    assert result["status"] == "completed"
    assert result["answer"] == "Booking 2 belongs to Kareem."

    assert result["tool_trace"] == [
        {
            "tool": "get_booking",
            "arguments": {
                "booking_id": 2
            },
        }
    ]

    mock_execute_tool.assert_called_once_with(
        "get_booking",
        {"booking_id": 2},
        db,
    )

    mock_update_state.assert_called_once_with(
        conversation_id=1,
        tool_name="get_booking",
        result=mock_execute_tool.return_value,
        db=db,
    )

    assert mock_llm.call_count == 2


@patch("ai.agent.create_pending_action")
@patch("ai.agent.execute_tool")
@patch("ai.agent.get_conversation_state")
@patch("ai.agent.client.chat.completions.create")
def test_cancel_booking_requires_confirmation(
    mock_llm,
    mock_get_state,
    mock_execute_tool,
    mock_create_pending,
):
    db = MagicMock()

    mock_get_state.return_value = {
        "active_booking": {
            "id": 2,
            "guest_name": "Kareem",
            "status": "confirmed",
        }
    }

    mock_llm.return_value = make_tool_response(
        "cancel_booking",
        '{"booking_id": 2}',
    )

    result = run_agent(
        user_message="Cancel booking 2",
        db=db,
        conversation_id=1,
        conversation_history=[],
    )

    assert result["status"] == "confirmation_required"
    assert result["tool"] == "cancel_booking"
    assert result["arguments"] == {
        "booking_id": 2
    }

    assert result["tool_trace"] == [
        {
            "tool": "cancel_booking",
            "arguments": {
                "booking_id": 2
            },
        }
    ] 

    # Critical safety assertion:
    # cancellation must NOT execute before confirmation.
    mock_execute_tool.assert_not_called()

    mock_create_pending.assert_called_once()

    call_kwargs = mock_create_pending.call_args.kwargs

    assert call_kwargs["conversation_id"] == 1
    assert call_kwargs["tool_name"] == "cancel_booking"
    assert call_kwargs["arguments"] == {
        "booking_id": 2
    }
    assert call_kwargs["db"] is db
    assert call_kwargs["confirmation_id"]