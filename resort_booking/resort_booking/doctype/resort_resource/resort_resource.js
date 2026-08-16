// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resort Resource", {
	
	validate(frm) {
		if (
			frm.doc.operating_hours_from &&
			frm.doc.operating_hours_to &&
			frm.doc.operating_hours_to <= frm.doc.operating_hours_from
		) {
			frappe.throw(__("Operating Hours To must be after Operating Hours From"));
		}
		if (frm.doc.capacity <= 0) {
			frappe.throw(__("Capacity must be greater than zero"));
		}
	},
});
