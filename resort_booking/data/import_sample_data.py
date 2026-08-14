"""Loads apps/resort_booking/resort_booking/data/sample_data.json into the site.

Run with:
	bench --site <site> execute resort_booking.data.import_sample_data.run

Dates in the JSON are day offsets from "today" (not fixed dates), so the
sample data is always relevant to whenever it's imported - a booking with
check_in_offset: -1 always means "checked in yesterday", not a specific
calendar date that goes stale.

Bookings are driven through the same status transitions a receptionist would
use (Draft -> Pre-booked/Confirmed -> Checked-in -> Checked-out, or Cancelled)
instead of writing the target status directly, so the same validation and
side effects (room status updates, advance-paid gate, auto refund on
cancellation) run exactly as they would in real use.
"""

import json
import os

import frappe
from frappe.utils import add_days


def run():
	frappe.set_user("Administrator")
	data = load_json()

	create_masters(data)
	create_rooms(data)
	create_rate_plans(data)
	create_guests(data)
	create_resort_resources(data)
	create_bookings(data)

	frappe.db.commit()
	print("Sample data import complete.")


def load_json():
	path = os.path.join(os.path.dirname(__file__), "sample_data.json")
	with open(path) as f:
		return json.load(f)


def create_masters(data):
	for row in data["room_types"]:
		get_or_insert("Room Type", {"room_type_name": row["room_type_name"]}, row)

	for row in data["room_categories"]:
		get_or_insert("Room Category", {"category_name": row["category_name"]}, row)

	for row in data["amenities"]:
		get_or_insert("Amenity", {"amenity_name": row["amenity_name"]}, row)


def create_rooms(data):
	for row in data["rooms"]:
		if frappe.db.exists("Room", {"room_number": row["room_number"]}):
			continue
		room = frappe.new_doc("Room")
		room.room_number = row["room_number"]
		room.room_type = row["room_type"]
		room.room_category = row["room_category"]
		room.floor = row["floor"]
		room.status = row["status"]
		for amenity in row["amenities"]:
			room.append("amenities", {"amenity": amenity})
		room.insert()


def create_rate_plans(data):
	for row in data["rate_plans"]:
		exists = frappe.db.exists(
			"Rate Plan", {"room_type": row["room_type"], "plan_name": row["plan_name"]}
		)
		if exists:
			continue
		plan = frappe.new_doc("Rate Plan")
		plan.room_type = row["room_type"]
		plan.plan_name = row["plan_name"]
		plan.from_date = add_days(frappe.utils.nowdate(), row["from_date_offset"])
		plan.to_date = add_days(frappe.utils.nowdate(), row["to_date_offset"])
		plan.rate_per_night = row["rate_per_night"]
		plan.insert()


def create_guests(data):
	for row in data["guests"]:
		get_or_insert("Guest", {"guest_name": row["guest_name"]}, row)


def create_resort_resources(data):
	for row in data["resort_resources"]:
		get_or_insert("Resort Resource", {"resource_name": row["resource_name"]}, row)


def create_bookings(data):
	for row in data["bookings"]:
		booking = frappe.new_doc("Resort Booking")
		booking.guest = frappe.db.get_value("Guest", {"guest_name": row["guest"]})
		booking.check_in = add_days(frappe.utils.nowdate(), row["check_in_offset"])
		booking.check_out = add_days(frappe.utils.nowdate(), row["check_out_offset"])
		for room_number in row["rooms"]:
			booking.append("rooms", {"room": room_number})
		booking.insert()

		record_payments(booking, row.get("payments", []))
		advance_booking_status(booking, row["status"], row.get("cancellation_reason"))
		create_resource_bookings(booking, row.get("resource_bookings", []))


def record_payments(booking, payments):
	for row in payments:
		payment = frappe.new_doc("Booking Payment")
		payment.booking = booking.name
		payment.payment_type = row["payment_type"]
		payment.amount = row["amount"]
		payment.payment_mode = row["payment_mode"]
		payment.reference_no = row.get("reference_no", "")
		payment.insert()
		payment.submit()


def advance_booking_status(booking, target_status, cancellation_reason):
	if target_status == "Draft":
		return

	if target_status == "Cancelled":
		booking.reload()
		booking.status = "Cancelled"
		booking.cancellation_reason = cancellation_reason
		booking.save()
		return

	# Confirmed/Checked-in/Checked-out all pass through Confirmed first, since
	# that's the step that checks the advance payment gate.
	booking.reload()
	booking.status = "Confirmed" if target_status != "Pre-booked" else "Pre-booked"
	booking.save()

	if target_status in ("Checked-in", "Checked-out"):
		booking.reload()
		booking.status = "Checked-in"
		booking.save()

	if target_status == "Checked-out":
		booking.reload()
		booking.status = "Checked-out"
		booking.save()


def create_resource_bookings(booking, resource_bookings):
	for row in resource_bookings:
		resource_booking = frappe.new_doc("Resource Booking")
		resource_booking.resource = row["resource"]
		resource_booking.booking = booking.name
		resource_booking.slot_date = add_days(frappe.utils.nowdate(), row["slot_date_offset"])
		resource_booking.slot_start_time = row["slot_start_time"]
		resource_booking.slot_end_time = row["slot_end_time"]
		resource_booking.insert()


def get_or_insert(doctype, filters, values):
	if frappe.db.exists(doctype, filters):
		return
	doc = frappe.new_doc(doctype)
	doc.update(values)
	doc.insert()
