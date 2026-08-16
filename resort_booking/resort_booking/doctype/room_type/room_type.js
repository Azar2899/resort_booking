// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Room Type", {
	validate(frm) {
		if (frm.doc.default_rate <= 0) {
			frappe.throw(__("Default Rate Per Night must be greater than zero"));
		}
	},
});
