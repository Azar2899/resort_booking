import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate


class RatePlan(Document):
	def validate(self):
		self.from_date = getdate(self.from_date)
		self.to_date = getdate(self.to_date)
		if self.from_date > self.to_date:
			frappe.throw(_("From Date cannot be after To Date"))
		self.check_overlap_with_other_plans()

	def check_overlap_with_other_plans(self):
		overlapping = frappe.db.sql(
			"""
			select name from `tabRate Plan`
			where room_type = %(room_type)s
				and name != %(name)s
				and from_date <= %(to_date)s
				and to_date >= %(from_date)s
			""",
			{
				"room_type": self.room_type,
				"name": self.name or "New Rate Plan",
				"from_date": self.from_date,
				"to_date": self.to_date,
			},
		)
		if overlapping:
			frappe.throw(
				_("Rate Plan {0} already covers an overlapping date range for this Room Type").format(
					overlapping[0][0]
				)
			)
