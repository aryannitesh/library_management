# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class LibraryFine(Document):

    def validate(self):
        self._calculate_outstanding()
        self._set_status()

    def on_submit(self):
        self._update_member_outstanding_fines()
        self._create_journal_entry()

    def on_cancel(self):
        self._cancel_journal_entry()
        self._update_member_outstanding_fines()

    # ------------------------------------------------------------------
    # validate helpers
    # ------------------------------------------------------------------

    def _calculate_outstanding(self):
        total  = flt(self.total_fine_amount)
        paid   = flt(self.amount_paid)
        waiver = flt(self.waiver_amount)

        outstanding = total - paid - waiver
        if outstanding < 0:
            frappe.throw(
                _("Outstanding Amount cannot be negative. "
                  "Check the waiver or paid amounts.")
            )
        self.outstanding_amount = outstanding

    def _set_status(self):
        total  = flt(self.total_fine_amount)
        paid   = flt(self.amount_paid)
        waiver = flt(self.waiver_amount)

        if waiver >= total:
            self.status = "Waived"
        elif paid >= total:
            self.status = "Paid"
        elif paid > 0:
            self.status = "Partially Paid"
        else:
            self.status = "Unpaid"

    # ------------------------------------------------------------------
    # member outstanding balance
    # ------------------------------------------------------------------

    def _update_member_outstanding_fines(self):
        if not self.member:
            return
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
        frappe.db.set_value(
            "Library Member", self.member,
            "outstanding_fines", result[0][0] if result else 0
        )

    # ------------------------------------------------------------------
    # Journal Entry — uses Library Settings accounts
    # ------------------------------------------------------------------

    def _create_journal_entry(self):
        # ---- resolve accounts from Library Settings ----
        settings          = self._get_settings()
        debtors_account   = settings.get("member_receivable_account") if settings else None
        income_account    = settings.get("fine_income_account") if settings else None
        company           = settings.get("company") if settings else None

        # Fallback: resolve from Chart of Accounts if settings incomplete
        if not company:
            company = (
                frappe.defaults.get_user_default("Company")
                or frappe.db.get_single_value("Global Defaults", "default_company")
            )
        if not debtors_account:
            debtors_account = self._resolve_account(
                ["Library Member Receivable", "Debtors", "Accounts Receivable"], company
            )
        if not income_account:
            income_account = self._resolve_account(
                ["Library Fine Income", "Indirect Income", "Other Income"], company
            )

        if not company or not debtors_account or not income_account:
            frappe.log_error(
                "Library Fine JE: Could not resolve company or GL accounts. "
                "company={}, debtors={}, income={}. Skipping.".format(
                    company, debtors_account, income_account
                ),
                "Library Fine Accounting",
            )
            return

        remark = (
            "Library Fine for {member_name} - Book: {book_title} - "
            "Overdue Days: {overdue_days} - Ref: {name}"
        ).format(
            member_name  = self.member_name,
            book_title   = self.book_title,
            overdue_days = self.overdue_days,
            name         = self.name,
        )

        je = frappe.get_doc({
            "doctype":      "Journal Entry",
            "voucher_type": "Journal Entry",
            "company":      company,
            "posting_date": nowdate(),
            "user_remark":  remark,
            "accounts": [
                {
                    # DEBIT: Member Receivable
                    "account":                    debtors_account,
                    "party_type":                 "Customer",
                    "party":                      self.member,
                    "debit_in_account_currency":  flt(self.total_fine_amount),
                    "credit_in_account_currency": 0,
                },
                {
                    # CREDIT: Fine Income
                    "account":                    income_account,
                    "debit_in_account_currency":  0,
                    "credit_in_account_currency": flt(self.total_fine_amount),
                },
            ],
        })
        je.insert(ignore_permissions=True)
        je.submit()

        frappe.db.set_value("Library Fine", self.name, "journal_entry", je.name)
        self.journal_entry = je.name

    def _cancel_journal_entry(self):
        if not self.journal_entry:
            return
        try:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
        except frappe.DoesNotExistError:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_settings(self):
        """Return Library Settings as a dict; None if not configured."""
        try:
            s = frappe.get_single("Library Settings")
            return {
                "company":                   s.company,
                "fine_income_account":        s.fine_income_account,
                "member_receivable_account":  s.member_receivable_account,
            }
        except Exception:
            return None

    def _resolve_account(self, candidates, company):
        for name in candidates:
            account = frappe.db.get_value(
                "Account",
                {"account_name": name, "company": company, "is_group": 0},
                "name",
            )
            if account:
                return account
        return None
