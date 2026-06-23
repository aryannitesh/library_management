# Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Patch v1.0: Create default Chart of Accounts entries for Library Management.

Creates (if not already present):
  1. Library Fine Income    — Income account under Direct/Indirect Income
  2. Library Member Receivable — Receivable account under Accounts Receivable
"""

import frappe


def execute():
    companies = frappe.get_all("Company", fields=["name", "default_currency"])

    for company in companies:
        _create_fine_income_account(company["name"])
        _create_member_receivable_account(company["name"])

    frappe.db.commit()


def _create_fine_income_account(company):
    account_name = "Library Fine Income"

    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        return

    # Resolve parent: prefer Direct Income, fall back to Indirect Income, then Income
    parent = _get_parent_account(
        ["Direct Income", "Indirect Income", "Income"],
        company,
    )
    if not parent:
        frappe.log_error(
            "create_library_accounts: Could not find income parent account "
            "for company {}. Skipping Library Fine Income creation.".format(company),
            "Library Accounts Patch",
        )
        return

    frappe.get_doc({
        "doctype":           "Account",
        "account_name":      account_name,
        "company":           company,
        "parent_account":    parent,
        "account_type":      "Income Account",
        "is_group":          0,
        "root_type":         "Income",
    }).insert(ignore_permissions=True)

    frappe.logger().info(
        "Created account 'Library Fine Income' for company {}.".format(company)
    )


def _create_member_receivable_account(company):
    account_name = "Library Member Receivable"

    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        return

    # Resolve parent: prefer Accounts Receivable, fall back to Debtors
    parent = _get_parent_account(
        ["Accounts Receivable", "Debtors"],
        company,
    )
    if not parent:
        frappe.log_error(
            "create_library_accounts: Could not find receivable parent account "
            "for company {}. Skipping Library Member Receivable creation.".format(company),
            "Library Accounts Patch",
        )
        return

    frappe.get_doc({
        "doctype":        "Account",
        "account_name":   account_name,
        "company":        company,
        "parent_account": parent,
        "account_type":   "Receivable",
        "is_group":       0,
        "root_type":      "Asset",
    }).insert(ignore_permissions=True)

    frappe.logger().info(
        "Created account 'Library Member Receivable' for company {}.".format(company)
    )


def _get_parent_account(candidates, company):
    """Return the first matching account name from candidates list."""
    for name in candidates:
        account = frappe.db.get_value(
            "Account",
            {"account_name": name, "company": company},
            "name",
        )
        if account:
            return account
    return None
