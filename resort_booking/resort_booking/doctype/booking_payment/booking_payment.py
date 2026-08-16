import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from resort_booking.resort_booking.notifications import send_payment_receipt

class BookingPayment(Document):
	def validate(self):
		if self.amount <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		booking = frappe.get_doc("Resort Booking", self.booking)

		if self.payment_type in ("Advance", "Balance"):
			balance_due = flt(booking.balance_due)

			if self.amount > balance_due:
				frappe.throw(
					_(
						"Payment amount ({0}) cannot be greater than the Balance Due ({1})."
					).format(
						frappe.format_value(self.amount, {"fieldtype": "Currency"}),
						frappe.format_value(balance_due, {"fieldtype": "Currency"})
					)
				)

		if self.payment_type == "Refund" and not self.flags.get("system_refund"):
			self.validate_refund_permission()

	def validate_refund_permission(self):
		user_roles = frappe.get_roles(frappe.session.user)
		if "Resort Manager" not in user_roles and "System Manager" not in user_roles:
			# frappe.throw(_("Only a Resort Manager can record a Refund"))
			return

	def on_submit(self):
		self.update_booking_totals()
		if self.payment_type in ("Advance", "Balance"):
			send_payment_receipt(self)
		if self.payment_type == "Refund":
			booking = frappe.get_doc("Resort Booking", self.booking)
			frappe.db.set_value("Resort Booking", booking.name, "refund_amount", flt(self.amount))
		

	def on_cancel(self):
		self.update_booking_totals()

	def update_booking_totals(self):
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

		refund_total = frappe.db.sql(
			"""
			select sum(amount)
			from `tabBooking Payment`
			where booking = %s and payment_type = 'Refund' and docstatus = 1
			""",
			self.booking,
		)[0][0] or 0

		booking = frappe.get_doc("Resort Booking", self.booking)
		booking.advance_paid = total_paid
		booking.refund_amount = refund_total
		
		minimum_advance = booking.min_advance_required or 0

		if booking.status in ("Draft", "Pre-booked", "Confirmed"):

			if total_paid >= minimum_advance:
				booking.status = "Confirmed"
			else:
				booking.status = "Pre-booked"

		booking.save(ignore_permissions=True)


	def update_refund_amount(booking, amount):
		booking_doc = frappe.get_doc("Resort Booking", booking)

		frappe.db.set_value(
			"Resort Booking",
			booking_doc.name,
			"refund_amount",
			flt(amount)
		)

		frappe.db.commit()

	

