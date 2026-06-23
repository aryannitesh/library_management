// Copyright (c) 2024, Klaimify Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Book", {
    refresh(frm) {
        frm.trigger("set_availability_color");
    },

    total_copies(frm) {
        frm.trigger("update_availability_status");
    },

    available_copies(frm) {
        frm.trigger("update_availability_status");
    },

    update_availability_status(frm) {
        const total = frm.doc.total_copies || 0;
        const available = frm.doc.available_copies || 0;

        let status;
        if (available <= 0) {
            status = "Not Available";
        } else if (available >= total) {
            status = "Available";
        } else {
            status = "Partially Available";
        }

        frappe.model.set_value(frm.doctype, frm.docname, "availability_status", status);
        frm.trigger("set_availability_color");
    },

    set_availability_color(frm) {
        const status = frm.doc.availability_status;
        const fieldEl = frm.fields_dict["availability_status"].$wrapper;

        // Remove previous color indicators
        fieldEl.find(".availability-badge").remove();

        const colorMap = {
            "Available":           { bg: "#d4edda", color: "#155724", border: "#c3e6cb" },
            "Partially Available": { bg: "#fff3cd", color: "#856404", border: "#ffeeba" },
            "Not Available":       { bg: "#f8d7da", color: "#721c24", border: "#f5c6cb" },
        };

        const style = colorMap[status];
        if (!style) return;

        const badge = $(
            `<span class="availability-badge" style="
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                background-color: ${style.bg};
                color: ${style.color};
                border: 1px solid ${style.border};
                margin-top: 4px;
            ">${status}</span>`
        );

        fieldEl.find(".control-value").html("").append(badge);
    },
});
