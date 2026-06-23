# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, date_diff


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Issue No"),      "fieldname": "name",          "fieldtype": "Link",     "options": "Library Book Issue", "width": 140},
        {"label": _("Member"),        "fieldname": "member",        "fieldtype": "Link",     "options": "Library Member",     "width": 110},
        {"label": _("Member Name"),   "fieldname": "member_name",   "fieldtype": "Data",     "width": 150},
        {"label": _("Member Type"),   "fieldname": "member_type",   "fieldtype": "Data",     "width": 120},
        {"label": _("Book Title"),    "fieldname": "book_title",    "fieldtype": "Data",     "width": 200},
        {"label": _("ISBN"),          "fieldname": "isbn",          "fieldtype": "Data",     "width": 130},
        {"label": _("Rack Location"), "fieldname": "rack_location", "fieldtype": "Data",     "width": 120},
        {"label": _("Issue Date"),    "fieldname": "issue_date",    "fieldtype": "Date",     "width": 100},
        {"label": _("Due Date"),      "fieldname": "due_date",      "fieldtype": "Date",     "width": 100},
        {"label": _("Days Overdue"),  "fieldname": "days_overdue",  "fieldtype": "Int",      "width": 110},
        {"label": _("Fine Accrued"),  "fieldname": "fine_accrued",  "fieldtype": "Currency", "width": 120},
        {"label": _("Phone"),         "fieldname": "member_phone",  "fieldtype": "Data",     "width": 120},
        {"label": _("Email"),         "fieldname": "member_email",  "fieldtype": "Data",     "width": 160},
    ]


def get_data(filters):
    as_on = getdate(filters.get("as_on_date") or nowdate())

    conditions = [
        "lbi.docstatus = 1",
        "(lbi.status = 'Overdue' OR (lbi.status = 'Issued' AND lbi.due_date < %(as_on)s))",
    ]
    values = {"as_on": as_on}

    if filters.get("member_type"):
        conditions.append("lm.member_type = %(member_type)s")
        values["member_type"] = filters["member_type"]

    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        """
        SELECT
            lbi.name,
            lbi.member,
            lbi.member_name,
            lbi.member_type,
            lbi.book_title,
            lbi.isbn,
            lbi.issue_date,
            lbi.due_date,
            lm.phone  AS member_phone,
            lm.email  AS member_email,
            b.rack_location
        FROM `tabLibrary Book Issue` lbi
        JOIN `tabLibrary Member`     lm ON lm.name = lbi.member
        LEFT JOIN `tabBook`          b  ON b.name  = lbi.book
        WHERE {where}
        """.format(where=where),
        values,
        as_dict=True,
    )

    fine_rate_cache = {}
    data = []

    for row in rows:
        days_overdue = max(0, date_diff(as_on, getdate(row["due_date"])))

        mt = row.get("member_type") or ""
        if mt not in fine_rate_cache:
            fine_rate_cache[mt] = flt(
                frappe.db.get_value("Library Member Type", mt, "fine_per_day") or 0
            )

        rack_name = ""
        if row.get("rack_location"):
            rack_name = (
                frappe.db.get_value("Book Rack", row["rack_location"], "rack_name")
                or row["rack_location"]
            )

        data.append({
            "name":          row["name"],
            "member":        row["member"],
            "member_name":   row["member_name"],
            "member_type":   mt,
            "book_title":    row["book_title"],
            "isbn":          row.get("isbn") or "",
            "rack_location": rack_name,
            "issue_date":    row["issue_date"],
            "due_date":      row["due_date"],
            "days_overdue":  days_overdue,
            "fine_accrued":  days_overdue * fine_rate_cache[mt],
            "member_phone":  row.get("member_phone") or "",
            "member_email":  row.get("member_email") or "",
        })

    data.sort(key=lambda x: x["days_overdue"], reverse=True)
    return data
