import frappe
from frappe.utils import getdate

from resort_booking.resort_booking.doctype.resort_booking.resort_booking import BLOCKING_STATUSES


@frappe.whitelist()
def check_availability(check_in, check_out, room_type=None):
	"""Return rooms that are free for the given date range.

	GET /api/method/resort_booking.api.check_availability
		?check_in=2026-08-20&check_out=2026-08-22&room_type=Luxury
	"""
	check_in = getdate(check_in)
	check_out = getdate(check_out)
	if check_out <= check_in:
		frappe.throw("check_out must be after check_in")

	room_filters = {"status": ["!=", "Under Maintenance"]}
	if room_type:
		room_filters["room_type"] = room_type

	all_rooms = frappe.get_all("Room", filters=room_filters, fields=["name", "room_type", "room_category"])
	booked_room_names = get_booked_room_names(check_in, check_out)

	return [room for room in all_rooms if room.name not in booked_room_names]


def get_booked_room_names(check_in, check_out):
	rows = frappe.db.sql(
		"""
		select distinct r.room
		from `tabBooking Room` r
		inner join `tabResort Booking` b on b.name = r.parent
		where b.status in %(blocking_statuses)s
			and b.check_in < %(check_out)s
			and b.check_out > %(check_in)s
		""",
		{"blocking_statuses": BLOCKING_STATUSES, "check_in": check_in, "check_out": check_out},
		as_dict=True,
	)
	return {row.room for row in rows}


@frappe.whitelist()
def get_resource_slots(resource, slot_date):
	"""Return booked slots and remaining capacity for a resource on a date.

	GET /api/method/resort_booking.api.get_resource_slots
		?resource=Main Pool&slot_date=2026-08-20
	"""
	capacity = frappe.db.get_value("Resort Resource", resource, "capacity")
	if capacity is None:
		frappe.throw(f"Resort Resource {resource} not found")

	booked_slots = frappe.get_all(
		"Resource Booking",
		filters={"resource": resource, "slot_date": slot_date, "status": "Booked"},
		fields=["name", "slot_start_time", "slot_end_time"],
		order_by="slot_start_time",
	)

	return {"resource": resource, "capacity": capacity, "booked_slots": booked_slots}
