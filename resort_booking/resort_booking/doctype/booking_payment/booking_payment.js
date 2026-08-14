frappe.ui.form.on("Booking Payment", {
	setup(frm) {
		// Hide "Refund" from the dropdown for anyone who isn't a Resort
		// Manager/System Manager - this only improves the UX (no point
		// offering an option that will just be rejected). The real
		// enforcement is server-side in booking_payment.py
		// validate_refund_permission(), which this cannot bypass.
		const can_refund = frappe.user.has_role(["Resort Manager", "System Manager"]);
		if (!can_refund) {
			frm.set_df_property("payment_type", "options", ["Advance", "Balance"]);
		}
	},

	amount(frm) {
		if (frm.doc.amount && frm.doc.amount <= 0) {
			frappe.msgprint(__("Amount must be greater than zero"));
		}
	},
});
