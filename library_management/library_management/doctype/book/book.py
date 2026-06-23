# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Book(Document):

    def before_save(self):
        """Set available_copies to total_copies on first save (new doc)."""
        if self.is_new() and (self.available_copies is None or self.available_copies == 0):
            self.available_copies = self.total_copies or 1

    def validate(self):
        self._validate_copies()
        self._set_availability_status()

    def _validate_copies(self):
        total = self.total_copies or 0
        available = self.available_copies or 0

        if total < 0:
            frappe.throw(_("Total Copies cannot be negative."))

        if available < 0:
            frappe.throw(_("Available Copies cannot be negative."))

        if available > total:
            frappe.throw(
                _("Available Copies ({0}) cannot exceed Total Copies ({1}).").format(
                    available, total
                )
            )

    def _set_availability_status(self):
        total = self.total_copies or 0
        available = self.available_copies or 0

        if available == 0:
            self.availability_status = "Not Available"
        elif available >= total:
            self.availability_status = "Available"
        else:
            self.availability_status = "Partially Available"
