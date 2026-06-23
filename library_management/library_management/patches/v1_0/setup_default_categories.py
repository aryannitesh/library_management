# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Patch v1.0: Create default Book Categories.
"""

import frappe


DEFAULT_CATEGORIES = [
    {
        "category_name": "Fiction",
        "description":   "Novels, short stories, and other fictional works.",
    },
    {
        "category_name": "Science & Technology",
        "description":   "Books on science, engineering, and technology.",
    },
    {
        "category_name": "Reference",
        "description":   "Encyclopedias, dictionaries, atlases, and reference works.",
    },
    {
        "category_name": "History & Culture",
        "description":   "History, geography, culture, and civilisation.",
    },
    {
        "category_name": "Academic & Educational",
        "description":   "Textbooks and academic course material.",
    },
    {
        "category_name": "Arts & Literature",
        "description":   "Poetry, drama, fine arts, and literary criticism.",
    },
    {
        "category_name": "Business & Management",
        "description":   "Business, economics, finance, and management.",
    },
]


def execute():
    for cat in DEFAULT_CATEGORIES:
        if not frappe.db.exists("Book Category", cat["category_name"]):
            frappe.get_doc(
                dict(doctype="Book Category", **cat)
            ).insert(ignore_permissions=True)
            frappe.logger().info(
                "Created Book Category: {}".format(cat["category_name"])
            )

    frappe.db.commit()
