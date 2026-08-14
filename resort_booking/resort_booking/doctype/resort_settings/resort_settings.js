// Copyright (c) 2026, Prithivraj Thangadurai and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resort Settings", {
	validate(frm) {
		if (frm.doc.advance_percent <= 0 || frm.doc.advance_percent > 100) {
			frappe.throw(__("Minimum Advance Percent must be between 0 and 100"));
		}
		if (frm.doc.pre_booking_hold_hours <= 0) {
			frappe.throw(__("Pre-booking Hold Hours must be greater than zero"));
		}
	},
});
