import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time


class ResourceBooking(Document):
	def validate(self):
		self.validate_times()
		if self.status == "Booked":
			self.check_slot_capacity()

	def validate_times(self):
		# Time fields can arrive as a string (from the UI/API) or a timedelta
		# (when read back from the database) - normalize both sides to
		# datetime.time before comparing, otherwise "<" raises a TypeError.
		start_time = get_time(self.slot_start_time)
		end_time = get_time(self.slot_end_time)
		if end_time <= start_time:
			frappe.throw(_("Slot End Time must be after Slot Start Time"))

		resource = frappe.get_cached_doc("Resort Resource", self.resource)
		if start_time < get_time(resource.operating_hours_from):
			frappe.throw(_("{0} opens at {1}").format(self.resource, resource.operating_hours_from))
		if end_time > get_time(resource.operating_hours_to):
			frappe.throw(_("{0} closes at {1}").format(self.resource, resource.operating_hours_to))

	def check_slot_capacity(self):
		# Lock the Resort Resource row first so two guests booking the same
		# slot at the same time can't both slip past the capacity count below.
		frappe.db.get_value("Resort Resource", self.resource, "name", for_update=True)

		overlapping_count = frappe.db.count(
			"Resource Booking",
			filters={
				"resource": self.resource,
				"status": "Booked",
				"slot_date": self.slot_date,
				"name": ["!=", self.name or "New Resource Booking"],
				"slot_start_time": ["<", self.slot_end_time],
				"slot_end_time": [">", self.slot_start_time],
			},
		)

		capacity = frappe.db.get_value("Resort Resource", self.resource, "capacity") or 1
		if overlapping_count >= capacity:
			frappe.throw(
				_("{0} is fully booked for {1} - {2} on {3}").format(
					self.resource, self.slot_start_time, self.slot_end_time, self.slot_date
				)
			)
