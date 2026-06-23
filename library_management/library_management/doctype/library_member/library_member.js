// Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Library Member", {

    refresh(frm) {
        frm.trigger("show_status_banners");
    },

    // ------------------------------------------------------------------
    // Member Type change — show loan period + fine rate as info
    // ------------------------------------------------------------------
    member_type(frm) {
        if (!frm.doc.member_type) return;

        frappe.db.get_value(
            "Library Member Type",
            frm.doc.member_type,
            ["loan_period_days", "fine_per_day", "max_books_allowed"],
            (r) => {
                if (!r) return;
                frappe.show_alert({
                    message: __(
                        "Member Type: <b>{0}</b> &nbsp;|&nbsp; "
                        + "Loan Period: <b>{1} days</b> &nbsp;|&nbsp; "
                        + "Max Books: <b>{2}</b> &nbsp;|&nbsp; "
                        + "Fine: <b>&#8377;{3}/day</b>",
                        [
                            frm.doc.member_type,
                            r.loan_period_days,
                            r.max_books_allowed,
                            r.fine_per_day,
                        ]
                    ),
                    indicator: "blue",
                }, 7);
            }
        );
    },

    // ------------------------------------------------------------------
    // Alert banners
    // ------------------------------------------------------------------
    show_status_banners(frm) {
        // Clear previous banners
        frm.dashboard.clear_headline();
        frm.layout.show_message("");

        const status   = frm.doc.membership_status;
        const fines    = frm.doc.outstanding_fines || 0;
        const currency = frappe.defaults.get_default("currency") || "INR";

        if (status === "Expired") {
            frm.dashboard.set_headline_alert(
                '<span style="color:#c0392b; font-weight:600;">'
                + "&#9888; Membership Expired. Book issuance is blocked."
                + "</span>",
                "red"
            );
        }

        if (fines > 0) {
            const formatted = format_currency(fines, currency);
            frm.dashboard.add_comment(
                `<span style="color:#e67e22; font-weight:600;">
                    &#9888; This member has outstanding fines of ${formatted}
                </span>`,
                "orange",
                true
            );
        }
    },
});
