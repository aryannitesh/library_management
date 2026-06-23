app_name = "library_management"
app_title = "Library Management System"
app_publisher = "Klaimify Pvt. Ltd."
app_description = "Library Management System with Integrated Accounting"
app_icon = "octicon octicon-book"
app_color = "#1a73e8"
app_email = "support@klaimify.in"
app_license = "MIT"

# Fixtures: all module-owned documents exported with bench export-fixtures
fixtures = [
    {"dt": "DocType",
     "filters": [["module", "=", "Library Management"]]},
    {"dt": "Role",
     "filters": [["name", "in", [
         "Library Administrator", "Library Staff",
         "Library Accounts Staff", "Library Management",
     ]]]},
    {"dt": "Library Settings"},
    {"dt": "Report",
     "filters": [["module", "=", "Library Management"],
                 ["is_standard", "=", "Yes"]]},
    {"dt": "Number Card",
     "filters": [["module", "=", "Library Management"]]},
    {"dt": "Dashboard Chart",
     "filters": [["module", "=", "Library Management"]]},
    {"dt": "Dashboard",
     "filters": [["module", "=", "Library Management"]]},
    {"dt": "Workspace",
     "filters": [["module", "=", "Library Management"]]},
    {"dt": "Notification",
     "filters": [["name", "in", [
         "Fine Raised Alert",
         "Membership Expiry Warning",
         "Book Due Tomorrow Reminder",
     ]]]},
]

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "library_management.library_management.tasks.auto_mark_overdue",
        "library_management.library_management.tasks.send_overdue_reminders",
        "library_management.library_management.tasks.update_membership_status",
    ],
}

# Document Events
doc_events = {}

# Override standard whitelisted methods
override_whitelisted_methods = {}

# App-level CSS/JS includes
app_include_css = []
app_include_js = []

# Welcome email
welcome_email = None
