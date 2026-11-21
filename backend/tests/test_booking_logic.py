from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from models import BookingCreate, AvailabilityCheck, QuoteRequest
from services.bookings import (
    create_booking,
    check_availability,
    calculate_quote,
)


def make_apartment(
    apartment_id=1204,
    capacity=3,
    base_price=350,
):
    return SimpleNamespace(
        id=apartment_id,
        capacity=capacity,
        base_price=base_price,
    )


def make_booking(
    apartment_id=1204,
    guest_name="Ahmed",
    check_in=date(2026, 10, 21),
    check_out=date(2026, 10, 23),
    guest_count=2,
):
    return BookingCreate(
        apartment_id=apartment_id,
        guest_name=guest_name,
        check_in=check_in,
        check_out=check_out,
        guest_count=guest_count,
    )


def test_create_booking_success():
    db = MagicMock()

    apartment = make_apartment()
    db.get.return_value = apartment

    db.execute.return_value.scalars.return_value.all.return_value = []

    booking = make_booking()

    result = create_booking(booking, db)

    assert result.apartment_id == 1204
    assert result.guest_name == "Ahmed"
    assert result.guest_count == 2
    assert result.total_price == 700
    assert result.status == "confirmed"

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_booking_unknown_apartment():
    db = MagicMock()
    db.get.return_value = None

    booking = make_booking()

    with pytest.raises(HTTPException) as exc:
        create_booking(booking, db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Apartment not found"


def test_create_booking_exceeds_capacity():
    db = MagicMock()

    apartment = make_apartment(capacity=2)
    db.get.return_value = apartment

    booking = make_booking(guest_count=3)

    with pytest.raises(HTTPException) as exc:
        create_booking(booking, db)

    assert exc.value.status_code == 400


def test_create_booking_invalid_dates():
    db = MagicMock()

    apartment = make_apartment()
    db.get.return_value = apartment

    booking = make_booking(
        check_in=date(2026, 10, 23),
        check_out=date(2026, 10, 21),
    )

    with pytest.raises(HTTPException) as exc:
        create_booking(booking, db)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Check-out must be after check-in"


def test_create_booking_overlap():
    db = MagicMock()

    apartment = make_apartment()
    db.get.return_value = apartment

    existing_booking = SimpleNamespace(
        check_in=date(2026, 10, 20),
        check_out=date(2026, 10, 22),
    )

    db.execute.return_value.scalars.return_value.all.return_value = [
        existing_booking
    ]

    booking = make_booking(
        check_in=date(2026, 10, 21),
        check_out=date(2026, 10, 23),
    )

    with pytest.raises(HTTPException) as exc:
        create_booking(booking, db)

    assert exc.value.status_code == 409


def test_check_availability_when_available():
    db = MagicMock()

    apartment = make_apartment()
    db.get.return_value = apartment

    db.execute.return_value.scalars.return_value.first.return_value = None

    request = AvailabilityCheck(
        apartment_id=1204,
        check_in=date(2026, 10, 21),
        check_out=date(2026, 10, 23),
    )

    result = check_availability(request, db)

    assert result["available"] is True


def test_check_availability_when_unavailable():
    db = MagicMock()

    apartment = make_apartment()
    db.get.return_value = apartment

    db.execute.return_value.scalars.return_value.first.return_value = (
        SimpleNamespace(id=1)
    )

    request = AvailabilityCheck(
        apartment_id=1204,
        check_in=date(2026, 10, 21),
        check_out=date(2026, 10, 23),
    )

    result = check_availability(request, db)

    assert result["available"] is False


def test_calculate_quote():
    db = MagicMock()

    apartment = make_apartment(
        capacity=3,
        base_price=350,
    )
    db.get.return_value = apartment

    request = QuoteRequest(
        apartment_id=1204,
        check_in=date(2026, 10, 21),
        check_out=date(2026, 10, 24),
        guest_count=2,
    )

    result = calculate_quote(request, db)

    assert result["nights"] == 3
    assert result["base_price"] == 350
    assert result["total_price"] == 1050