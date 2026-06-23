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
        {"label": _("Member No"),           "fieldname": "name",            "fieldtype": "Link",     "options": "Library Member", "width": 130},
        {"label": _("Member Name"),         "fieldname": "full_name",       "fieldtype": "Data",     "width": 160},
        {"label": _("Member Type"),         "fieldname": "member_type",     "fieldtype": "Data",     "width": 120},
        {"label": _("Phone"),               "fieldname": "phone",           "fieldtype": "Data",     "width": 120},
        {"label": _("Email"),               "fieldname": "email",           "fieldtype": "Data",     "width": 160},
        {"label": _("Pending Fines"),       "fieldname": "pending_count",   "fieldtype": "Int",      "width": 110},
        {"label": _("Total Fines Raised"),  "fieldname": "total_fines",     "fieldtype": "Currency", "width": 140},
        {"label": _("Amount Paid"),         "fieldname": "amount_paid",     "fieldtype": "Currency", "width": 120},
        {"label": _("Outstanding Balance"), "fieldname": "outstanding",     "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    conditions = ["lm.docstatus < 2"]
    values = {}

    if filters.get("member_type"):
        conditions.append("lm.member_type = %(member_type)s")
        values["member_type"] = filters["member_type"]

    where = " AND ".join(conditions)

    members = frappe.db.sql(
        """
        SELECT lm.name, lm.full_name, lm.member_type, lm.phone, lm.email
        FROM `tabLibrary Member` lm
        WHERE {where}
        ORDER BY lm.full_name
        """.format(where=where),
        values,
        as_dict=True,
    )

    data      = []
    g_total   = g_paid = g_outstanding = 0.0

    for m in members:
        agg = frappe.db.sql(
            """
            SELECT
                COUNT(name)                       AS pending_count,
                COALESCE(SUM(total_fine_amount),0) AS total_fines,
                COALESCE(SUM(amount_paid),       0) AS amount_paid,
                COALESCE(SUM(outstanding_amount),0) AS outstanding
            FROM `tabLibrary Fine`
            WHERE member    = %s
              AND status   != 'Paid'
              AND docstatus  = 1
            """,
            (m["name"],),
            as_dict=True,
        )
        row_agg = agg[0] if agg else {}
        outstanding = flt(row_agg.get("outstanding"))

        if outstanding <= 0:
            continue

        total_fines = flt(row_agg.get("total_fines"))
        amount_paid = flt(row_agg.get("amount_paid"))

        g_total       += total_fines
        g_paid        += amount_paid
        g_outstanding += outstanding

        data.append({
            "name":          m["name"],
            "full_name":     m["full_name"],
            "member_type":   m.get("member_type") or "",
            "phone":         m.get("phone") or "",
            "email":         m.get("email") or "",
            "pending_count": int(row_agg.get("pending_count") or 0),
            "total_fines":   total_fines,
            "amount_paid":   amount_paid,
            "outstanding":   outstanding,
        })

    # Sort most overdue first
    data.sort(key=lambda x: x["outstanding"], reverse=True)

    # Grand total row
    if data:
        data.append({
            "name":          "GRAND TOTAL",
            "full_name":     "",
            "member_type":   "",
            "phone":         "",
            "email":         "",
            "pending_count": None,
            "total_fines":   g_total,
            "amount_paid":   g_paid,
            "outstanding":   g_outstanding,
        })

    return data
