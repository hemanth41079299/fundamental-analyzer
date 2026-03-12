"""Admin-only user approval interface."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.audit_service import log_audit_event
from services.auth_service import require_admin
from services.user_service import list_pending_users, update_user_approval_status
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def render_admin_user_approvals_page() -> None:
    """Render the pending-user approval page for admins."""
    apply_finance_theme()
    require_admin()

    render_section_header(
        "User Approvals",
        "Review pending registrations and approve or reject access to the platform.",
    )

    pending_users = list_pending_users()
    if not pending_users:
        render_empty_state("No pending users", "All current registrations have already been reviewed.")
        return

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge(f"{len(pending_users)} pending", tone="warning")
    display_frame = pd.DataFrame(pending_users).rename(
        columns={
            "name": "Name",
            "email": "Email",
            "approval_status": "Status",
            "is_active": "Active",
            "approval_note": "Note",
            "created_at": "Created At",
            "updated_at": "Updated At",
        }
    )
    st.dataframe(
        display_frame[["Name", "Email", "Status", "Active", "Note", "Created At", "Updated At"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    selected_user = st.selectbox(
        "Select pending user",
        options=pending_users,
        format_func=lambda item: f"{item['name']} ({item['email']})",
        key="admin_pending_user",
    )

    action_column, note_column = st.columns([0.9, 1.4])
    with action_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Approval Action", tone="info")
        render_section_header("Approve User", "Approving activates login access immediately.")
        if st.button("Approve Selected User", use_container_width=True):
            update_user_approval_status(
                user_id=int(selected_user["id"]),
                approval_status="approved",
                is_active=True,
                approval_note=None,
            )
            log_audit_event(
                "approve_user",
                details={"approved_user_id": selected_user["id"], "email": selected_user["email"]},
            )
            st.success("User approved successfully.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with note_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Rejection Action", tone="warning")
        render_section_header("Reject User", "Rejecting keeps the account inactive and stores an optional reason.")
        rejection_reason = st.text_area(
            "Optional rejection reason",
            placeholder="Incomplete information or access not authorized",
            key="admin_rejection_reason",
        )
        if st.button("Reject Selected User", use_container_width=True):
            update_user_approval_status(
                user_id=int(selected_user["id"]),
                approval_status="rejected",
                is_active=False,
                approval_note=rejection_reason,
            )
            log_audit_event(
                "reject_user",
                details={
                    "rejected_user_id": selected_user["id"],
                    "email": selected_user["email"],
                    "reason": rejection_reason,
                },
            )
            st.success("User rejected successfully.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
