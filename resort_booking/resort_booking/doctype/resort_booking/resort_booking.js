frappe.ui.form.on("Resort Booking", {
	setup(frm) {
		// Only offer rooms that aren't under maintenance in the child table -
		// the server still re-checks real availability on save, this just
		// saves the receptionist a failed round trip for the obvious case.
		frm.set_query("room", "rooms", () => {
			return { filters: { status: ["!=", "Under Maintenance"] } };
		});
	},

	refresh(frm) {
		frm.trigger("add_check_availability_button");
	},

	check_in(frm) {
		frm.trigger("add_check_availability_button");
	},

	check_out(frm) {
		frm.trigger("add_check_availability_button");
	},

	validate(frm) {
		// Fast client-side check before the round trip - the server (see
		// resort_booking.py validate_dates()) is still the real authority and
		// re-checks this itself, so nothing here is a security control.
		if (frm.doc.check_in && frm.doc.check_out && frm.doc.check_out <= frm.doc.check_in) {
			frappe.throw(__("Check-out Date must be after Check-in Date"));
		}
		if (!(frm.doc.rooms || []).length) {
			frappe.throw(__("Add at least one room before saving"));
		}
	},

	add_check_availability_button(frm) {
		frm.clear_custom_buttons();
		if (!frm.doc.check_in || !frm.doc.check_out) return;

		frm.add_custom_button(__("Check Availability"), () => {
			frappe.call({
				method: "resort_booking.resort_booking.api.check_availability",
				args: { check_in: frm.doc.check_in, check_out: frm.doc.check_out },
				callback(r) {
					show_available_rooms(r.message || []);
				},
			});
		});
	},
});

function show_available_rooms(rooms) {
	if (!rooms.length) {
		frappe.msgprint(__("No rooms are free for these dates."));
		return;
	}

	const rows = rooms
		.map(
			(room) =>
				`<tr><td>${frappe.utils.escape_html(room.name)}</td>` +
				`<td>${frappe.utils.escape_html(room.room_type)}</td>` +
				`<td>${frappe.utils.escape_html(room.room_category)}</td></tr>`
		)
		.join("");

	frappe.msgprint({
		title: __("Available Rooms"),
		message:
			`<table class="table table-bordered"><thead><tr>` +
			`<th>${__("Room")}</th><th>${__("Type")}</th><th>${__("Category")}</th>` +
			`</tr></thead><tbody>${rows}</tbody></table>`,
	});
}
