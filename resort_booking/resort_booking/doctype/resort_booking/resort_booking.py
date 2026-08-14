import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, getdate, now_datetime

from resort_booking.resort_booking.notifications import send_booking_confirmation, send_cancellation_emails
from resort_booking.resort_booking.utils import get_rate_for_room_type, get_settings

# A booking can only move forward along this chain (each status also allows
# staying on itself, so re-saving a form doesn't get rejected). Cancelled is
# reachable from every state except Checked-in/Checked-out - once a guest has
# physically checked in, "cancelling" no longer makes sense, that's a checkout.
ALLOWED_NEXT_STATUS = {
	"Draft": {"Draft", "Pre-booked", "Confirmed", "Cancelled"},
	"Pre-booked": {"Pre-booked", "Confirmed", "Cancelled"},
	"Confirmed": {"Confirmed", "Checked-in", "Cancelled"},
	"Checked-in": {"Checked-in", "Checked-out"},
	"Checked-out": {"Checked-out"},
	"Cancelled": {"Cancelled"},
}

# A room booked under any of these statuses holds the inventory, so it must
# be counted when checking for double-booking.
BLOCKING_STATUSES = ("Pre-booked", "Confirmed", "Checked-in")


class ResortBooking(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_pricing()
		self.validate_status_transition()

		if self.status in BLOCKING_STATUSES:
			self.check_room_availability()

		if self.is_transitioning_to("Confirmed"):
			self.validate_advance_paid()

		if self.status == "Pre-booked" and not self.pre_booking_expires_on:
			hold_hours = get_settings().pre_booking_hold_hours or 24
			self.pre_booking_expires_on = add_to_date(now_datetime(), hours=hold_hours)

		if self.status == "Cancelled":
			self.validate_cancel_allowed()
			if not self.cancellation_reason:
				frappe.throw(_("Cancellation Reason is mandatory"))

	def on_update(self):
		previous = self.get_doc_before_save()
		if not previous or previous.status == self.status:
			return

		if self.status == "Checked-in":
			self.db_set("checked_in_on", now_datetime(), update_modified=False)
			self.set_room_status("Occupied")

		if self.status == "Checked-out":
			self.db_set("checked_out_on", now_datetime(), update_modified=False)
			self.set_room_status("Available")

		if self.status == "Confirmed":
			send_booking_confirmation(self)

		if self.status == "Cancelled":
			self.db_set("cancelled_on", now_datetime(), update_modified=False)
			self.create_refund_entry()
			send_cancellation_emails(self)

	# ---- validation ---------------------------------------------------------

	def validate_dates(self):
		# Date fields arrive as plain strings when a doc is created via the API
		# or a form submit - normalize to real date objects before any of the
		# date arithmetic below (nights, rate lookups, overlap checks) runs.
		self.check_in = getdate(self.check_in)
		self.check_out = getdate(self.check_out)
		if self.check_out <= self.check_in:
			frappe.throw(_("Check-out Date must be after Check-in Date"))

	def validate_status_transition(self):
		if self.is_new():
			return
		previous_status = self.get_doc_before_save().status
		if self.status not in ALLOWED_NEXT_STATUS.get(previous_status, set()):
			frappe.throw(_("Booking cannot move from {0} to {1}").format(previous_status, self.status))

	def is_transitioning_to(self, status):
		"""True only on the save that moves the booking INTO this status, not
		on every later save while it happens to already be in it - otherwise
		e.g. cancelling a submitted payment on a Confirmed booking (which
		recomputes and re-saves advance_paid) would be blocked by the advance
		gate, even though that gate should only apply at the moment of
		confirming, not to every unrelated update afterwards."""
		if self.status != status:
			return False
		if self.is_new():
			return True
		return self.get_doc_before_save().status != status

	def validate_advance_paid(self):
		if (self.advance_paid or 0) < (self.min_advance_required or 0):
			frappe.throw(
				_("An advance of at least {0} is required to confirm this booking (received: {1})").format(
					frappe.format_value(self.min_advance_required, {"fieldtype": "Currency"}),
					frappe.format_value(self.advance_paid or 0, {"fieldtype": "Currency"}),
				)
			)

	def validate_cancel_allowed(self):
		"""Only a Resort Manager can cancel a booking by hand. The scheduler's
		cancel_expired_pre_booking() sets flags.system_cancel to skip this check,
		since an expired hold is cancelled by the system, not by a logged-in user."""
		if self.flags.get("system_cancel"):
			return
		user_roles = frappe.get_roles(frappe.session.user)
		if "Resort Manager" not in user_roles and "System Manager" not in user_roles:
			frappe.throw(_("Only a Resort Manager can cancel a booking"))

	def check_room_availability(self):
		for row in self.rooms:
			# Lock the Room row first so two receptionists saving at the same
			# time can't both pass this check before either save commits.
			frappe.db.get_value("Room", row.room, "name", for_update=True)

			conflicting = frappe.db.sql(
				"""
				select b.name
				from `tabResort Booking` b
				inner join `tabBooking Room` r on r.parent = b.name
				where b.status in %(blocking_statuses)s
					and b.name != %(name)s
					and r.room = %(room)s
					and b.check_in < %(check_out)s
					and b.check_out > %(check_in)s
				""",
				{
					"blocking_statuses": BLOCKING_STATUSES,
					"name": self.name or "New Resort Booking",
					"room": row.room,
					"check_out": self.check_out,
					"check_in": self.check_in,
				},
			)
			if conflicting:
				frappe.throw(
					_("Room {0} is already booked for these dates (Booking {1})").format(
						row.room, conflicting[0][0]
					)
				)

	# ---- pricing --------------------------------------------------------------

	def calculate_pricing(self):
		self.total_nights = (self.check_out - self.check_in).days
		grand_total = 0

		for row in self.rooms:
			room_type = frappe.db.get_value("Room", row.room, "room_type")
			amount, nights = get_rate_for_room_type(room_type, self.check_in, self.check_out)
			row.nights = nights
			row.rate_per_night = amount / nights if nights else 0
			row.amount = amount
			grand_total += amount

		self.grand_total = grand_total
		self.min_advance_required = grand_total * (get_settings().advance_percent or 30) / 100
		self.balance_due = grand_total - (self.advance_paid or 0)

	# ---- side effects on status change -----------------------------------

	def set_room_status(self, status):
		for row in self.rooms:
			frappe.db.set_value("Room", row.room, "status", status)

	def create_refund_entry(self):
		"""Leave a paper trail of what is owed back to the guest, even on a
		fully-automatic cancellation - per the "refund tracking" requirement."""
		if not self.advance_paid:
			return

		refund = frappe.new_doc("Booking Payment")
		refund.booking = self.name
		refund.payment_type = "Refund"
		refund.amount = self.advance_paid
		refund.remarks = "Auto-created on booking cancellation"
		refund.flags.system_refund = True
		refund.insert(ignore_permissions=True)
		refund.submit()

	# ---- called by the scheduler --------------------------------------------

	def cancel_expired_pre_booking(self):
		self.flags.system_cancel = True
		self.status = "Cancelled"
		self.cancellation_reason = "Auto-cancelled: pre-booking was not confirmed within the hold period"
		self.save(ignore_permissions=True)
