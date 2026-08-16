app_name = "resort_booking"
app_title = "Resort Booking"
app_publisher = "Azar"
app_description = "Resort Booking Management System"
app_email = "azar.m.90804@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "resort_booking",
# 		"logo": "/assets/resort_booking/logo.png",
# 		"title": "Resort Booking",
# 		"route": "/resort_booking",
# 		"has_permission": "resort_booking.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/resort_booking/css/resort_booking.css"
# app_include_js = "/assets/resort_booking/js/resort_booking.js"

# include js, css files in header of web template
# web_include_css = "/assets/resort_booking/css/resort_booking.css"
# web_include_js = "/assets/resort_booking/js/resort_booking.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "resort_booking/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
doctype_calendar_js = {"Resort Booking": "public/js/resort_booking_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "resort_booking/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "resort_booking.utils.jinja_methods",
# 	"filters": "resort_booking.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "resort_booking.install.before_install"
# after_install = "resort_booking.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "resort_booking.uninstall.before_uninstall"
# after_uninstall = "resort_booking.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "resort_booking.utils.before_app_install"
# after_app_install = "resort_booking.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "resort_booking.utils.before_app_uninstall"
# after_app_uninstall = "resort_booking.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "resort_booking.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------


fixtures = [
	{
		"dt": "Role",
		"filters": [
			["name", "in", [
				"Resort Sales Manager",
				"Resort Owner",
				"Resort Manager",
				"Receptionist"
			]]
		]
	},
	{
		"dt": "Custom DocPerm",
		"filters": [
			["name", "in", [
				"4ivkechdp0",
				"3rqf7uavjs",
				"3dli5n6jqn",
				"tt5lafklh7",
				"rindrub6f9",
				"pj1cl2i3j8",
				"paudetrpgl",
				"ovce0dvokn",
				"olave4q5ug",
				"d7c9usdhe4",
				"d0ls9a0jje",
				"co8d42jtfr",
				"cc5ao7ojsb",
				"c4dkpn091v",
				"buugkc7end",
				"biup2dq90g",
				"bf4dqc7q6o",
				"bbpvisrbi0",
				"b5sq35brcn",
				"96pktp5qj1",
				"6cd3el11fa",
				"6cdksu8hod",
				"6cdcat1opr",
				"6cctnl83ua",
				"64kkt0ud65",
				"64kknods2i",
				"64k02t61vd",
				"64khdkloq6",
				"5rh5flrms3",
				"5rgm7vibn1",
				"5bri5012sj",
				"560h9a3j65",
				"5606i9q1k6",
				"4vpss6veok",
				"4mepc7nf1r",
				"4meml8rmp6",
				"4dvsr08knv",
				"4durkm6et3",
				"48ojtc6md8",
				"48nmqac2ll",
				"41t7chq86h",
				"41t08c69ri",
				"3rfc0jv9d0",
				"3rf1bsp9gn",
				"3rf8ka7qn0",
				"27clcjdfjp",
				"27crip6d1j",
				"27bc0cfc6a",
				"215ohdji5k",
				"215lfvr8op",
				"215sot970e",
				"1pbc28d2s0",
				"1pbf42igbi",
				"1pb5hl6ifn"
			]]
		]
	},
	{
		"dt": "Workspace",
		"filters": [
			["name", "in", [
				"Resort Management"
			]]
		]
	}
]

scheduler_events = {
	"hourly": [
		"resort_booking.resort_booking.tasks.expire_pre_bookings",
	],
	"daily": [
		"resort_booking.resort_booking.tasks.send_prebooking_reminders",
	],
}

# Testing
# -------

# before_tests = "resort_booking.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "resort_booking.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "resort_booking.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["resort_booking.utils.before_request"]
# after_request = ["resort_booking.utils.after_request"]

# Job Events
# ----------
# before_job = ["resort_booking.utils.before_job"]
# after_job = ["resort_booking.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"resort_booking.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

