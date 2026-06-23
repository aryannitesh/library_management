// Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Library Book Issue", {

    // ------------------------------------------------------------------
    // Form load / refresh
    // ------------------------------------------------------------------
    refresh(frm) {
        frm.trigger("show_return_button");
    },

    // ------------------------------------------------------------------
    // Member field change
    // ------------------------------------------------------------------
    member(frm) {
        if (!frm.doc.member) return;

        frappe.db.get_value(
            "Library Member",
            frm.doc.member,
            ["membership_status", "outstanding_fines", "full_name"],
            (r) => {
                if (!r) return;

                if (r.membership_status !== "Active") {
                    frappe.msgprint({
                        title: __("Membership Issue"),
                        message: __(
                            "<b>&#9888; WARNING:</b> This member's membership is "
                            + "<b>{0}</b>. Book cannot be issued.",
                            [r.membership_status]
                        ),
                        indicator: "red",
                    });
                }

                if (r.outstanding_fines > 0) {
                    const fmt = format_currency(
                        r.outstanding_fines,
                        frappe.defaults.get_default("currency") || "INR"
                    );
                    frappe.show_alert({
                        message: __("This member has outstanding fines of {0}", [fmt]),
                        indicator: "orange",
                    }, 8);
                }
            }
        );
    },

    // ------------------------------------------------------------------
    // Book field change
    // ------------------------------------------------------------------
    book(frm) {
        if (!frm.doc.book) return;

        frappe.db.get_value("Book", frm.doc.book, "available_copies", (r) => {
            if (!r) return;
            const copies = r.available_copies || 0;

            if (copies <= 0) {
                frappe.msgprint({
                    title: __("Not Available"),
                    message: __(
                        "<b>&#9888; No copies available.</b> "
                        + "This book cannot be issued right now."
                    ),
                    indicator: "red",
                });
            } else {
                frappe.show_alert({
                    message: __("{0} {1} available", [
                        copies,
                        copies === 1 ? __("copy") : __("copies"),
                    ]),
                    indicator: "green",
                }, 5);
            }
        });
    },

    // ------------------------------------------------------------------
    // Due date auto-calculation
    // ------------------------------------------------------------------
    issue_date(frm) {
        frm.trigger("calculate_due_date");
    },

    loan_period_days(frm) {
        frm.trigger("calculate_due_date");
    },

    calculate_due_date(frm) {
        if (!frm.doc.issue_date) return;

        const days = frm.doc.loan_period_days || 14;
        const due  = frappe.datetime.add_days(frm.doc.issue_date, days);

        frappe.model.set_value(frm.doctype, frm.docname, "due_date", due);

        frappe.show_alert({
            message: __("Due Date: {0} ({1}-day loan)", [
                frappe.datetime.str_to_user(due),
                days,
            ]),
            indicator: "blue",
        }, 5);
    },

    // ------------------------------------------------------------------
    // Process Return button (shown when submitted + status = Issued/Overdue)
    // ------------------------------------------------------------------
    show_return_button(frm) {
        if (
            frm.doc.docstatus === 1
            && ["Issued", "Overdue"].includes(frm.doc.status)
        ) {
            frm.add_custom_button(__("&#x1F4E5; Process Return"), () => {
                frm.trigger("open_return_dialog");
            }, __("Actions"));

            // Make the button prominent
            frm.page.set_primary_action(__("&#x1F4E5; Process Return"), () => {
                frm.trigger("open_return_dialog");
            });
        }
    },

    open_return_dialog(frm) {
        const today = frappe.datetime.get_today();

        const d = new frappe.ui.Dialog({
            title: __("Process Book Return"),
            fields: [
                {
                    label:     __("Return Date"),
                    fieldname: "return_date",
                    fieldtype: "Date",
                    default:   today,
                    reqd:      1,
                },
                {
                    fieldtype: "HTML",
                    options:   `<p class="text-muted small">
                        Due Date: <b>${frappe.datetime.str_to_user(frm.doc.due_date)}</b>
                    </p>`,
                },
            ],
            primary_action_label: __("Confirm Return"),
            primary_action(values) {
                d.hide();

                frappe.call({
                    method: "library_management.library_management.doctype"
                            + ".library_book_issue.library_book_issue.process_return",
                    args: {
                        docname:     frm.doc.name,
                        return_date: values.return_date,
                    },
                    freeze:         true,
                    freeze_message: __("Processing return..."),
                    callback(r) {
                        if (r.exc) return;

                        const res = r.message;
                        if (res.days_overdue > 0 && res.fine_amount > 0) {
                            const fmt = format_currency(
                                res.fine_amount,
                                frappe.defaults.get_default("currency") || "INR"
                            );
                            frappe.msgprint({
                                title:   __("Return Processed — Fine Applied"),
                                message: __(
                                    "Book returned <b>{0} day(s) late</b>.<br>"
                                    + "Fine of <b>{1}</b> has been created.",
                                    [res.days_overdue, fmt]
                                ),
                                indicator: "orange",
                            });
                        } else {
                            frappe.show_alert({
                                message:   __("Book returned successfully. No fine applicable."),
                                indicator: "green",
                            }, 5);
                        }

                        frm.reload_doc();
                    },
                });
            },
        });

        d.show();
    },
});
