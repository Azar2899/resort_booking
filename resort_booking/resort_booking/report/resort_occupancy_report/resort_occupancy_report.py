import calendar
from datetime import timedelta

import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate


OCCUPIED_STATUSES = ("Confirmed", "Checked-in", "Checked-out")


def execute(filters=None):
	months = get_last_n_months(6)
	columns = get_columns()
	data = get_data(months)
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns():
	return [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 120},
		{"label": "Room-Nights Booked", "fieldname": "booked_nights", "fieldtype": "Int", "width": 160},
		{"label": "Room-Nights Available", "fieldname": "available_nights", "fieldtype": "Int", "width": 170},
		{"label": "Occupancy %", "fieldname": "occupancy_percent", "fieldtype": "Percent", "width": 120},
	]


def get_last_n_months(n):
	today = getdate()
	return [get_first_day(add_months(today, -i)) for i in range(n - 1, -1, -1)]


def get_data(months):
	total_rooms = frappe.db.count("Room") or 1
	window_start = months[0]
	window_end = get_last_day(months[-1])

	bookings = frappe.db.sql(
		"""
		select b.check_in, b.check_out, count(r.name) as room_count
		from `tabResort Booking` b
		inner join `tabBooking Room` r on r.parent = b.name
		where b.status in %(statuses)s
			and b.check_in < %(window_end)s
			and b.check_out > %(window_start)s
		group by b.name
		""",
		{"statuses": OCCUPIED_STATUSES, "window_start": window_start, "window_end": window_end},
		as_dict=True,
	)

	booked_nights_by_month = {get_month_key(m): 0 for m in months}
	for booking in bookings:
		add_booking_nights_to_month_buckets(booking, booked_nights_by_month)

	return [build_month_row(month_start, total_rooms, booked_nights_by_month) for month_start in months]


def add_booking_nights_to_month_buckets(booking, booked_nights_by_month):
	"""Walk every night of the stay and add its room count to that night's
	month - this is what makes a booking spanning two months split correctly
	between them instead of being counted whole in one month."""
	night = getdate(booking.check_in)
	checkout = getdate(booking.check_out)
	while night < checkout:
		key = get_month_key(night)
		if key in booked_nights_by_month:
			booked_nights_by_month[key] += booking.room_count
		night += timedelta(days=1)


def build_month_row(month_start, total_rooms, booked_nights_by_month):
	days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]
	available_nights = total_rooms * days_in_month
	booked_nights = booked_nights_by_month[get_month_key(month_start)]
	occupancy_percent = (booked_nights / available_nights * 100) if available_nights else 0

	return {
		"month": month_start.strftime("%b %Y"),
		"booked_nights": booked_nights,
		"available_nights": available_nights,
		"occupancy_percent": round(occupancy_percent, 1),
	}


def get_month_key(date):
	return (date.year, date.month)


def get_chart(data):
	return {
		"data": {
			"labels": [row["month"] for row in data],
			"datasets": [{"name": "Occupancy %", "values": [row["occupancy_percent"] for row in data]}],
		},
		"type": "pie",
	}
