import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestResourceBooking(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		room_type = get_or_create("Room Type", {"room_type_name": "RB Test Room Type"}, {"default_rate": 1000})
		room_category = get_or_create("Room Category", {"category_name": "RB Test Category"}, {})
		room = get_or_create(
			"Room",
			{"room_number": "RB-101"},
			{"room_type": room_type, "room_category": room_category, "status": "Available"},
		)
		guest = get_or_create("Guest", {"guest_name": "RB Test Guest"}, {"phone": "9000000001"})

		booking = frappe.new_doc("Resort Booking")
		booking.guest = guest
		booking.check_in = add_days(nowdate(), 5)
		booking.check_out = add_days(nowdate(), 7)
		booking.append("rooms", {"room": room})
		booking.insert()
		cls.room_booking = booking.name

		cls.resource = get_or_create(
			"Resort Resource",
			{"resource_name": "Test Capacity Pool"},
			{"resource_type": "Pool", "capacity": 1, "operating_hours_from": "06:00:00", "operating_hours_to": "22:00:00"},
		)

	def make_slot(self, start, end, slot_date_offset=5):
		slot = frappe.new_doc("Resource Booking")
		slot.resource = self.resource
		slot.booking = self.room_booking
		slot.slot_date = add_days(nowdate(), slot_date_offset)
		slot.slot_start_time = start
		slot.slot_end_time = end
		return slot

	# Each test below uses its own slot_date_offset. FrappeTestCase only rolls
	# back once the whole class finishes (not after each test method), so
	# slots inserted by one test are still in the database for the next one -
	# reusing a date would make these tests pass or fail depending on run
	# order instead of on their own logic.

	def test_end_time_must_be_after_start_time(self):
		slot = self.make_slot("10:00:00", "10:00:00", slot_date_offset=1)
		self.assertRaises(frappe.ValidationError, slot.insert)

	def test_slot_outside_operating_hours_is_rejected(self):
		slot = self.make_slot("05:00:00", "06:00:00", slot_date_offset=2)
		self.assertRaises(frappe.ValidationError, slot.insert)

	def test_overlapping_slot_beyond_capacity_is_rejected(self):
		first = self.make_slot("10:00:00", "11:00:00", slot_date_offset=3)
		first.insert()

		second = self.make_slot("10:30:00", "11:30:00", slot_date_offset=3)  # overlaps, capacity is 1
		self.assertRaises(frappe.ValidationError, second.insert)

	def test_non_overlapping_slot_is_allowed(self):
		first = self.make_slot("10:00:00", "11:00:00", slot_date_offset=4)
		first.insert()

		second = self.make_slot("11:00:00", "12:00:00", slot_date_offset=4)  # starts exactly when first ends
		second.insert()  # should not raise
		self.assertEqual(second.status, "Booked")


def get_or_create(doctype, filters, values):
	name = frappe.db.exists(doctype, filters)
	if name:
		return name
	doc = frappe.new_doc(doctype)
	doc.update(filters)
	doc.update(values)
	doc.insert()
	return doc.name
