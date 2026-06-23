# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Fine No"),      "fieldname": "name",               "fieldtype": "Link",     "options": "Library Fine",   "width": 140},
        {"label": _("Member"),       "fieldname": "member",             "fieldtype": "Link",     "options": "Library Member", "width": 110},
        {"label": _("Member Name"),  "fieldname": "member_name",        "fieldtype": "Data",     "width": 150},
        {"label": _("Member Type"),  "fieldname": "member_type",        "fieldtype": "Data",     "width": 120},
        {"label": _("Book Title"),   "fieldname": "book_title",         "fieldtype": "Data",     "width": 180},
        {"label": _("Issue Date"),   "fieldname": "issue_date",         "fieldtype": "Date",     "width": 100},
        {"label": _("Due Date"),     "fieldname": "due_date",           "fieldtype": "Date",     "width": 100},
        {"label": _("Return Date"),  "fieldname": "return_date",        "fieldtype": "Date",     "width": 100},
        {"label": _("Overdue Days"), "fieldname": "overdue_days",       "fieldtype": "Int",      "width": 100},
        {"label": _("Fine Raised"),  "fieldname": "total_fine_amount",  "fieldtype": "Currency", "width": 120},
        {"label": _("Amount Paid"),  "fieldname": "amount_paid",        "fieldtype": "Currency", "width": 120},
        {"label": _("Outstanding"),  "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Status"),       "fieldname": "status",             "fieldtype": "Data",     "width": 110},
    ]


def get_data(filters):
    conditions = ["lf.docstatus = 1"]
    values = {}

    if filters.get("from_date"):
        conditions.append("DATE(lf.creation) >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("DATE(lf.creation) <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    status = filters.get("status")
    if status and status != "All":
        conditions.append("lf.status = %(status)s")
        values["status"] = status

    member_type_join = ""
    if filters.get("member_type"):
        member_type_join = "JOIN `tabLibrary Member` lm2 ON lm2.name = lf.member"
        conditions.append("lm2.member_type = %(member_type)s")
        values["member_type"] = filters["member_type"]

    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        """
        SELECT
            lf.name,
            lf.member,
            lf.member_name,
            lf.book_title,
            lf.issue_date,
            lf.due_date,
            lf.return_date,
            lf.overdue_days,
            lf.total_fine_amount,
            lf.amount_paid,
            lf.outstanding_amount,
            lf.status
        FROM `tabLibrary Fine` lf
        {join}
        WHERE {where}
        ORDER BY lf.creation DESC
        """.format(join=member_type_join, where=where),
        values,
        as_dict=True,
    )

    # Attach member_type per row
    for row in rows:
        row["member_type"] = frappe.db.get_value(
            "Library Member", row["member"], "member_type"
        ) or ""

    data = list(rows)

    if data:
        data.append({
            "name":               "TOTAL",
            "member":             "",
            "member_name":        "",
            "member_type":        "",
            "book_title":         "",
            "issue_date":         None,
            "due_date":           None,
            "return_date":        None,
            "overdue_days":       None,
            "total_fine_amount":  sum(flt(r["total_fine_amount"])  for r in rows),
            "amount_paid":        sum(flt(r["amount_paid"])         for r in rows),
            "outstanding_amount": sum(flt(r["outstanding_amount"])  for r in rows),
            "status":             "",
        })

    return data
