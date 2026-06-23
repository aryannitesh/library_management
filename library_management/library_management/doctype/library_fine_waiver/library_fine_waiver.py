# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class LibraryFineWaiver(Document):

    def validate(self):
        outstanding = flt(
            frappe.db.get_value("Library Fine", self.library_fine, "outstanding_amount")
        )
        if flt(self.waiver_amount) <= 0:
            frappe.throw(_("Waiver Amount must be greater than zero."))
        if flt(self.waiver_amount) > outstanding:
            frappe.throw(
                _(
                    "Waiver Amount ({0}) cannot exceed the outstanding amount ({1})."
                ).format(self.waiver_amount, outstanding)
            )

    def on_submit(self):
        self._apply_waiver_to_fine()
        self._update_member_outstanding_fines()
        self._create_adjustment_journal_entry()

    def on_cancel(self):
        self._reverse_waiver_from_fine()
        self._update_member_outstanding_fines()
        self._cancel_adjustment_journal_entry()

    # ------------------------------------------------------------------

    def _apply_waiver_to_fine(self):
        fine = frappe.get_doc("Library Fine", self.library_fine)
        fine.waiver_amount  = flt(fine.waiver_amount) + flt(self.waiver_amount)
        fine.waiver_reason  = self.waiver_reason
        fine.waived_by      = self.approved_by
        fine.waiver_date    = self.waiver_date
        fine.save(ignore_permissions=True)

    def _reverse_waiver_from_fine(self):
        fine = frappe.get_doc("Library Fine", self.library_fine)
        fine.waiver_amount = max(0, flt(fine.waiver_amount) - flt(self.waiver_amount))
        fine.save(ignore_permissions=True)

    def _update_member_outstanding_fines(self):
        member = frappe.db.get_value("Library Fine", self.library_fine, "member")
        if not member:
            return
        result = frappe.db.sql(
            """
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM   `tabLibrary Fine`
            WHERE  member    = %s
              AND  status   != 'Paid'
              AND  docstatus  = 1
            """,
            (member,),
        )
        outstanding = result[0][0] if result else 0
        frappe.db.set_value("Library Member", member, "outstanding_fines", outstanding)

    # ------------------------------------------------------------------
    # Adjustment Journal Entry — reverses the receivable by waiver amount
    # ------------------------------------------------------------------

    def _create_adjustment_journal_entry(self):
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )
        if not company:
            return

        debtors_account = self._get_account(
            ["Debtors", "Accounts Receivable", "Member Receivable"], company
        )
        income_account  = self._get_account(
            ["Library Fine Income", "Indirect Income", "Other Income"], company
        )

        if not debtors_account or not income_account:
            return

        fine_doc = frappe.get_doc("Library Fine", self.library_fine)
        remark = _(
            "Fine Waiver for {0} — Fine: {1} — Waiver Amount: {2} — Reason: {3}"
        ).format(
            fine_doc.member_name, self.library_fine,
            self.waiver_amount, self.waiver_reason
        )

        # Reverse the receivable: credit Debtors, debit Income (adjustment)
        je = frappe.get_doc({
            "doctype":      "Journal Entry",
            "voucher_type": "Journal Entry",
            "company":      company,
            "posting_date": nowdate(),
            "user_remark":  remark,
            "accounts": [
                {
                    "account":      income_account,
                    "debit_in_account_currency":  flt(self.waiver_amount),
                    "credit_in_account_currency": 0,
                },
                {
                    "account":      debtors_account,
                    "party_type":   "Customer",
                    "party":        fine_doc.member,
                    "debit_in_account_currency":  0,
                    "credit_in_account_currency": flt(self.waiver_amount),
                },
            ],
        })
        je.insert(ignore_permissions=True)
        je.submit()

        frappe.db.set_value(
            "Library Fine Waiver", self.name, "adjustment_journal_entry", je.name
        )
        self.adjustment_journal_entry = je.name

    def _cancel_adjustment_journal_entry(self):
        if self.adjustment_journal_entry:
            try:
                je = frappe.get_doc("Journal Entry", self.adjustment_journal_entry)
                if je.docstatus == 1:
                    je.cancel()
            except frappe.DoesNotExistError:
                pass

    def _get_account(self, candidates, company):
        for name in candidates:
            account = frappe.db.get_value(
                "Account",
                {"account_name": name, "company": company, "is_group": 0},
                "name",
            )
            if account:
                return account
        return None
