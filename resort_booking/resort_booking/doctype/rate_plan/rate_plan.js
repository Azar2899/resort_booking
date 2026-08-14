// Copyright (c) 2026, Prithivraj Thangadurai and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rate Plan", {
	// Mirrors the server-side check in rate_plan.py - the server still
	// re-validates on save (including the overlap check, which needs a DB
	// query and can't be done client-side), this just fails fast.
	validate(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.from_date > frm.doc.to_date) {
			frappe.throw(__("From Date cannot be after To Date"));
		}
		if (frm.doc.rate_per_night <= 0) {
			frappe.throw(__("Rate Per Night must be greater than zero"));
		}
	},
});
