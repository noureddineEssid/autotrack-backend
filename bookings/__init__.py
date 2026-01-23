"""
Bookings App

This app manages garage booking system for AutoTrack.

## Models

- **GarageService**: Services offered by garages
- **GarageAvailability**: Time slots when garages are available
- **Booking**: Customer appointments
- **BookingReview**: Customer reviews after service

## Features

- Book appointments at garages
- Check available time slots
- Confirm/cancel bookings
- Track booking status
- Email notifications
- Customer reviews
- Statistics and analytics
"""

default_app_config = 'bookings.apps.BookingsConfig'
