import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, getdate, now_datetime

from resort_booking.resort_booking.notifications import send_booking_confirmation, send_cancellation_emails
from resort_booking.resort_booking.utils import get_rate_for_room_type, get_settings

from frappe.utils import get_datetime
from frappe.utils import flt


ALLOWED_NEXT_STATUS = {
	"Draft": {"Draft", "Pre-booked", "Confirmed", "Cancelled"},
	"Pre-booked": {"Pre-booked", "Confirmed", "Cancelled"},
	"Confirmed": {"Confirmed", "Checked-in", "Cancelled"},
	"Checked-in": {"Checked-in", "Checked-out"},
	"Checked-out": {"Checked-out"},
	"Cancelled": {"Cancelled"},
}

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
		
		

	def validate_dates(self):

		if not self.check_in or not self.check_out:
			return

		if self.check_out <= self.check_in:
			frappe.throw(
				"Check-out Date & Time must be after Check-in Date & Time."
			)

		blocking_statuses = [
			"Pre-booked",
			"Confirmed",
			"Checked-in",
		]

		for row in self.rooms:

			if not row.room:
				continue

			existing_bookings = frappe.db.sql(
				"""
				SELECT
					b.name,
					b.check_in,
					b.check_out
				FROM `tabResort Booking` b
				INNER JOIN `tabBooking Room` br
					ON br.parent = b.name
				WHERE
					br.room = %(room)s
					AND b.name != %(booking)s
					AND b.status IN %(blocking_statuses)s

					AND b.check_in < %(check_out)s
					AND b.check_out > %(check_in)s
				""",
				{
					"room": row.room,
					"booking": self.name or "",
					"blocking_statuses": blocking_statuses,
					"check_in": self.check_in,
					"check_out": self.check_out,
				},
				as_dict=True,
			)

			if existing_bookings:
				booking = existing_bookings[0]

				frappe.throw(
					f"""
					Room <b>{row.room}</b> is already booked.

					<br><br>
					Existing Booking:
					<b>{booking.name}</b>

					<br>
					Check-in:
					<b>{booking.check_in}</b>

					<br>
					Check-out:
					<b>{booking.check_out}</b>
					"""
				)

	def validate_status_transition(self):
		if self.is_new():
			return
		previous_status = self.get_doc_before_save().status
		if self.status not in ALLOWED_NEXT_STATUS.get(previous_status, set()):
			frappe.throw(_("Booking cannot move from {0} to {1}").format(previous_status, self.status))

	def is_transitioning_to(self, status):
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
		if self.flags.get("system_cancel"):
			return
		user_roles = frappe.get_roles(frappe.session.user)
		# if "Resort Manager" not in user_roles and "System Manager" not in user_roles:
		# 	frappe.throw(_("Only a Resort Manager can cancel a booking"))

	def check_room_availability(self):
		for row in self.rooms:
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
		check_in = get_datetime(self.check_in)
		check_out = get_datetime(self.check_out)

		self.total_nights = (check_out.date() - check_in.date()).days
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

		frappe.msgprint(
				_("Refund entry created successfully."),
				title=_("Refund Created"),
				indicator="green"
			)

		frappe.enqueue(
			"resort_booking.resort_booking.doctype.booking_payment.booking_payment.update_refund_amount",
			booking=self.name,
			queue="long",
		)

	# ---- called by the scheduler --------------------------------------------

	def cancel_expired_pre_booking(self):
		self.flags.system_cancel = True
		self.status = "Cancelled"
		self.cancellation_reason = "Auto-cancelled: pre-booking was not confirmed within the hold period"
		self.save(ignore_permissions=True)



