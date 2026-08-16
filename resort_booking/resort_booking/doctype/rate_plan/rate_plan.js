// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rate Plan", {
	validate(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.from_date > frm.doc.to_date) {
			frappe.throw(__("From Date cannot be after To Date"));
		}
		if (frm.doc.rate_per_night <= 0) {
			frappe.throw(__("Rate Per Night must be greater than zero"));
		}
	},
});
