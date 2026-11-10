from sqlalchemy.orm import Session

from db_models import PendingActionDB


def create_pending_action(
    confirmation_id: str,
    conversation_id: int,
    tool_name: str,
    arguments: dict,
    db: Session,
):
    action = PendingActionDB(
        id=confirmation_id,
        conversation_id=conversation_id,
        tool_name=tool_name,
        arguments=arguments,
        status="pending",
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


def get_pending_action(
    confirmation_id: str,
    db: Session,
):
    return db.get(
        PendingActionDB,
        confirmation_id,
    )


def mark_action_completed(
    confirmation_id: str,
    db: Session,
):
    action = get_pending_action(
        confirmation_id,
        db,
    )

    if action is None:
        return None

    action.status = "completed"

    db.commit()
    db.refresh(action)

    return action


def mark_action_rejected(
    confirmation_id: str,
    db: Session,
):
    action = get_pending_action(
        confirmation_id,
        db,
    )

    if action is None:
        return None

    action.status = "rejected"

    db.commit()
    db.refresh(action)

    return action