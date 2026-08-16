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
	},
});
