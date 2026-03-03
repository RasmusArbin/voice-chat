"""
Mock tools that can be called by agents during dealership calls.

These are placeholder implementations demonstrating the tool interface.
In production, replace with real integrations to your CRM, inventory systems,
calendar systems, and other backend services.
"""

import logging

from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def get_dealership_info(
    location: str,
) -> str:
    """
    Returns basic dealership information for a given location.
    location should be a city or area name (e.g. 'Stockholm', 'Gothenburg').
    """
    logger.info("[Dealership] Fetching info for location %s", location)
    # TODO: replace with real dealership directory lookup
    return (
        f"Dealership info for {location}: Northlake Auto. "
        "Address: 214 Bergsgatan, Gothenburg. "
        "Phone: +46 31 555 120. "
        "Hours: Mon-Fri 09:00-18:00, Sat 10:00-15:00, Sun closed. "
        "Brands: Volvo, Volkswagen, Toyota. "
        "Services: new and used cars, trade-ins, financing, service bookings. "
        "Test drives: available daily by appointment."
    )


@function_tool
async def check_calendar_availability(
    date: str,
    time_window: str,
) -> str:
    """
    Checks whether the dealership has availability in a given time window.
    date should be an ISO 8601 date string (e.g. '2026-03-05').
    time_window should be a simple range (e.g. '10:00-12:00').
    """
    logger.info("[Calendar] Checking availability on %s during %s", date, time_window)
    # TODO: replace with real calendar availability lookup
    return f"Availability found on {date} between {time_window}."


@function_tool
async def book_meeting(
    customer_name: str,
    date: str,
    time: str,
    purpose: str,
) -> str:
    """
    Books a dealership meeting such as a test drive or consultation.
    date should be an ISO 8601 date string (e.g. '2026-03-05').
    time should be a 24-hour time string (e.g. '14:30').
    purpose should be 'test_drive', 'sales_consultation', or 'trade_in_review'.
    """
    logger.info(
        "[Calendar] Booking %s for %s on %s at %s",
        purpose, customer_name, date, time,
    )
    # TODO: replace with real calendar integration (Google Calendar, Outlook, etc.)
    return (
        f"Booked {purpose} for {customer_name} on {date} at {time}. "
        "A confirmation will be sent to the customer."
    )
