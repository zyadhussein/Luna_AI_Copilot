from sqlalchemy.orm import Session
from sqlalchemy import func, select
from db_models import AgentInteractionDB


def log_agent_interaction(
    user_message: str,
    status: str,
    tool_count: int,
    latency_seconds: float,
    db: Session
):
    interaction = AgentInteractionDB(
        user_message=user_message,
        status=status,
        tool_count=tool_count,
        latency_seconds=latency_seconds,
    )

    db.add(interaction)
    db.commit()
def get_agent_metrics(
    db: Session
):
    total_requests = db.scalar(
        select(
            func.count(AgentInteractionDB.id)
        )
    ) or 0

    average_latency = db.scalar(
        select(
            func.avg(
                AgentInteractionDB.latency_seconds
            )
        )
    ) or 0

    average_tools = db.scalar(
        select(
            func.avg(
                AgentInteractionDB.tool_count
            )
        )
    ) or 0

    completed_requests = db.scalar(
        select(
            func.count(AgentInteractionDB.id)
        ).where(
            AgentInteractionDB.status == "completed"
        )
    ) or 0

    completion_rate = (
        completed_requests / total_requests * 100
        if total_requests > 0
        else 0
    )

    return {
        "total_requests": total_requests,
        "average_latency_seconds": round(
            float(average_latency),
            2
        ),
        "average_tools_per_request": round(
            float(average_tools),
            2
        ),
        "completion_rate": round(
            completion_rate,
            1
        )
    }