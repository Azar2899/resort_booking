import frappe

from resort_booking.resort_booking.utils import get_settings

settings = get_settings()
management_email = settings.management_alert_email

def send_booking_confirmation(booking):
	guest_email = frappe.db.get_value("Guest", booking.guest, "email")
	if not guest_email:
		return

	resource_booking_link = create_resource_booking_link(booking)

	subject, message = _render(
		get_settings().booking_confirmation_template,
		{
			"booking": booking,
			"resource_booking_link": resource_booking_link,
		},
		fallback_subject=f"Booking Confirmed - {booking.name}",
		fallback_message=(
			f"Dear Guest,<br><br>"
			f"Your booking <b>{booking.name}</b> "
			f"from {booking.check_in} to {booking.check_out} is confirmed.<br>"
			f"Grand Total: {booking.grand_total}<br>"
			f"Advance Paid: {booking.advance_paid}<br><br>"

			f"<a href='{resource_booking_link}' "
			f"style='background:#2490ef;"
			f"color:white;"
			f"padding:10px 18px;"
			f"text-decoration:none;"
			f"border-radius:5px;'>"
			f"Book Pool / Game Area"
			f"</a>"

			f"<br><br>"
			f"Thank you for choosing us."
		),
	)

	
	if guest_email:
		_send(
			[guest_email],
			subject,
			message
		)

	
	if management_email:
		_send(
			[management_email],
			f"[Management Alert] Booking Confirmed - {booking.name}",
			(
				f"Booking <b>{booking.name}</b> has been confirmed.<br><br>"
				f"Guest: {booking.guest}<br>"
				f"Check-in: {booking.check_in}<br>"
				f"Check-out: {booking.check_out}<br>"
				f"Grand Total: {booking.grand_total}<br>"
				f"Advance Paid: {booking.advance_paid}<br>"
				f"Balance Due: {booking.balance_due}"
			),
		)



def send_payment_receipt(payment):
	booking = frappe.get_doc("Resort Booking", payment.booking)
	guest_email = frappe.db.get_value("Guest", booking.guest, "email")
	if not guest_email:
		return

	subject, message = _render(
		get_settings().payment_receipt_template,
		{"booking": booking, "payment": payment},
		fallback_subject=f"Payment Receipt - {payment.name}",
		fallback_message=(
			f"Dear Guest,<br><br>We received a payment of <b>{payment.amount}</b> "
			f"({payment.payment_type}) against booking {booking.name}.<br>"
			f"Balance Due: {booking.balance_due}<br><br>Thank you."
		),
	)

	if guest_email:
		_send(
			[guest_email],
			subject,
			message
		)

	if management_email:
		_send(
			[management_email],
			f"[Management Alert] Payment Received - {booking.name}",
			(
				f"A payment has been received for booking "
				f"<b>{booking.name}</b>.<br><br>"
				f"Payment: {payment.name}<br>"
				f"Guest: {booking.guest}<br>"
				f"Payment Type: {payment.payment_type}<br>"
				f"Amount: {payment.amount}<br>"
				f"Balance Due: {booking.balance_due}"
			),
		)


def send_cancellation_emails(booking):
	subject, message = _render(
		get_settings().booking_cancellation_template,
		{"booking": booking},
		fallback_subject=f"Booking Cancelled - {booking.name}",
		fallback_message=(
			f"Dear Guest,<br><br>Your booking <b>{booking.name}</b> has been cancelled.<br>"
			f"Reason: {booking.cancellation_reason}<br><br>"
			f"Any refund due will be processed shortly."
		),
	)

	guest_email = frappe.db.get_value("Guest", booking.guest, "email")
	if guest_email:
		_send([guest_email], subject, message)

	management_email = get_settings().management_alert_email
	if management_email:
		_send(
			[management_email],
			f"[Alert] Booking Cancelled - {booking.name}",
			(
				f"Booking {booking.name} for guest {booking.guest} was cancelled.<br>"
				f"Reason: {booking.cancellation_reason}"
			),
		)


def send_prebooking_reminder(booking):
	guest_email = frappe.db.get_value("Guest", booking.guest, "email")
	if not guest_email:
		return

	subject, message = _render(
		get_settings().prebooking_reminder_template,
		{"booking": booking},
		fallback_subject=f"Reminder: Check-in Tomorrow - {booking.name}",
		fallback_message=(
			f"Dear Guest,<br><br>This is a reminder that check-in for booking "
			f"<b>{booking.name}</b> is scheduled for {booking.check_in}.<br><br>"
			f"We look forward to hosting you."
		),
	)
	
	if guest_email:
		_send(
			[guest_email],
			subject,
			message
		)

	if management_email:
		_send(
			[management_email],
			f"[Management Alert] Pre-booking Reminder - {booking.name}",
			(
				f"Booking <b>{booking.name}</b> is still pre-booked "
				f"and check-in is scheduled within 24 hours.<br><br>"
				f"Guest: {booking.guest}<br>"
				f"Check-in: {booking.check_in}<br>"
				f"Check-out: {booking.check_out}<br>"
				f"Grand Total: {booking.grand_total}<br>"
				f"Advance Paid: {booking.advance_paid}<br>"
				f"Balance Due: {booking.balance_due}"
			),
		)



def _render(template_name, context, fallback_subject, fallback_message):
	"""Use the Email Template configured in Resort Settings if there is one,
	otherwise fall back to a plain built-in message. This is what makes the
	email content configurable without code, per the Story 5 requirement."""
	if not template_name:
		return fallback_subject, fallback_message

	template = frappe.get_doc("Email Template", template_name)
	subject = frappe.render_template(template.subject, context)
	message = frappe.render_template(template.response, context)
	return subject, message


def _send(recipients, subject, message):
	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message
		)

	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Resort Booking: failed to send email"
		)


def create_resource_booking_link(booking):
    base_url = frappe.utils.get_url()

    return (
        f"{base_url}/resource-booking"
        f"?booking={frappe.utils.quote(booking.name)}"
        f"&guest={frappe.utils.quote(booking.guest)}"
    )