frappe.views.calendar["Resort Booking"] = {
	field_map: {
		start: "check_in",
		end: "check_out",
		id: "name",
		title: "guest",
		allDay: 1,
		status: "status",
	},
	gantt: false,
	filters: [
		{
			fieldtype: "Link",
			fieldname: "guest",
			options: "Guest",
			label: __("Guest"),
		},
		{
			fieldtype: "Select",
			fieldname: "status",
			options: "Draft\nPre-booked\nConfirmed\nChecked-in\nChecked-out\nCancelled",
			label: __("Status"),
		},
	],
	get_events_method: "frappe.desk.calendar.get_events",
};
