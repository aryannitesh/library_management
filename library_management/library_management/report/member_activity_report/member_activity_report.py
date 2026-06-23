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
        {"label": _("Member No"),          "fieldname": "name",              "fieldtype": "Link",     "options": "Library Member", "width": 130},
        {"label": _("Member Name"),        "fieldname": "full_name",          "fieldtype": "Data",     "width": 160},
        {"label": _("Member Type"),        "fieldname": "member_type",        "fieldtype": "Data",     "width": 120},
        {"label": _("Membership Status"),  "fieldname": "membership_status",  "fieldtype": "Data",     "width": 130},
        {"label": _("Books Issued"),       "fieldname": "books_issued",       "fieldtype": "Int",      "width": 110},
        {"label": _("Books Returned"),     "fieldname": "books_returned",     "fieldtype": "Int",      "width": 120},
        {"label": _("Currently Issued"),   "fieldname": "currently_issued",   "fieldtype": "Int",      "width": 120},
        {"label": _("Overdue Count"),      "fieldname": "overdue_count",      "fieldtype": "Int",      "width": 110},
        {"label": _("Total Fines Raised"), "fieldname": "total_fines",        "fieldtype": "Currency", "width": 140},
        {"label": _("Fines Paid"),         "fieldname": "fines_paid",         "fieldtype": "Currency", "width": 110},
        {"label": _("Outstanding Balance"),"fieldname": "outstanding",        "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    conditions = ["lm.docstatus < 2"]
    values = {}

    if filters.get("member"):
        conditions.append("lm.name = %(member)s")
        values["member"] = filters["member"]

    if filters.get("member_type"):
        conditions.append("lm.member_type = %(member_type)s")
        values["member_type"] = filters["member_type"]

    where = " AND ".join(conditions)

    members = frappe.db.sql(
        """
        SELECT lm.name, lm.full_name, lm.member_type, lm.membership_status
        FROM `tabLibrary Member` lm
        WHERE {where}
        ORDER BY lm.full_name
        """.format(where=where),
        values,
        as_dict=True,
    )

    from_date = filters.get("from_date")
    to_date   = filters.get("to_date")

    data = []
    for m in members:
        mid = m["name"]

        # Issues in period
        issue_filters = {
            "member":   mid,
            "docstatus": 1,
            "issue_date": ["between", [from_date, to_date]],
        }
        books_issued = frappe.db.count("Library Book Issue", issue_filters)

        # Returns in period
        return_filters = {
            "member":      mid,
            "docstatus":   1,
            "status":      "Returned",
            "return_date": ["between", [from_date, to_date]],
        }
        books_returned = frappe.db.count("Library Book Issue", return_filters)

        # Current live counts (not period-filtered)
        currently_issued = frappe.db.count(
            "Library Book Issue", {"member": mid, "docstatus": 1, "status": "Issued"}
        )
        overdue_count = frappe.db.count(
            "Library Book Issue", {"member": mid, "docstatus": 1, "status": "Overdue"}
        )

        # Fine aggregates
        fine_agg = frappe.db.sql(
            """
            SELECT
                COALESCE(SUM(total_fine_amount), 0) AS total_fines,
                COALESCE(SUM(amount_paid),        0) AS fines_paid,
                COALESCE(SUM(outstanding_amount), 0) AS outstanding
            FROM `tabLibrary Fine`
            WHERE member = %s AND docstatus = 1
            """,
            (mid,),
            as_dict=True,
        )
        agg = fine_agg[0] if fine_agg else {}

        # Only include members with some activity
        if not any([books_issued, books_returned, currently_issued,
                    overdue_count, flt(agg.get("total_fines"))]):
            continue

        data.append({
            "name":             mid,
            "full_name":        m["full_name"],
            "member_type":      m["member_type"],
            "membership_status": m["membership_status"],
            "books_issued":     books_issued,
            "books_returned":   books_returned,
            "currently_issued": currently_issued,
            "overdue_count":    overdue_count,
            "total_fines":      flt(agg.get("total_fines")),
            "fines_paid":       flt(agg.get("fines_paid")),
            "outstanding":      flt(agg.get("outstanding")),
        })

    return data
