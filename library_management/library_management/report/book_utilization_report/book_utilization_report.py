# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data    = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Book Title"),       "fieldname": "title",            "fieldtype": "Data",    "width": 200},
        {"label": _("Author"),           "fieldname": "author",           "fieldtype": "Data",    "width": 150},
        {"label": _("ISBN"),             "fieldname": "isbn",             "fieldtype": "Data",    "width": 130},
        {"label": _("Category"),         "fieldname": "category",         "fieldtype": "Data",    "width": 120},
        {"label": _("Rack Location"),    "fieldname": "rack_location",    "fieldtype": "Data",    "width": 120},
        {"label": _("Total Copies"),     "fieldname": "total_copies",     "fieldtype": "Int",     "width": 110},
        {"label": _("Available Copies"), "fieldname": "available_copies", "fieldtype": "Int",     "width": 130},
        {"label": _("Times Issued"),     "fieldname": "times_issued",     "fieldtype": "Int",     "width": 110},
        {"label": _("Last Issued"),      "fieldname": "last_issued_date", "fieldtype": "Date",    "width": 110},
        {"label": _("Utilization %"),    "fieldname": "utilization_pct",  "fieldtype": "Float",   "width": 110},
    ]


def get_data(filters):
    book_conditions = ["b.docstatus < 2"]
    book_values = {}

    if filters.get("category"):
        book_conditions.append("b.category = %(category)s")
        book_values["category"] = filters["category"]

    book_where = " AND ".join(book_conditions)

    books = frappe.db.sql(
        """
        SELECT
            b.name,
            b.title,
            b.author,
            b.isbn,
            b.category,
            b.rack_location,
            b.total_copies,
            b.available_copies
        FROM `tabBook` b
        WHERE {where}
        ORDER BY b.title
        """.format(where=book_where),
        book_values,
        as_dict=True,
    )

    # Build issue count + last-issued map in one query
    issue_conditions = ["lbi.docstatus = 1"]
    issue_values = {}

    if filters.get("from_date"):
        issue_conditions.append("lbi.issue_date >= %(from_date)s")
        issue_values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        issue_conditions.append("lbi.issue_date <= %(to_date)s")
        issue_values["to_date"] = filters["to_date"]

    issue_where = " AND ".join(issue_conditions)

    issue_stats = frappe.db.sql(
        """
        SELECT
            lbi.book,
            COUNT(lbi.name)       AS times_issued,
            MAX(lbi.issue_date)   AS last_issued_date
        FROM `tabLibrary Book Issue` lbi
        WHERE {where}
        GROUP BY lbi.book
        """.format(where=issue_where),
        issue_values,
        as_dict=True,
    )

    stats_map = {r["book"]: r for r in issue_stats}

    data = []
    for book in books:
        stats       = stats_map.get(book["name"], {})
        times       = int(stats.get("times_issued") or 0)
        total       = int(book["total_copies"] or 1)
        util_pct    = min(100.0, round((times / total) * 100, 1)) if total else 0.0

        rack_name = ""
        if book.get("rack_location"):
            rack_name = (
                frappe.db.get_value("Book Rack", book["rack_location"], "rack_name")
                or book["rack_location"]
            )

        row = {
            "title":            book["title"],
            "author":           book["author"],
            "isbn":             book.get("isbn") or "",
            "category":         book.get("category") or "",
            "rack_location":    rack_name,
            "total_copies":     total,
            "available_copies": int(book.get("available_copies") or 0),
            "times_issued":     times,
            "last_issued_date": stats.get("last_issued_date"),
            "utilization_pct":  util_pct,
        }

        # Mark zero-issue rows for UI highlighting
        if times == 0:
            row["bold"] = 0
            row["color"] = "red"

        data.append(row)

    data.sort(key=lambda x: x["times_issued"], reverse=True)
    return data
