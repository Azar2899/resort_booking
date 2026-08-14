from datetime import timedelta

import frappe
from frappe.utils import getdate


def get_settings():
	"""Resort Settings is a Single doctype - one shared record holds the
	advance %, pre-booking hold hours and notification config for the app."""
	return frappe.get_cached_doc("Resort Settings")


def get_rate_for_room_type(room_type, check_in, check_out):
	"""Price a stay night by night instead of using one flat rate for the
	whole stay, so a booking that crosses a Rate Plan's date range is priced
	correctly. Returns (total_amount, number_of_nights).
	"""
	check_in = getdate(check_in)
	check_out = getdate(check_out)
	nights = (check_out - check_in).days
	default_rate = frappe.db.get_value("Room Type", room_type, "default_rate") or 0

	total = 0
	for day_offset in range(nights):
		night = check_in + timedelta(days=day_offset)
		rate = frappe.db.get_value(
			"Rate Plan",
			{"room_type": room_type, "from_date": ["<=", night], "to_date": [">=", night]},
			"rate_per_night",
		)
		total += rate if rate else default_rate

	return total, nights
