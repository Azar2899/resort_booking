frappe.ui.form.on("Resource Booking", {
	validate(frm) {
		// Fast client-side check before the round trip - the server (see
		// resource_booking.py validate_times()) is still the real authority
		// and re-checks this itself, so nothing here is a security control.
		if (frm.doc.slot_start_time && frm.doc.slot_end_time && frm.doc.slot_end_time <= frm.doc.slot_start_time) {
			frappe.throw(__("Slot End Time must be after Slot Start Time"));
		}
	},

	resource(frm) {
		frm.trigger("show_slot_button");
	},
	slot_date(frm) {
		frm.trigger("show_slot_button");
	},

	show_slot_button(frm) {
		frm.clear_custom_buttons();
		if (!frm.doc.resource || !frm.doc.slot_date) return;

		frm.add_custom_button(__("View Booked Slots"), () => {
			frappe.call({
				method: "resort_booking.resort_booking.api.get_resource_slots",
				args: { resource: frm.doc.resource, slot_date: frm.doc.slot_date },
				callback(r) {
					show_booked_slots(r.message);
				},
			});
		});
	},
});

function show_booked_slots(data) {
	if (!data) return;

	if (!data.booked_slots.length) {
		frappe.msgprint(__("No slots booked yet for {0} capacity - {1}.", [data.resource, data.capacity]));
		return;
	}

	const rows = data.booked_slots
		.map((slot) => `<tr><td>${slot.slot_start_time}</td><td>${slot.slot_end_time}</td></tr>`)
		.join("");

	frappe.msgprint({
		title: __("Booked Slots - {0} (capacity {1})", [data.resource, data.capacity]),
		message:
			`<table class="table table-bordered"><thead><tr>` +
			`<th>${__("Start")}</th><th>${__("End")}</th>` +
			`</tr></thead><tbody>${rows}</tbody></table>`,
	});
}
