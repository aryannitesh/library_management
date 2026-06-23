# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, nowdate


class LibraryBookIssue(Document):

    # ------------------------------------------------------------------
    # Validate — runs on Save and Submit
    # ------------------------------------------------------------------
    def validate(self):
        self._check_membership_status()
        self._check_book_availability()
        self._check_duplicate_issue()
        self._check_max_books()
        self._set_due_date()

    # ------------------------------------------------------------------
    # on_submit — decrement copies, log history
    # ------------------------------------------------------------------
    def on_submit(self):
        self.status = "Issued"
        self._update_book_copies(delta=-1)
        self._add_member_issue_history()

    # ------------------------------------------------------------------
    # on_cancel — restore copies, remove history, cancel related fine
    # ------------------------------------------------------------------
    def on_cancel(self):
        self._update_book_copies(delta=1)
        self._remove_member_issue_history()
        self._cancel_related_fine()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _check_membership_status(self):
        status = frappe.db.get_value("Library Member", self.member, "membership_status")
        if status != "Active":
            frappe.throw(
                _(
                    "Cannot issue book. Member membership is <b>{0}</b>. "
                    "Please renew membership first."
                ).format(status)
            )

    def _check_book_availability(self):
        available = frappe.db.get_value("Book", self.book, "available_copies") or 0
        if available <= 0:
            title = frappe.db.get_value("Book", self.book, "title")
            frappe.throw(
                _(
                    "Cannot issue. No copies of <b>'{0}'</b> are currently available."
                ).format(title)
            )

    def _check_duplicate_issue(self):
        exists = frappe.db.exists(
            "Library Book Issue",
            {
                "member": self.member,
                "book": self.book,
                "status": ["in", ["Issued", "Overdue"]],
                "docstatus": 1,
                "name": ["!=", self.name],
            },
        )
        if exists:
            frappe.throw(
                _("This book is already issued to this member and not yet returned.")
            )

    def _check_max_books(self):
        max_books = frappe.db.get_value(
            "Library Member Type",
            frappe.db.get_value("Library Member", self.member, "member_type"),
            "max_books_allowed",
        ) or 3

        current_count = frappe.db.count(
            "Library Book Issue",
            {
                "member": self.member,
                "status": ["in", ["Issued", "Overdue"]],
                "docstatus": 1,
                "name": ["!=", self.name],
            },
        )
        if current_count >= max_books:
            frappe.throw(
                _(
                    "Member has reached the maximum book limit of <b>{0}</b> books."
                ).format(max_books)
            )

    def _set_due_date(self):
        if self.issue_date and self.loan_period_days:
            self.due_date = add_days(self.issue_date, int(self.loan_period_days))
        elif self.issue_date and not self.loan_period_days:
            # fallback: default 14 days
            self.due_date = add_days(self.issue_date, 14)

    # ------------------------------------------------------------------
    # Book copy helpers
    # ------------------------------------------------------------------
    def _update_book_copies(self, delta):
        book = frappe.get_doc("Book", self.book)
        new_available = max(0, (book.available_copies or 0) + delta)
        new_available = min(new_available, book.total_copies or 0)
        book.available_copies = new_available

        total = book.total_copies or 0
        if new_available == 0:
            book.availability_status = "Not Available"
        elif new_available >= total:
            book.availability_status = "Available"
        else:
            book.availability_status = "Partially Available"

        book.save(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Member Issue History helpers
    # ------------------------------------------------------------------
    def _add_member_issue_history(self):
        member = frappe.get_doc("Library Member", self.member)
        member.append(
            "issue_history",
            {
                "book": self.book,
                "book_title": self.book_title,
                "isbn": self.isbn,
                "issue_date": self.issue_date,
                "due_date": self.due_date,
                "return_date": None,
                "status": "Issued",
            },
        )
        member.save(ignore_permissions=True)

    def _remove_member_issue_history(self):
        member = frappe.get_doc("Library Member", self.member)
        member.issue_history = [
            row for row in member.issue_history if row.get("book") != self.book
            or str(row.get("issue_date")) != str(self.issue_date)
        ]
        member.save(ignore_permissions=True)

    def _update_member_issue_history(self, status, return_date=None):
        member = frappe.get_doc("Library Member", self.member)
        for row in member.issue_history:
            if row.book == self.book and str(row.issue_date) == str(self.issue_date):
                row.status = status
                if return_date:
                    row.return_date = return_date
                break
        member.save(ignore_permissions=True)

    # ------------------------------------------------------------------
    # Cancel related fine
    # ------------------------------------------------------------------
    def _cancel_related_fine(self):
        if not frappe.db.exists("DocType", "Library Fine"):
            return
        fine_name = frappe.db.get_value(
            "Library Fine", {"book_issue": self.name, "docstatus": 1}
        )
        if fine_name:
            fine_doc = frappe.get_doc("Library Fine", fine_name)
            fine_doc.cancel()


# ------------------------------------------------------------------
# Whitelisted API — Process Return
# ------------------------------------------------------------------
@frappe.whitelist()
def process_return(docname, return_date):
    """
    Called by the Process Return button on the form.
    Handles return, availability update, history update, and fine creation.
    """
    doc = frappe.get_doc("Library Book Issue", docname)

    if doc.docstatus != 1:
        frappe.throw(_("Only submitted issues can be processed for return."))
    if doc.status == "Returned":
        frappe.throw(_("This book has already been returned."))

    return_date = getdate(return_date)
    due_date    = getdate(doc.due_date)

    # Update the issue doc fields (use db_set to avoid re-running validate)
    frappe.db.set_value(
        "Library Book Issue",
        docname,
        {
            "return_date": return_date,
            "status": "Returned",
        },
    )

    # Restore book availability
    book = frappe.get_doc("Book", doc.book)
    new_available = min(
        (book.available_copies or 0) + 1, book.total_copies or 0
    )
    book.available_copies = new_available
    if new_available == 0:
        book.availability_status = "Not Available"
    elif new_available >= (book.total_copies or 0):
        book.availability_status = "Available"
    else:
        book.availability_status = "Partially Available"
    book.save(ignore_permissions=True)

    # Update member issue history
    member = frappe.get_doc("Library Member", doc.member)
    for row in member.issue_history:
        if row.book == doc.book and str(row.issue_date) == str(doc.issue_date):
            row.status      = "Returned"
            row.return_date = return_date
            break
    member.save(ignore_permissions=True)

    # Fine calculation
    fine_amount = 0.0
    days_overdue = date_diff(return_date, due_date)

    if days_overdue > 0:
        member_type_name = frappe.db.get_value(
            "Library Member", doc.member, "member_type"
        )
        fine_per_day = (
            frappe.db.get_value(
                "Library Member Type", member_type_name, "fine_per_day"
            )
            or 0
        )
        fine_amount = days_overdue * fine_per_day

        if fine_amount > 0:
            # Create Library Fine only if the DocType exists
            if frappe.db.exists("DocType", "Library Fine"):
                fine_doc = frappe.get_doc(
                    {
                        "doctype":            "Library Fine",
                        "member":             doc.member,
                        "book_issue":         docname,
                        "book":               doc.book,
                        "issue_date":         doc.issue_date,
                        "due_date":           doc.due_date,
                        "return_date":        return_date,
                        "overdue_days":       days_overdue,
                        "fine_per_day":       fine_per_day,
                        "total_fine_amount":  fine_amount,
                        "outstanding_amount": fine_amount,
                        "status":             "Unpaid",
                    }
                )
                fine_doc.insert(ignore_permissions=True)
                fine_doc.submit()

            # Write fine totals back onto the issue record
            frappe.db.set_value(
                "Library Book Issue",
                docname,
                {
                    "fine_amount":      fine_amount,
                    "fine_outstanding": fine_amount,
                    "fine_paid":        0,
                },
            )

    frappe.db.commit()

    return {
        "status":       "success",
        "days_overdue": days_overdue,
        "fine_amount":  fine_amount,
        "return_date":  str(return_date),
    }
