import frappe
from frappe import _
from frappe.model.document import Document

from resort_booking.resort_booking.notifications import send_payment_receipt


class BookingPayment(Document):
	def validate(self):
		if self.amount <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		if self.payment_type == "Refund" and not self.flags.get("system_refund"):
			self.validate_refund_permission()

	def validate_refund_permission(self):
		user_roles = frappe.get_roles(frappe.session.user)
		if "Resort Manager" not in user_roles and "System Manager" not in user_roles:
			frappe.throw(_("Only a Resort Manager can record a Refund"))

	def on_submit(self):
		self.update_booking_totals()
		if self.payment_type in ("Advance", "Balance"):
			send_payment_receipt(self)

	def on_cancel(self):
		self.update_booking_totals()

	def update_booking_totals(self):
		"""Recompute the booking's Advance Paid from the ledger of submitted
		Booking Payment rows, instead of incrementing/decrementing a counter -
		this way it can never drift out of sync."""
		total_paid = frappe.db.sql(
			"""
			select
				sum(case when payment_type in ('Advance', 'Balance') then amount else 0 end)
				- sum(case when payment_type = 'Refund' then amount else 0 end)
			from `tabBooking Payment`
			where booking = %s and docstatus = 1
			""",
			self.booking,
		)[0][0] or 0

		booking = frappe.get_doc("Resort Booking", self.booking)
		booking.advance_paid = total_paid
		booking.save(ignore_permissions=True)
