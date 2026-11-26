import os
import requests


N8N_BOOKING_CREATED_WEBHOOK = os.getenv(
    "N8N_BOOKING_CREATED_WEBHOOK",
    "http://localhost:5678/webhook-test/booking-created",
)


def notify_booking_created(booking: dict):
    response = requests.post(
        N8N_BOOKING_CREATED_WEBHOOK,
        json=booking,
        timeout=5,
    )

    response.raise_for_status()

    return {
        "status_code": response.status_code,
    }