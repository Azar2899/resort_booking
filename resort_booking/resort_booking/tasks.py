import frappe
from frappe.utils import add_days, now_datetime, nowdate

from resort_booking.resort_booking.notifications import send_prebooking_reminder


def expire_pre_bookings():
	"""Runs hourly. A Pre-booked reservation that is never Confirmed within
	its hold window is auto-cancelled so the room becomes bookable again."""
	expired = frappe.get_all(
		"Resort Booking",
		filters={"status": "Pre-booked", "pre_booking_expires_on": ["<", now_datetime()]},
		pluck="name",
	)
	for name in expired:
		booking = frappe.get_doc("Resort Booking", name)
		booking.cancel_expired_pre_booking()


def send_prebooking_reminders():
	"""Runs daily. Emails guests whose check-in is tomorrow, exactly once."""
	tomorrow = add_days(nowdate(), 1)
	bookings = frappe.get_all(
		"Resort Booking",
		filters={
			"status": ["in", ("Pre-booked", "Confirmed")],
			"check_in": tomorrow,
			"reminder_sent": 0,
		},
		pluck="name",
	)
	for name in bookings:
		booking = frappe.get_doc("Resort Booking", name)
		send_prebooking_reminder(booking)
		booking.db_set("reminder_sent", 1, update_modified=False)
