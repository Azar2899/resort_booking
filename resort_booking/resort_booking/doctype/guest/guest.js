// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Guest", {
	phone(frm) {
		// Basic sanity check only - not a strict format validator, just
		// catches obvious typos (too short to be a real phone number).
		// if (frm.doc.phone && frm.doc.phone.replace(/\D/g, "").length < 7) {
		// 	frappe.msgprint(__("Phone number looks too short - please double-check it."));
		// }
	},
});
