"""
Policy Editor Page - Individual policy editing and gate modification
"""

import streamlit as st
import os
import sys
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constitutional_enforcement_interactive import ConstitutionalEnforcer


# Page configuration
st.set_page_config(
    page_title="Policy Editor",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Policy Editor")
st.caption("Edit policy rules and modify gate configurations")

st.markdown("---")

# Policy selection
st.markdown("### Select Policy to Edit")

def get_policy_files():
    """Get all JSON policy files from root directory"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    policy_files = []
    if os.path.exists(parent_dir):
        for file in os.listdir(parent_dir):
            if file.endswith('.json') and os.path.isfile(os.path.join(parent_dir, file)):
                policy_files.append(file)
    return sorted(policy_files)

def load_policy_json(policy_filename: str) -> Optional[Dict[str, Any]]:
    """Load a policy file as JSON dictionary"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    policy_path = os.path.join(parent_dir, policy_filename)
    try:
        with open(policy_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

policy_files = get_policy_files()

if not policy_files:
    st.error("No policy JSON files found in root directory")
    st.stop()

# Get current selection or default to first file
current_policy = st.session_state.get("editor_selected_policy", policy_files[0] if policy_files else None)
selected_policy = st.selectbox(
    "Select Policy File",
    options=policy_files,
    index=policy_files.index(current_policy) if current_policy in policy_files else 0,
    key="editor_policy_selector"
)

if selected_policy != st.session_state.get("editor_selected_policy"):
    st.session_state.editor_selected_policy = selected_policy
    st.rerun()

# Load policy
policy = load_policy_json(selected_policy)

if not policy:
    st.error(f"Failed to load policy file: {selected_policy}")
    st.stop()

st.markdown("---")

# Policy metadata
st.markdown("### Policy Metadata")
col_meta1, col_meta2 = st.columns(2)

with col_meta1:
    policy_id = st.text_input("Policy ID", value=policy.get("policy_id", ""), key="editor_policy_id")
    policy_version = st.text_input("Version", value=policy.get("policy_version", ""), key="editor_policy_version")

with col_meta2:
    description = st.text_area("Description", value=policy.get("description", ""), key="editor_description", height=100)

st.markdown("---")

# Rules section
st.markdown("### Policy Rules")

# Initialize rule states if not exists
if "editor_rule_states" not in st.session_state:
    st.session_state.editor_rule_states = {}

rules = policy.get("rules", [])

if not rules:
    st.info("No rules defined in this policy.")
else:
    st.write(f"**{len(rules)} rule(s) defined**")
    
    # Rule list with editing capabilities
    for idx, rule in enumerate(rules):
        with st.expander(f"Rule {idx + 1}: {rule.get('rule_id', 'Unknown')}", expanded=False):
            col_rule1, col_rule2 = st.columns([3, 1])
            
            with col_rule1:
                rule_id = st.text_input("Rule ID", value=rule.get("rule_id", ""), key=f"rule_id_{idx}")
                description = st.text_area("Description", value=rule.get("description", ""), key=f"rule_desc_{idx}", height=80)
                clause_ref = st.text_input("Policy Clause Reference", value=rule.get("policy_clause_ref", ""), key=f"rule_clause_{idx}")
                severity = st.selectbox("Severity", ["low", "medium", "high", "critical"], 
                                       index=["low", "medium", "high", "critical"].index(rule.get("severity", "medium")) if rule.get("severity") in ["low", "medium", "high", "critical"] else 1,
                                       key=f"rule_severity_{idx}")
            
            with col_rule2:
                is_baseline = rule.get("baseline", False)
                if is_baseline:
                    st.markdown("🔒 **BASELINE**")
                    st.caption("Regulatory floor — cannot be modified")
                else:
                    st.markdown("⚙️ **CUSTOM**")
                    st.caption("Organizational policy")
                
                enabled = st.checkbox("Enabled", value=rule.get("enabled", True), key=f"rule_enabled_{idx}", disabled=is_baseline)
                
                if not is_baseline:
                    if st.button("Delete Rule", key=f"delete_rule_{idx}", type="secondary"):
                        rules.pop(idx)
                        st.success("Rule deleted (changes not saved yet)")
                        st.rerun()
            
            st.markdown("---")

st.markdown("---")

# Gate modification section
st.markdown("### Gate Configuration")

gate_tabs = st.tabs(["Gate 1-4 (Pre-Flight)", "Gate 5-6 (Verdict)", "Gate 7-8 (Evidence)"])

with gate_tabs[0]:
    st.markdown("#### Pre-Flight Gates")
    st.info("Gates 1-4: Input Validation, Intent Classification, Data Classification, Policy Lookup")
    st.caption("These gates perform validation and classification before making decisions.")
    
    # Gate-specific configuration would go here
    st.json(policy.get("gates", {}))

with gate_tabs[1]:
    st.markdown("#### Verdict Gates")
    st.info("Gates 5-6: Permission Check, Action Approval")
    st.caption("These gates make the final verdict: ALLOW, ESCALATE, or DENY.")
    
    # Gate-specific configuration would go here
    st.json(policy.get("gates", {}))

with gate_tabs[2]:
    st.markdown("#### Evidence Gates")
    st.info("Gates 7-8: Evidence Capture, Audit Export")
    st.caption("These gates capture evidence and prepare audit packets.")
    
    # Gate-specific configuration would go here
    st.json(policy.get("gates", {}))

st.markdown("---")

# Save/Export section
st.markdown("### Save Changes")

col_save1, col_save2, col_save3 = st.columns(3)

with col_save1:
    if st.button("💾 Save to File", type="primary"):
        # Update policy with edited values
        policy["policy_id"] = policy_id
        policy["policy_version"] = policy_version
        policy["description"] = description
        
        # Save to file
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        policy_path = os.path.join(parent_dir, selected_policy)
        try:
            with open(policy_path, 'w') as f:
                json.dump(policy, f, indent=2)
            st.success(f"Policy saved to {selected_policy}")
        except Exception as e:
            st.error(f"Failed to save policy: {str(e)}")

with col_save2:
    if st.button("📥 Export as JSON"):
        policy_json = json.dumps(policy, indent=2)
        st.download_button(
            label="Download Policy JSON",
            data=policy_json,
            file_name=f"policy_{policy_id}_{policy_version}.json",
            mime="application/json"
        )

with col_save3:
    if st.button("🔄 Reset Changes"):
        st.session_state.editor_selected_policy = None
        st.rerun()

# Warning about baseline rules
st.markdown("---")
st.warning("⚠️ **Note:** Baseline rules (marked with 🔒) cannot be disabled or deleted as they represent regulatory requirements. Only custom rules can be modified.")

# Navigation
st.markdown("---")
if st.button("← Back to Main Dashboard"):
    st.switch_page("app.py")
