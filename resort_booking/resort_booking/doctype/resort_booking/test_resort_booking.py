import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestResortBooking(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.room_type = get_or_create("Room Type", {"room_type_name": "Test Luxury"}, {"default_rate": 5000})
		cls.room_category = get_or_create("Room Category", {"category_name": "Test Villas"}, {})
		cls.room = get_or_create(
			"Room",
			{"room_number": "TU-101"},
			{"room_type": cls.room_type, "room_category": cls.room_category, "status": "Available"},
		)
		cls.guest = get_or_create("Guest", {"guest_name": "Test Guest"}, {"phone": "9000000000"})

	def make_booking(self, check_in_offset, check_out_offset, room=None):
		booking = frappe.new_doc("Resort Booking")
		booking.guest = self.guest
		booking.check_in = add_days(nowdate(), check_in_offset)
		booking.check_out = add_days(nowdate(), check_out_offset)
		booking.append("rooms", {"room": room or self.room})
		booking.insert()
		return booking

	def test_grand_total_is_nights_times_rate(self):
		booking = self.make_booking(10, 13)  # 3 nights
		self.assertEqual(booking.total_nights, 3)
		self.assertEqual(booking.grand_total, 15000)

	def test_pricing_blends_rate_plan_and_default_rate_across_the_boundary(self):
		"""A Rate Plan only covers part of the stay - nights inside it should
		use its rate, nights outside it should fall back to the default rate,
		instead of one flat rate applying to the whole stay."""
		rate_plan = frappe.new_doc("Rate Plan")
		rate_plan.room_type = self.room_type
		rate_plan.plan_name = "Test Peak Season"
		rate_plan.from_date = add_days(nowdate(), 100)
		rate_plan.to_date = add_days(nowdate(), 101)
		rate_plan.rate_per_night = 9000
		rate_plan.insert()

		# stay = nights at offset 99, 100, 101 -> only 100 and 101 are inside the plan
		booking = self.make_booking(99, 102)
		self.assertEqual(booking.total_nights, 3)
		self.assertEqual(booking.grand_total, 5000 + 9000 + 9000)

	def test_check_out_must_be_after_check_in(self):
		booking = frappe.new_doc("Resort Booking")
		booking.guest = self.guest
		booking.check_in = add_days(nowdate(), 10)
		booking.check_out = add_days(nowdate(), 10)
		booking.append("rooms", {"room": self.room})
		self.assertRaises(frappe.ValidationError, booking.insert)

	def test_double_booking_is_blocked_for_overlapping_dates(self):
		first = self.make_booking(20, 23)
		first.status = "Pre-booked"  # Pre-booked already holds the room
		first.save()

		clashing = frappe.new_doc("Resort Booking")
		clashing.guest = self.guest
		clashing.check_in = add_days(nowdate(), 21)  # overlaps 20-23
		clashing.check_out = add_days(nowdate(), 24)
		clashing.append("rooms", {"room": self.room})
		clashing.insert()
		clashing.status = "Pre-booked"
		self.assertRaises(frappe.ValidationError, clashing.save)

	def test_back_to_back_bookings_do_not_clash(self):
		"""Checkout day of one booking is the check-in day of the next -
		this is a valid same-day turnover, not a double-booking."""
		first = self.make_booking(30, 33)
		first.status = "Pre-booked"
		first.save()

		second = frappe.new_doc("Resort Booking")
		second.guest = self.guest
		second.check_in = add_days(nowdate(), 33)  # starts exactly when first ends
		second.check_out = add_days(nowdate(), 35)
		second.append("rooms", {"room": self.room})
		second.insert()
		second.status = "Pre-booked"
		second.save()  # should not raise
		self.assertEqual(second.status, "Pre-booked")

	def test_confirm_requires_minimum_advance(self):
		booking = self.make_booking(40, 42)  # grand_total = 10000, needs >= 3000
		booking.status = "Confirmed"
		self.assertRaises(frappe.ValidationError, booking.save)

	def test_confirm_succeeds_once_advance_is_paid(self):
		booking = self.make_booking(45, 47)  # grand_total = 10000
		self.add_advance_payment(booking, amount=3000)
		booking.reload()
		booking.status = "Confirmed"
		booking.save()
		self.assertEqual(booking.status, "Confirmed")

	def test_cancelling_a_payment_after_confirm_does_not_break_the_booking(self):
		"""Regression test: the advance gate must only fire on the save that
		moves the booking INTO Confirmed, not on every later save. Otherwise
		correcting a payment (amend/cancel) after confirmation is a dead end -
		the booking's own re-save (triggered by the payment update) would
		fail the same gate it already passed once."""
		booking = self.make_booking(65, 67)  # grand_total = 10000
		payment = frappe.new_doc("Booking Payment")
		payment.booking = booking.name
		payment.payment_type = "Advance"
		payment.amount = 3000
		payment.insert()
		payment.submit()

		booking.reload()
		booking.status = "Confirmed"
		booking.save()

		payment.cancel()  # should not raise

		booking.reload()
		self.assertEqual(booking.advance_paid, 0)
		self.assertEqual(booking.status, "Confirmed")

	def test_checkin_occupies_room_and_checkout_frees_it(self):
		room = get_or_create(
			"Room",
			{"room_number": "TU-102"},
			{"room_type": self.room_type, "room_category": self.room_category, "status": "Available"},
		)
		booking = self.make_booking(50, 52, room=room)
		self.add_advance_payment(booking, amount=3000)
		booking.reload()
		booking.status = "Confirmed"
		booking.save()

		booking.status = "Checked-in"
		booking.save()
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")

		booking.status = "Checked-out"
		booking.save()
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Available")

	def test_cancel_after_checkin_is_rejected(self):
		room = get_or_create(
			"Room",
			{"room_number": "TU-103"},
			{"room_type": self.room_type, "room_category": self.room_category, "status": "Available"},
		)
		booking = self.make_booking(55, 57, room=room)
		self.add_advance_payment(booking, amount=3000)
		booking.reload()
		booking.status = "Confirmed"
		booking.save()
		booking.status = "Checked-in"
		booking.save()

		booking.status = "Cancelled"
		booking.cancellation_reason = "test"
		self.assertRaises(frappe.ValidationError, booking.save)

	def test_cancellation_creates_automatic_refund_entry(self):
		booking = self.make_booking(60, 62)
		self.add_advance_payment(booking, amount=3000)
		booking.reload()
		booking.status = "Cancelled"
		booking.cancellation_reason = "guest changed plans"
		booking.save()

		refund = frappe.db.get_value(
			"Booking Payment", {"booking": booking.name, "payment_type": "Refund"}, "amount"
		)
		self.assertEqual(refund, 3000)

	def add_advance_payment(self, booking, amount=3000):
		payment = frappe.new_doc("Booking Payment")
		payment.booking = booking.name
		payment.payment_type = "Advance"
		payment.amount = amount
		payment.insert()
		payment.submit()


def get_or_create(doctype, filters, values):
	name = frappe.db.exists(doctype, filters)
	if name:
		return name
	doc = frappe.new_doc(doctype)
	doc.update(filters)
	doc.update(values)
	doc.insert()
	return doc.name
