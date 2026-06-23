# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class LibraryFinePayment(Document):

    def validate(self):
        self._validate_payment_rows()
        self._calculate_total()

    def on_submit(self):
        self._apply_payments_to_fines()
        self._update_member_outstanding_fines()
        self._create_payment_entry()

    def on_cancel(self):
        self._reverse_payments_from_fines()
        self._update_member_outstanding_fines()
        self._cancel_payment_entry()

    # ------------------------------------------------------------------
    # validate helpers
    # ------------------------------------------------------------------

    def _validate_payment_rows(self):
        if not self.fine_payments:
            frappe.throw(_("Please add at least one fine in the Fine Payments table."))

        for row in self.fine_payments:
            if flt(row.amount_to_pay) <= 0:
                frappe.throw(
                    _("Row {0}: Amount to Pay must be greater than zero.").format(row.idx)
                )
            outstanding = flt(
                frappe.db.get_value(
                    "Library Fine", row.library_fine, "outstanding_amount"
                )
            )
            if flt(row.amount_to_pay) > outstanding:
                frappe.throw(
                    _(
                        "Row {0}: Amount to Pay ({1}) cannot exceed the "
                        "outstanding amount ({2}) for fine {3}."
                    ).format(row.idx, row.amount_to_pay, outstanding, row.library_fine)
                )

    def _calculate_total(self):
        self.total_amount_paid = sum(
            flt(r.amount_to_pay) for r in (self.fine_payments or [])
        )

    # ------------------------------------------------------------------
    # apply / reverse payments on Library Fine records
    # ------------------------------------------------------------------

    def _apply_payments_to_fines(self):
        for row in self.fine_payments:
            fine = frappe.get_doc("Library Fine", row.library_fine)
            fine.amount_paid = flt(fine.amount_paid) + flt(row.amount_to_pay)
            fine.save(ignore_permissions=True)

    def _reverse_payments_from_fines(self):
        for row in self.fine_payments:
            fine = frappe.get_doc("Library Fine", row.library_fine)
            fine.amount_paid = max(0.0, flt(fine.amount_paid) - flt(row.amount_to_pay))
            fine.save(ignore_permissions=True)

    # ------------------------------------------------------------------
    # member outstanding balance
    # ------------------------------------------------------------------

    def _update_member_outstanding_fines(self):
        result = frappe.db.sql(
            """
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM   `tabLibrary Fine`
            WHERE  member    = %s
              AND  status   != 'Paid'
              AND  docstatus  = 1
            """,
            (self.member,),
        )
        outstanding = result[0][0] if result else 0
        frappe.db.set_value(
            "Library Member", self.member, "outstanding_fines", outstanding
        )

    # ------------------------------------------------------------------
    # Payment Entry — uses Library Settings for account resolution
    # ------------------------------------------------------------------

    def _create_payment_entry(self):
        from library_management.library_management.doctype.library_settings.library_settings import (
            get_payment_account,
        )

        company = self._get_company()
        if not company:
            frappe.log_error(
                "Library Fine Payment: No company found. Skipping Payment Entry.",
                "Library Fine Accounting",
            )
            return

        # Resolve payment (debit) account via Library Settings
        paid_to_account = get_payment_account(self.payment_mode)

        # Fallback: Mode of Payment Account table → Cash account
        if not paid_to_account:
            paid_to_account = frappe.db.get_value(
                "Mode of Payment Account",
                {"parent": self.payment_mode, "company": company},
                "default_account",
            )
        if not paid_to_account:
            paid_to_account = frappe.db.get_value(
                "Account",
                {"account_type": "Cash", "company": company, "is_group": 0},
                "name",
            )

        if not paid_to_account:
            frappe.log_error(
                "Library Fine Payment: Cannot resolve payment account for "
                "mode '{}'. Skipping.".format(self.payment_mode),
                "Library Fine Accounting",
            )
            return

        # Build Journal Entry references from linked Library Fine JEs
        references = []
        for row in self.fine_payments:
            je_name = frappe.db.get_value(
                "Library Fine", row.library_fine, "journal_entry"
            )
            if je_name:
                references.append({
                    "reference_doctype": "Journal Entry",
                    "reference_name":    je_name,
                    "allocated_amount":  flt(row.amount_to_pay),
                })

        pe = frappe.get_doc({
            "doctype":         "Payment Entry",
            "payment_type":    "Receive",
            "party_type":      "Customer",
            "party":           self.member,
            "company":         company,
            "posting_date":    self.payment_date or nowdate(),
            "mode_of_payment": self.payment_mode,
            "paid_to":         paid_to_account,
            "paid_amount":     flt(self.total_amount_paid),
            "received_amount": flt(self.total_amount_paid),
            "reference_no":    self.reference_number or self.name,
            "reference_date":  self.payment_date or nowdate(),
            "remarks":         "Fine payment received - Ref: {}".format(self.name),
            "references":      references,
        })
        pe.insert(ignore_permissions=True)
        pe.submit()

        frappe.db.set_value("Library Fine Payment", self.name, "payment_entry", pe.name)

    def _cancel_payment_entry(self):
        pe_name = frappe.db.get_value(
            "Library Fine Payment", self.name, "payment_entry"
        )
        if not pe_name:
            return
        try:
            pe = frappe.get_doc("Payment Entry", pe_name)
            if pe.docstatus == 1:
                pe.cancel()
        except frappe.DoesNotExistError:
            pass

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _get_company(self):
        try:
            s = frappe.get_single("Library Settings")
            if s.company:
                return s.company
        except Exception:
            pass
        return (
            frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
        )
