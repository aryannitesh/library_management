# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, date_diff, getdate, flt, formatdate, fmt_money


def auto_mark_overdue():
    """
    Daily task.
    Marks all submitted Library Book Issues with status='Issued'
    and due_date < today as 'Overdue'.
    Mirrors the status change in each member's Issue History child table.
    """
    today = nowdate()

    overdue_issues = frappe.db.get_all(
        "Library Book Issue",
        filters={
            "docstatus": 1,
            "status":    "Issued",
            "due_date":  ["<", today],
        },
        fields=["name", "member", "book", "issue_date"],
    )

    if not overdue_issues:
        return

    for issue in overdue_issues:
        frappe.db.set_value("Library Book Issue", issue["name"], "status", "Overdue")

        member  = frappe.get_doc("Library Member", issue["member"])
        changed = False
        for row in member.issue_history:
            if (
                row.book == issue["book"]
                and str(row.issue_date) == str(issue["issue_date"])
                and row.status == "Issued"
            ):
                row.status = "Overdue"
                changed    = True
                break

        if changed:
            member.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.logger().info(
        "auto_mark_overdue: marked {} issue(s) as Overdue.".format(len(overdue_issues))
    )


def send_overdue_reminders():
    """
    Daily task.
    Sends email reminders to members with overdue books.
    Includes the number of overdue days and fine accrued so far.
    """
    today = getdate(nowdate())

    overdue_issues = frappe.db.get_all(
        "Library Book Issue",
        filters={
            "docstatus": 1,
            "status":    "Overdue",
        },
        fields=[
            "name", "member", "member_name",
            "book", "book_title", "due_date", "member_type",
        ],
    )

    if not overdue_issues:
        return

    sent_count = 0

    for issue in overdue_issues:
        member_email = frappe.db.get_value("Library Member", issue["member"], "email")
        if not member_email:
            continue

        due_date     = getdate(issue["due_date"])
        days_overdue = date_diff(today, due_date)
        if days_overdue <= 0:
            continue

        fine_per_day = 0.0
        if issue.get("member_type"):
            fine_per_day = flt(
                frappe.db.get_value(
                    "Library Member Type", issue["member_type"], "fine_per_day"
                )
            )

        accrued_fine = days_overdue * fine_per_day

        subject = "Overdue Book Reminder - Please Return: {}".format(issue["book_title"])

        message = """Dear {member_name},<br><br>
Your borrowed book <b>'{book_title}'</b> was due on <b>{due_date}</b>
and is now <b>{days_overdue} day(s) overdue</b>.<br><br>
Fine accrued : <b>{accrued_fine}</b><br>
Fine rate    : <b>{fine_per_day} per day</b><br><br>
Please return the book at the earliest to avoid further charges.<br><br>
&mdash; Library Management System<br>
Klaimify Pvt. Ltd.
""".format(
            member_name  = issue["member_name"],
            book_title   = issue["book_title"],
            due_date     = formatdate(issue["due_date"]),
            days_overdue = days_overdue,
            accrued_fine = fmt_money(accrued_fine),
            fine_per_day = fmt_money(fine_per_day),
        )

        try:
            frappe.sendmail(
                recipients = [member_email],
                subject    = subject,
                message    = message,
                now        = True,
            )
            sent_count += 1
        except Exception as exc:
            frappe.log_error(
                "Overdue reminder failed for {} ({}): {}".format(
                    issue["member"], member_email, exc
                ),
                "Library Overdue Reminder",
            )



def update_membership_status():
    today = nowdate()

    expired = frappe.db.get_all(
        "Library Member",
        filters={"status": "Active", "membership_expiry": ["<", today]},
        fields=["name"],
    )
    for m in expired:
        frappe.db.set_value("Library Member", m["name"], "status", "Inactive")

    reactivated = frappe.db.get_all(
        "Library Member",
        filters={"status": "Inactive", "membership_expiry": [">=", today]},
        fields=["name"],
    )
    for m in reactivated:
        frappe.db.set_value("Library Member", m["name"], "status", "Active")

    frappe.db.commit()
    frappe.logger().info(
        "update_membership_status: expired={}, reactivated={}.".format(
            len(expired), len(reactivated)
        )
    )