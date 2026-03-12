"""Rules editor component for viewing and saving rule sets."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from config.settings import SUPPORTED_OPERATORS
from models.rule_model import Rule
from services.rule_service import RuleService
from ui.design_system import render_action_bar, render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def render_rules_editor(rule_service: RuleService, category: str, rule_source: str | None = None) -> list[Rule]:
    """Render an editable rules table and return the active rules."""
    apply_finance_theme()
    rules = rule_service.get_rules(category)
    if not rules:
        render_section_header("Rules Manager", "Edit the rule profile used for this market-cap bucket.")
        st.warning("No rules configured for this market-cap category.")
        return []

    render_status_badge("Custom Rules" if rule_source == "custom" else "Default Rules", tone="neutral")
    render_section_header(
        "Rules Manager",
        f"Editing the {category.replace('_', ' ').title()} framework used by the current analysis.",
    )
    preview_frame = pd.DataFrame([rule.to_dict() for rule in rules]).fillna("")
    grouped_categories = [value for value in sorted(preview_frame["category"].astype(str).unique()) if value and value.lower() != "none"]
    render_action_bar(
        "Rule framework",
        "Edit thresholds, operators, labels, and rationale. Save to persist a user-scoped custom profile.",
        badges=[
            (category.replace("_", " ").title(), "info"),
            (f"{len(rules)} rules", "neutral"),
            ("Grouped" if grouped_categories else "Flat", "warning"),
        ],
    )
    editor_data = pd.DataFrame([rule.to_dict() for rule in rules])
    edited_data = st.data_editor(
        editor_data,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"rules_editor_{category}",
        column_config={
            "category": st.column_config.TextColumn("category"),
            "label": st.column_config.TextColumn("label"),
            "operator": st.column_config.SelectboxColumn(
                "operator",
                options=SUPPORTED_OPERATORS,
                required=True,
            ),
            "value": st.column_config.NumberColumn("value", required=True, step=0.1),
        },
    )

    edited_rules: list[Rule] = []
    for _, row in edited_data.iterrows():
        parameter = str(row.get("parameter", "")).strip()
        operator = str(row.get("operator", "")).strip()
        rationale = str(row.get("rationale", "")).strip()
        value_raw = row.get("value", 0)

        if not parameter:
            continue
        if not rule_service.validate_operator(operator):
            st.error(f"Unsupported operator detected: {operator}")
            return rules

        edited_rules.append(
            Rule(
                parameter=parameter,
                operator=operator,
                value=float(value_raw),
                rationale=rationale,
                category=str(row.get("category", "")).strip() or None,
                label=str(row.get("label", "")).strip() or None,
            )
        )

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Save Rules", key=f"save_rules_{category}", use_container_width=True):
            rule_service.save_rules(category, edited_rules)
            st.success("Rules saved to your custom profile.")
    with action_cols[1]:
        st.download_button(
            label="Download Rules JSON",
            data=rule_service.export_rules_json(category),
            file_name=f"{category}_rules.json",
            mime="application/json",
            key=f"download_rules_{category}",
            use_container_width=True,
        )

    if grouped_categories:
        render_section_header("Category Preview", "Quick grouped preview of the active rule set before saving.")
        preview_tabs = st.tabs([group.title() for group in grouped_categories])
        for tab, group in zip(preview_tabs, grouped_categories):
            with tab:
                group_frame = editor_data[editor_data["category"].fillna("").astype(str) == group].copy()
                st.dataframe(group_frame, use_container_width=True, hide_index=True)

    render_section_header("Import Rule Profile", "Replace the current custom rules for this bucket with a validated JSON profile.")
    uploaded_profile = st.file_uploader(
        "Upload Rule Profile JSON",
        type=["json"],
        key=f"upload_rules_profile_{category}",
    )
    if uploaded_profile is not None:
        try:
            payload = json.load(uploaded_profile)
        except json.JSONDecodeError:
            st.error("Uploaded file is not valid JSON.")
            return edited_rules

        is_valid, message, imported_rules = rule_service.validate_rule_payload(payload)
        if not is_valid:
            st.error(message)
            return edited_rules

        if st.button("Import Rules", key=f"import_rules_{category}", use_container_width=True):
            rule_service.save_rules(category, imported_rules)
            st.success("Imported rule profile saved as custom rules.")
            st.rerun()

    return edited_rules
