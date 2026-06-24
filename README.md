# Library Management System

**A production-ready ERPNext custom app by Klaimify Pvt. Ltd.**

> Full-featured library management with integrated accounting, built on Frappe/ERPNext v15.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [DocTypes](#doctypes)
4. [Installation](#installation)
5. [How to Use](#how-to-use)
6. [Roles and Permissions](#roles-and-permissions)
7. [Scheduled Tasks](#scheduled-tasks)
8. [Project Structure](#project-structure)
9. [License](#license)

---

## Overview

The Library Management System provides a complete solution for managing a library's catalog,
members, book issues, returns, fines, and accounting -- all from within ERPNext.
Every monetary transaction is automatically posted to the books of accounts. No double entry required.

---

## Features

- Central searchable book catalog with real-time copy availability
- Configurable member types (Student, Staff, Public) with per-type loan periods and fine rates
- Book issue and return with automatic due date, availability check, and duplicate issue prevention
- Overdue detection with automatic fine creation on late returns
- Fine payment and waiver with automatic Journal Entry and Payment Entry creation
- 5 built-in reports and a live dashboard
- 4 role-based access levels
- 3 automatic email notifications
- Daily scheduled tasks for overdue marking, reminders, and membership expiry

---

## Features Detail

### Book Catalog Management
- Central searchable catalog of all books (title, author, ISBN, category, rack location)
- Book Category and Book Rack master data
- Real-time available copy tracking -- updated automatically on issue and return
- Availability status: Available / Partially Available / Not Available

### Member Management
- Register members with full profile (name, contact, ID proof, photo)
- Configurable member types: Student, Staff, Public -- each with its own loan period, max books, and fine rate
- Membership validity dates with auto-expiry detection
- Outstanding fine balance displayed on every member profile
- Complete issue history per member

### Book Issue and Return
- Issue date recorded automatically
- Due date calculated from member type loan period (default 14 days)
- Prevents issuance if membership is expired, no copies available, duplicate issue, or max books reached
- One-click Process Return button on submitted issue
- Availability counts updated immediately on return
- Overdue fine auto-created on late return

### Fine Management
- Fine calculated automatically: overdue_days x fine_per_day
- Fine lifecycle: Unpaid -> Partially Paid -> Paid / Waived
- Fine Payment for recording payments against one or multiple fines
- Fine Waiver for authorized staff to waive or adjust fines
- Member outstanding balance updated in real time

### Accounting Integration
- Journal Entry auto-created when fine is raised (Debit: Receivable, Credit: Fine Income)
- Payment Entry auto-created when payment is recorded
- Adjustment Journal Entry on waiver
- All accounts configurable via Library Settings

### Reports

| Report                    | Description                                           |
|---------------------------|-------------------------------------------------------|
| Fine Collection Report    | Fines raised vs collected over any date range         |
| Overdue Books Report      | All overdue books with days overdue and accrued fine  |
| Member Activity Report    | Issue/return activity per member over a period        |
| Book Utilization Report   | Most and least accessed books with utilization %      |
| Outstanding Fines Summary | Current outstanding balances across all members       |

### Dashboard
- 6 Number Cards: Total Books, Books Issued Today, Overdue Books, Active Members, Outstanding Fines, Fine Collected This Month
- 3 Charts: Books Issued Per Month (Bar), Member Type Distribution (Donut), Fine Collection Trend (Line)

### Email Notifications
- Fine Raised Alert -- email to member when a fine is created
- Membership Expiry Warning -- email 7 days before membership expires
- Book Due Tomorrow Reminder -- email 1 day before due date

---

## DocTypes

| DocType               | Type        | Description                               |
|-----------------------|-------------|-------------------------------------------|
| Book Category         | Master      | Groups books into categories              |
| Book Rack             | Master      | Physical rack location tracking           |
| Book                  | Master      | Complete book record with copy tracking   |
| Library Member Type   | Master      | Configurable member categories            |
| Library Member        | Master      | Member profiles with issue history        |
| Member Issue History  | Child Table | Issue history embedded in member          |
| Library Book Issue    | Submittable | Core issue/return transaction             |
| Library Fine          | Submittable | Fine record with accounting entry         |
| Fine Payment Detail   | Child Table | Per-fine amounts in a payment             |
| Library Fine Payment  | Submittable | Payment against one or more fines         |
| Library Fine Waiver   | Submittable | Authorized fine waiver with adjustment JE |
| Library Settings      | Single      | Central accounting configuration          |

---

## Installation

### Prerequisites
- Frappe Bench v5+
- ERPNext v15
- Python 3.10+

### Steps

```bash
# 1. Clone the app into your bench apps folder
cd /home/frappe/frappe-bench
git clone https://github.com/your-org/library_management apps/library_management

# 2. Install Python package (no-deps since frappe is already installed)
env/bin/pip install --no-deps -e apps/library_management

# 3. Install app on your site
bench --site your-site.local install-app library_management

# 4. Run migrations (creates all tables and runs patches)
bench --site your-site.local migrate

# 5. Build frontend assets
bench build --app library_management

# 6. Restart bench
bench restart

# 7. Enable scheduler
bench --site your-site.local enable-scheduler
```

---

## How to Use

### INITIAL SETUP (One-time, done by Administrator)

#### Step 1 -- Configure Library Settings
1. Go to: Library Management > Fines & Accounting > Library Settings
2. Set Company, Fine Income Account, Member Receivable Account
3. Set Cash / Bank / UPI accounts for payment routing
4. Set default loan period and fine per day

#### Step 2 -- Verify Default Data
- Book Categories are auto-created: Fiction, Science & Technology, Reference, History & Culture,
  Academic & Educational, Arts & Literature, Business & Management
- Member Types are auto-created:

| Type    | Loan Period | Max Books | Fine/Day |
|---------|-------------|-----------|----------|
| Student | 14 days     | 3 books   | Rs. 2.00 |
| Staff   | 21 days     | 5 books   | Rs. 1.00 |
| Public  | 7 days      | 2 books   | Rs. 5.00 |

#### Step 3 -- Create Book Racks (optional)
1. Go to Library Management > Book Catalog > Book Rack
2. Create entries like: Rack Code = R-01, Rack Name = Ground Floor

---

### DAY-TO-DAY OPERATIONS

#### Adding Books to the Catalog
1. Go to Library Management > Book Catalog > New Book
2. Fill in Title, Author, ISBN (auto-becomes document name), Category, Rack Location
3. Set Total Copies (e.g. 5)
4. Save -- available_copies auto-sets to total_copies
5. Availability status updates automatically: Available / Partially Available / Not Available

#### Registering a New Member
1. Go to Library Management > Members > New Library Member
2. Fill in:
   - Full Name
   - Member Type (Student / Staff / Public)
   - Email, Phone, Address
   - ID Proof Type and Number
   - Membership Start Date and End Date
3. Save -- member gets auto-name like LM-2026-00001
4. Attach photo if needed

#### Issuing a Book to a Member
1. Go to Library Management > Transactions > New Library Book Issue
2. Select Member:
   - System fetches membership status automatically
   - Red warning shown if membership is expired or suspended
   - Orange warning shown if member has outstanding fines
3. Select Book:
   - Green indicator shows available copies
   - Red warning shown if 0 copies available
4. Issue Date defaults to today
5. Loan Period fetched from Member Type automatically
6. Due Date auto-calculated (issue date + loan period days)
7. Save, then Submit
8. Book available_copies decreases by 1 immediately

#### Returning a Book
1. Open the submitted Library Book Issue record
2. Click the "Process Return" button (appears only on submitted Issued/Overdue records)
3. Set Return Date (defaults to today)
4. Click Confirm Return
5. System automatically:
   - Increases book available_copies by 1
   - Marks issue status as Returned
   - Updates member issue history
   - If returned late: auto-creates a Library Fine with correct amount
   - If fine created: shows fine amount in success message

#### Recording a Fine Payment
1. Go to Library Management > Fines & Accounting > Library Fine Payment > New
2. Select Member
3. In the Fine Payments table, add the Library Fine record(s) to pay
4. Enter amount_to_pay for each fine (cannot exceed outstanding amount)
5. Select Payment Mode (Cash / Bank Transfer / UPI / Cheque)
6. Enter Reference Number (cheque no, UTR, UPI ref)
7. Save, then Submit
8. System automatically:
   - Updates Library Fine status (Unpaid -> Partially Paid -> Paid)
   - Updates member outstanding_fines balance
   - Creates a Payment Entry in ERPNext accounting

#### Waiving a Fine (Administrator / Accounts Staff only)
1. Go to Library Management > Fines & Accounting > Library Fine Waiver > New
2. Select the Library Fine to waive
3. Enter Waiver Amount and Waiver Reason
4. Select Approved By (User)
5. Save, then Submit
6. System automatically:
   - Updates fine outstanding amount
   - Updates member outstanding_fines
   - Creates adjustment Journal Entry in accounting

---

### REPORTS

#### Fine Collection Report
- Shows all fines raised and collected in a date range
- Filter by Member Type or Status (Unpaid / Paid / Waived)
- Summary row at bottom with totals
- Access: Library Management > Reports > Fine Collection Report

#### Overdue Books Report
- Shows all currently overdue books
- Displays days overdue, accrued fine, member phone and email
- Sorted by most overdue first
- Access: Library Management > Reports > Overdue Books Report

#### Member Activity Report
- Summary of each member's activity in a chosen period
- Shows books issued, returned, currently held, overdue count, fines
- Access: Library Management > Reports > Member Activity Report

#### Book Utilization Report
- Shows how often each book has been issued
- Utilization % = (times issued / total copies) x 100
- Books with 0 issues highlighted in red (rarely accessed)
- Access: Library Management > Reports > Book Utilization Report

#### Outstanding Fines Summary
- Shows all members with unpaid fine balances
- Sorted by highest outstanding amount first
- Grand total row at bottom
- Access: Library Management > Reports > Outstanding Fines Summary

#### Library Dashboard
- Access: Library Management > Reports > Library Dashboard
- Live number cards: Total Books, Books Issued Today, Overdue Books,
  Active Members, Outstanding Fines, Fine Collected This Month
- Charts: Books Issued Per Month, Member Type Distribution, Fine Collection Trend

---

### DAILY AUTOMATED TASKS (no manual action needed)

These run automatically every day via the Frappe scheduler:

| Task                     | What it does                                              |
|--------------------------|-----------------------------------------------------------|
| auto_mark_overdue        | Marks all issued books past due date as Overdue           |
| send_overdue_reminders   | Emails members with overdue books showing accrued fine    |
| update_membership_status | Auto-expires memberships whose end date has passed        |

Members also receive:
- Email when a fine is raised against them
- Email 7 days before their membership expires
- Email 1 day before their book is due

---

## Roles and Permissions

| Role                   | What they can do                                           |
|------------------------|------------------------------------------------------------|
| Library Administrator  | Full access -- catalog, members, fines, settings, reports |
| Library Staff          | Issue/return books, record payments, view members          |
| Library Accounts Staff | View and manage fines and financial records only           |
| Library Management     | Dashboard and reports -- read only, no data entry          |

### Assigning Roles to Users
1. Go to Settings > Users > select a user
2. Under Roles, add one of the four Library roles
3. Save

---

## Scheduled Tasks

```
library_management.library_management.tasks.auto_mark_overdue
library_management.library_management.tasks.send_overdue_reminders
library_management.library_management.tasks.update_membership_status
```

All three run daily. Verify in ERPNext: Settings > Scheduled Job Type.

---

## Project Structure

```
library_management/
|-- setup.py
|-- MANIFEST.in
|-- requirements.txt
|-- README.md
|-- library_management/
    |-- hooks.py
    |-- modules.txt
    |-- patches.txt
    |-- __init__.py
    |-- config/
    |   |-- desktop.py
    |   |-- docs.py
    |-- library_management/
    |   |-- tasks.py
    |   |-- doctype/
    |   |   |-- book/
    |   |   |-- book_category/
    |   |   |-- book_rack/
    |   |   |-- library_member/
    |   |   |-- library_member_type/
    |   |   |-- member_issue_history/
    |   |   |-- library_book_issue/
    |   |   |-- library_fine/
    |   |   |-- fine_payment_detail/
    |   |   |-- library_fine_payment/
    |   |   |-- library_fine_waiver/
    |   |   |-- library_settings/
    |   |-- report/
    |   |   |-- fine_collection_report/
    |   |   |-- overdue_books_report/
    |   |   |-- member_activity_report/
    |   |   |-- book_utilization_report/
    |   |   |-- outstanding_fines_summary/
    |   |-- dashboard/
    |   |-- dashboard_chart/
    |   |-- number_card/
    |   |-- workspace/
    |   |-- notification/
    |   |-- role/
    |   |-- patches/
    |       |-- v1_0/
    |           |-- create_library_accounts.py
    |           |-- setup_default_categories.py
    |           |-- setup_default_member_types.py
    |-- module_def/
```

---

## License

MIT License

**Publisher:** Klaimify Pvt. Ltd.
**Email:** support@klaimify.in
**Website:** https://www.klaimify.in