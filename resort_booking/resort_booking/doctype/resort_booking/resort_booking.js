frappe.ui.form.on("Resort Booking", {
	setup(frm) {
		frm.set_query("room", "rooms", function (cdt, cdn) {
			if (!frm.doc.check_in || !frm.doc.check_out) {
				return {
					filters: {
						name: ["=", "__NO_ROOM__"]
					}
				};
			}

			if (!frm.available_rooms || !frm.available_rooms.length) {
				return {
					filters: {
						name: ["=", "__NO_ROOM__"]
					}
				};
			}

			const selected_rooms = (frm.doc.rooms || [])
				.filter(row => row.name !== cdn && row.room)
				.map(row => row.room);

			const filters = [
				["Room", "status", "!=", "Under Maintenance"],
				["Room", "name", "in", frm.available_rooms]
			];

			if (selected_rooms.length) {
				filters.push([
					"Room",
					"name",
					"not in",
					selected_rooms
				]);
			}

			return {
				filters: filters
			};
		});
	},
	status(frm) {
		set_rooms_read_only(frm);
		if (frm.doc.balance_due == 0 && frm.doc.status == "Checked-out") {
			frappe.throw(__("Cannot change status to {0} when balance due is 0", [frm.doc.status]));
		}
	},

	refresh(frm) {
		set_rooms_read_only(frm);
		if (!["Draft", "Pre-Booked"].includes(frm.doc.status)) {
            frm.set_df_property("guests_staying", "read_only", 1);
        }
		if (frm.doc.status === "Cancelled") {
             frm.disable_form();
        }
		frm.toggle_display(
			"rooms",
			!!frm.doc.check_in && !!frm.doc.check_out
		);

		add_payment_button(frm);
		set_booking_editability(frm);
		frm.trigger("add_check_availability_button");


		frm.toggle_display(
			"pre_booking_expires_on",
			frm.doc.status === "Pre-booked"
		);

	},

	check_in(frm) {
		frm.trigger("add_check_availability_button");
		load_available_rooms(frm);
		update_room_rates(frm);

	},

	check_out(frm) {
		frm.trigger("add_check_availability_button");
		if (frm.doc.check_in && frm.doc.check_out && frm.doc.check_out < frm.doc.check_in) {
			frappe.throw(__("Check-out Date must be after Check-in Date"));
		}
		load_available_rooms(frm);
		frm.toggle_display(
			"rooms",
			!!frm.doc.check_in && !!frm.doc.check_out
		);
		update_room_rates(frm);

	},

	validate(frm) {
		validate_guest_occupancy(frm);

		if (frm.doc.balance_due > 0 && frm.doc.status == "Checked-out") {
			frappe.throw(__("Cannot change status to {0} when balance due is {1}", [frm.doc.status, frm.doc.balance_due]));
		}

		if (frm.doc.check_in && frm.doc.check_out && frm.doc.check_out <= frm.doc.check_in) {
			frappe.throw(__("Check-out Date must be after Check-in Date"));
		}
		if (!(frm.doc.rooms || []).length) {
			frappe.throw(__("Add at least one room before saving"));
		}


	},

	add_check_availability_button(frm) {

		frm.remove_custom_button("Check Availability");

		if (!frm.doc.check_in || !frm.doc.check_out) {
			return;
		}

		if (frm.doc.status === "Cancelled" || frm.doc.status === "Checked-out") {
			return;
		}

		frm.add_custom_button(__("Check Availability"), () => {

			if (frm.doc.check_out <= frm.doc.check_in) {
				frappe.msgprint({
					title: __("Invalid Dates"),
					message: __("Check-out must be after Check-in."),
					indicator: "red"
				});
				return;
			}

			frappe.call({
				method: "resort_booking.resort_booking.api.check_availability",
				args: {
					check_in: frm.doc.check_in,
					check_out: frm.doc.check_out
				},
				callback(r) {
					show_available_rooms(r.message || []);
				}
			});
		});
	},
	after_save(frm) {
        if (!["Draft", "Pre-Booked"].includes(frm.doc.status)) {
             frm.disable_form();
        }
    }

});

frappe.ui.form.on("Booking Room", {

	room(frm, cdt, cdn) {

		const row = locals[cdt][cdn];

		if (!row.room) {

			frappe.model.set_value(cdt, cdn, "max_occupancy", 0);
			frappe.model.set_value(cdt, cdn, "rate_per_night", 0);
			frappe.model.set_value(cdt, cdn, "nights", 0);
			frappe.model.set_value(cdt, cdn, "amount", 0);

			return;
		}
		// Prevent duplicate rooms
		const duplicate = (frm.doc.rooms || []).some(other_row =>
			other_row.name !== row.name &&
			other_row.room === row.room
		);

		if (duplicate) {

			frappe.msgprint({
				title: __("Duplicate Room"),
				message: __("Room {0} is already selected.", [row.room]),
				indicator: "red"
			});

			frappe.model.set_value(cdt, cdn, "room", "");

			return;
		}

		// Get Room
		frappe.db.get_doc("Room", row.room).then(room => {

			if (!room.room_type) {

				frappe.model.set_value(
					cdt,
					cdn,
					"max_occupancy",
					0
				);

				frappe.model.set_value(
					cdt,
					cdn,
					"rate_per_night",
					0
				);

				frappe.model.set_value(
					cdt,
					cdn,
					"amount",
					0
				);

				return;
			}

			// Get Room Type
			return frappe.db.get_doc(
				"Room Type",
				room.room_type
			);

		}).then(room_type => {

			if (!room_type) {
				return;
			}

			// Set Max Occupancy
			frappe.model.set_value(
				cdt,
				cdn,
				"max_occupancy",
				room_type.max_occupancy || 0
			);

			get_rate_for_room(
				frm,
				cdt,
				cdn,
				room_type.name
			);

		});
	},

	nights(frm, cdt, cdn) {
		calculate_booking_room_amount(frm, cdt, cdn);
	},

	rate_per_night(frm, cdt, cdn) {
		calculate_booking_room_amount(frm, cdt, cdn);
	}

});

function get_rate_for_room(frm, cdt, cdn, room_type) {

	if (!frm.doc.check_in || !frm.doc.check_out) {
		return;
	}

	frappe.db.get_list("Rate Plan", {
		filters: {
			room_type: room_type,
			from_date: ["<=", frm.doc.check_in],
			to_date: [">=", frm.doc.check_in]
		},
		fields: [
			"name",
			"plan_name",
			"rate_per_night",
			"from_date",
			"to_date"
		],
		order_by: "from_date desc",
		limit: 1
	}).then(rate_plans => {

		if (rate_plans.length) {

			const rate_plan = rate_plans[0];

			frappe.model.set_value(
				cdt,
				cdn,
				"rate_per_night",
				rate_plan.rate_per_night || 0
			);

			calculate_booking_room_amount(frm, cdt, cdn);

			return;
		}

		return frappe.db.get_value(
			"Room Type",
			room_type,
			"default_rate"
		).then(r => {

			const default_rate = flt(
				r.message && r.message.default_rate
			);

			if (default_rate > 0) {

				frappe.model.set_value(
					cdt,
					cdn,
					"rate_per_night",
					default_rate
				);

				calculate_booking_room_amount(frm, cdt, cdn);

				return;
			}

			frappe.msgprint({
				title: __("Rate Not Found"),
				message: __(
					"No Rate Plan or Default Rate found for Room Type {0}.",
					[room_type]
				),
				indicator: "red"
			});

			frappe.model.set_value(
				cdt,
				cdn,
				"rate_per_night",
				0
			);

			calculate_booking_room_amount(frm, cdt, cdn);
		});

	});
}


function calculate_booking_room_amount(frm, cdt, cdn) {

	const row = locals[cdt][cdn];

	const rate = flt(row.rate_per_night);
	const nights = flt(row.nights);

	const amount = rate * nights;

	frappe.model.set_value(
		cdt,
		cdn,
		"amount",
		amount
	);
}

function update_room_rates(frm) {

	if (!frm.doc.check_in || !frm.doc.check_out) {
		return;
	}

	(frm.doc.rooms || []).forEach(row => {

		if (!row.room) {
			return;
		}

		frappe.db.get_value(
			"Room",
			row.room,
			"room_type"
		).then(r => {

			if (!r.message || !r.message.room_type) {
				return;
			}

			get_rate_for_room(
				frm,
				row.doctype,
				row.name,
				r.message.room_type
			);

		});

	});
}


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



function validate_guest_occupancy(frm) {

	const guests_staying = flt(frm.doc.guests_staying);

	let total_max_occupancy = 0;

	(frm.doc.rooms || []).forEach(row => {
		total_max_occupancy += flt(row.max_occupancy);
	});

	if (guests_staying > total_max_occupancy) {

		frappe.msgprint({
			title: __("Occupancy Error"),
			message: __(
				"Guests Staying ({0}) exceeds the total room capacity ({1}). Please select additional rooms.",
				[guests_staying, total_max_occupancy]
			),
			indicator: "red"
		});

		frappe.validated = false;
	}
}

function set_booking_editability(frm) {

	const editable =
		frm.doc.status === "Draft" ||
		frm.doc.status === "Pre-booked";

	frm.set_df_property("check_in", "read_only", !editable);
	frm.set_df_property("check_out", "read_only", !editable);
}


function add_payment_button(frm) {

	// frm.remove_custom_button("Payment");
	if (frm.doc.status != "Confirmed" && frm.doc.status != "Checked-in") {
	if (flt(frm.doc.balance_due) > 0) {
		frappe.call({
			method: "resort_booking.resort_booking.api.get_booking_balance",
			args: {
				booking: frm.doc.name
			},
			callback: function (r) {
				if (r.message && flt(r.message) > 0) {
					frm.add_custom_button(
						"Payment",
						function () {
							frappe.new_doc("Booking Payment", {
								booking: frm.doc.name,
								payment_type: "Advance",
								amount: flt(r.message)
							});
						},
						"Create"
					);
				}
			}
		});

		return;
	}
	}

	if (frm.doc.status === "Confirmed" || frm.doc.status === "Checked-in") {
		if (flt(frm.doc.balance_due) > 0) {
			console.log("Balance due is greater than 0, adding Payment button");
			frappe.call({
				method: "resort_booking.resort_booking.api.get_booking_balance",
				args: {
					booking: frm.doc.name
				},
				callback: function (r) {
					if (r.message && flt(r.message) > 0) {
						frm.add_custom_button(
							"Payment",
							function () {
								frappe.new_doc("Booking Payment", {
									booking: frm.doc.name,
									payment_type: "Balance",
									amount: flt(r.message)
								});
							},
							"Create"
						);
					}
				}
			});
		}

		return;
	}

}


function load_available_rooms(frm) {

	frm.available_rooms = [];

	if (!frm.doc.check_in || !frm.doc.check_out) {
		frm.fields_dict.rooms.grid.refresh();
		return;
	}

	if (frm.doc.check_out <= frm.doc.check_in) {
		frm.fields_dict.rooms.grid.refresh();
		return;
	}

	frappe.call({
		method: "resort_booking.resort_booking.api.check_availability",
		args: {
			check_in: frm.doc.check_in,
			check_out: frm.doc.check_out
		},
		callback(r) {

			const rooms = r.message || [];

			// Store only available room names
			frm.available_rooms = rooms.map(room => room.name);

			// Refresh the Room link field in the child table
			frm.fields_dict.rooms.grid.refresh();

		}
	});
}


function set_rooms_read_only(frm) {
	const read_only = ["Confirmed", "Pre-booked", "Checked-in", "Checked-out", "Cancelled"].includes(frm.doc.status);

	frm.set_df_property("rooms", "read_only", read_only);

	if (frm.fields_dict.rooms && frm.fields_dict.rooms.grid) {
		frm.fields_dict.rooms.grid.wrapper
			.find(".grid-add-row")
			.toggle(!read_only);

		frm.fields_dict.rooms.grid.wrapper
			.find(".grid-remove-rows")
			.toggle(!read_only);

		frm.fields_dict.rooms.grid.cannot_add_rows = read_only;
		frm.fields_dict.rooms.grid.cannot_delete_rows = read_only;

		frm.refresh_field("rooms");
	}
}