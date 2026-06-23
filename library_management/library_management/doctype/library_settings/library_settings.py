# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LibrarySettings(Document):

    def validate(self):
        if self.default_loan_period_days and self.default_loan_period_days <= 0:
            frappe.throw(_("Default Loan Period must be greater than zero."))
        if self.default_fine_per_day and self.default_fine_per_day < 0:
            frappe.throw(_("Default Fine Per Day cannot be negative."))


# ------------------------------------------------------------------
# Public helpers — used by all other controllers
# ------------------------------------------------------------------

@frappe.whitelist()
def get_library_settings():
    """Return the Library Settings singleton."""
    return frappe.get_single("Library Settings")


def get_payment_account(payment_mode):
    """
    Resolve the correct GL account based on payment mode.
    Falls back to cash_account if the specific account is not configured.
    """
    settings = frappe.get_single("Library Settings")

    mode = (payment_mode or "").strip()

    if mode == "Cash":
        return settings.cash_account or settings.member_receivable_account
    elif mode in ("Bank Transfer", "Cheque"):
        return settings.bank_account or settings.cash_account
    elif mode == "UPI":
        return settings.upi_account or settings.cash_account

    # Default fallback
    return settings.cash_account or settings.member_receivable_account
