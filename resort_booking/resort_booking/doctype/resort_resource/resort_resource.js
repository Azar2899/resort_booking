// Copyright (c) 2026, Prithivraj Thangadurai and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resort Resource", {
	// Mirrors the server-side check in resource_booking.py - the server is
	// still the real authority for anything that touches other documents.
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
