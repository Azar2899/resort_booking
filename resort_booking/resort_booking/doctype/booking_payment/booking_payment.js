frappe.ui.form.on("Booking Payment", {
	// setup(frm) {
	// 	const can_refund = frappe.user.has_role(["Resort Manager", "Resort Sales Manager","System Manager"]);
	// 	if (!can_refund) {
	// 		frm.set_df_property("payment_type", "options", ["Advance", "Balance"]);
	// 	}
	// },

	amount(frm) {
		if (frm.doc.amount && frm.doc.amount <= 0) {
			frappe.msgprint(__("Amount must be greater than zero"));
		}
	},
});
