frappe.ui.form.on("Resource Booking", {
	validate(frm) {
		if (frm.doc.slot_start_time && frm.doc.slot_end_time && frm.doc.slot_end_time <= frm.doc.slot_start_time) {
			frappe.throw(__("Slot End Time must be after Slot Start Time"));
		}
	},

	async validate(frm) {

        if (!frm.doc.resource || !frm.doc.slot_date ||
            !frm.doc.slot_start_time || !frm.doc.slot_end_time) {
            return;
        }

        if (frm.doc.slot_start_time >= frm.doc.slot_end_time) {
            frappe.msgprint({
                title: __("Invalid Time"),
                message: __("Slot End Time must be after Slot Start Time."),
                indicator: "red"
            });

            frappe.validated = false;
            return;
        }

        const bookings = await frappe.db.get_list("Resource Booking", {
            filters: {
                resource: frm.doc.resource,
                slot_date: frm.doc.slot_date,
                status: "Booked",
                name: ["!=", frm.doc.name]
            },
            fields: [
                "name",
                "slot_start_time",
                "slot_end_time",
                
                "guest"
            ],
            limit_page_length: 500
        });

        const new_start = frm.doc.slot_start_time;
        const new_end = frm.doc.slot_end_time;

        for (const booking of bookings) {

            const existing_start = booking.slot_start_time;
            const existing_end = booking.slot_end_time;


            if (
                new_start < existing_end &&
                new_end > existing_start
            ) {

                frappe.msgprint({
                    title: __("Resource Already Booked"),
                    message: __(
                        "The resource <b>{0}</b> is already booked on <b>{1}</b> from <b>{2}</b> to <b>{3}</b>.Your selected time <b>{4}</b> to <b>{5}</b> overlaps with this booking.",
                        [
                            frm.doc.resource,
                            frappe.datetime.str_to_user(booking.slot_date || frm.doc.slot_date),
                            existing_start,
                            existing_end,
                            new_start,
                            new_end
                        ]
                    ),
                    indicator: "red"
                });

                frappe.validated = false;
                return;
            }
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
