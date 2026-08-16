// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Room Type", {
	validate(frm) {
		if (frm.doc.default_rate <= 0) {
			frappe.throw(__("Default Rate Per Night must be greater than zero"));
		}
	},
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button("Rate Plan", function () {
			frappe.new_doc("Rate Plan", {
				room_type: frm.doc.name
			});
		});
	}
});
