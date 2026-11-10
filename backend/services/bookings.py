from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import BookingCreate, BookingResponse, AvailabilityCheck,QuoteRequest
from sqlalchemy import select
from db_models import ApartmentDB, BookingDB

def create_booking( booking: BookingCreate,
    db: Session):
    

    selectedApartment = db.get(
    ApartmentDB,
    booking.apartment_id
)
    if selectedApartment is None:
        raise HTTPException(
            status_code=404,
            detail="Apartment not found"
        )
    if booking.guest_count>selectedApartment.capacity:
        raise HTTPException(
            status_code=400,
            detail = "guests number exceeds the max capacity"
        )
    if booking.check_out <= booking.check_in:
        raise HTTPException(
            status_code = 400,
            detail = "Check-out must be after check-in"
        )
    statement = select(BookingDB).where(
        BookingDB.apartment_id == booking.apartment_id,
        BookingDB.status == "confirmed"
        )

    existing_bookings = db.execute(
        statement
    ).scalars().all()
    for existing in existing_bookings:
        if (
            booking.check_in < existing.check_out
            and booking.check_out > existing.check_in
        ):
            raise HTTPException(
                status_code=409,
                detail="Booking dates overlap with an existing booking",
            )
    totalNights = (booking.check_out - booking.check_in).days
    totalPrice = totalNights * selectedApartment.base_price
    newBooking = BookingDB(

        apartment_id= booking.apartment_id,
        guest_name= booking.guest_name,
        check_in= booking.check_in,
        check_out= booking.check_out,
        guest_count= booking.guest_count,
        total_price= totalPrice,
        status= "confirmed",
    )
    db.add(newBooking)
    db.commit()
    db.refresh(newBooking)
    return newBooking
def get_booking(
    booking_id: int,
    db: Session
):
    booking = db.get(
        BookingDB,
        booking_id
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return booking
def check_availability(
    request: AvailabilityCheck,
    db: Session
):
    apartment = db.get(
        ApartmentDB,
        request.apartment_id
    )

    if apartment is None:
        raise HTTPException(
            status_code=404,
            detail="Apartment not found"
        )

    if request.check_out <= request.check_in:
        raise HTTPException(
            status_code=400,
            detail="Check-out must be after check-in"
        )

    statement = select(BookingDB).where(
        BookingDB.apartment_id == request.apartment_id,
        BookingDB.status == "confirmed",
        BookingDB.check_in < request.check_out,
        BookingDB.check_out > request.check_in
    )

    existing_booking = db.execute(
        statement
    ).scalars().first()

    return {
        "apartment_id": request.apartment_id,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "available": existing_booking is None
    }
def calculate_quote(
    request: QuoteRequest,
    db: Session
):
    apartment = db.get(
        ApartmentDB,
        request.apartment_id
    )

    if apartment is None:
        raise HTTPException(
            status_code=404,
            detail="Apartment not found"
        )

    if request.guest_count > apartment.capacity:
        raise HTTPException(
            status_code=400,
            detail="Guest count exceeds apartment capacity"
        )

    if request.check_out <= request.check_in:
        raise HTTPException(
            status_code=400,
            detail="Check-out must be after check-in"
        )

    nights = (
        request.check_out - request.check_in
    ).days

    total_price = (
        nights * apartment.base_price
    )

    return {
        "apartment_id": request.apartment_id,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "nights": nights,
        "base_price": apartment.base_price,
        "total_price": total_price
    }
def cancel_booking(
    booking_id: int,
    db: Session
):
    booking = db.get(
        BookingDB,
        booking_id
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Booking is already cancelled"
        )

    booking.status = "cancelled"

    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "status": booking.status
    }