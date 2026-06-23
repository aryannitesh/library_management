# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class LibraryMember(Document):

    def before_save(self):
        self._recalculate_outstanding_fines()

    def validate(self):
        self._validate_membership_dates()
        self._set_membership_status()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_membership_dates(self):
        if self.membership_start_date and self.membership_end_date:
            if getdate(self.membership_end_date) < getdate(self.membership_start_date):
                frappe.throw(
                    _("Membership End Date cannot be earlier than Membership Start Date.")
                )

    def _set_membership_status(self):
        # Suspended is a manually set state — preserve it
        if self.membership_status == "Suspended":
            return

        if self.membership_end_date and getdate(self.membership_end_date) < getdate(today()):
            self.membership_status = "Expired"
        else:
            self.membership_status = "Active"

    def _recalculate_outstanding_fines(self):
        """
        Sum outstanding_amount from all Library Fine records
        linked to this member where status != 'Paid'.
        Falls back to 0 if the Library Fine DocType doesn't exist yet
        (during initial migration before that module is installed).
        """
        if not frappe.db.exists("DocType", "Library Fine"):
            self.outstanding_fines = 0
            return

        result = frappe.db.sql(
            """
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM   `tabLibrary Fine`
            WHERE  member = %s
              AND  status != 'Paid'
            """,
            (self.name,),
        )
        self.outstanding_fines = result[0][0] if result else 0
