// Copyright (c) 2026, Azar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Room", {
	refresh(frm) {
		const indicator_by_status = {
			Available: "green",
			Occupied: "orange",
			"Under Maintenance": "red",
		};
		const color = indicator_by_status[frm.doc.status];
		if (color) {
			frm.page.set_indicator(frm.doc.status, color);
		}
		set_maintanance_button(frm);

	},
});

function set_maintanance_button(frm) {
	if (frm.is_new()) {
			return;
		}

		if (frm.doc.status !== "Under Maintenance") {
			frm.add_custom_button("Under Maintenance", function () {
				frappe.confirm(
					"Are you sure you want to mark this room as Under Maintenance?",
					function () {
						frm.set_value("status", "Under Maintenance");
						frm.save();
					}
				);
			});
		}
	}