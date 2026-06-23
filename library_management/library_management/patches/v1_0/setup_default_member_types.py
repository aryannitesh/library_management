# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Patch v1.0: Create default Library Member Types —
Student, Staff, and Public — with configurable loan periods and fine rates.
"""

import frappe


DEFAULT_MEMBER_TYPES = [
    {
        "member_type_name":  "Student",
        "loan_period_days":  14,
        "max_books_allowed": 3,
        "fine_per_day":      2.00,
        "description":       "Student members — 14-day loan period, up to 3 books, Rs. 2/day fine.",
    },
    {
        "member_type_name":  "Staff",
        "loan_period_days":  21,
        "max_books_allowed": 5,
        "fine_per_day":      1.00,
        "description":       "Staff members — 21-day loan period, up to 5 books, Rs. 1/day fine.",
    },
    {
        "member_type_name":  "Public",
        "loan_period_days":  7,
        "max_books_allowed": 2,
        "fine_per_day":      5.00,
        "description":       "Public members — 7-day loan period, up to 2 books, Rs. 5/day fine.",
    },
]


def execute():
    for mt in DEFAULT_MEMBER_TYPES:
        if not frappe.db.exists("Library Member Type", mt["member_type_name"]):
            frappe.get_doc(
                dict(doctype="Library Member Type", **mt)
            ).insert(ignore_permissions=True)
            frappe.logger().info(
                "Created Library Member Type: {}".format(mt["member_type_name"])
            )

    frappe.db.commit()
