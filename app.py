"""
Streamlit UI Application for Constitutional Ontology Enforcement
----------------------------------------------------------------
Complete implementation with:
1. Single-page demo dashboard
2. Visual gate activation
3. Human-in-the-loop approval modal
4. Live audit log panel
5. Export evidence pack
"""

import streamlit as st
import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Tuple, Optional
import io

from constitutional_enforcement_interactive import ConstitutionalEnforcer, Decision

# Import tool stubs from orchestrator
def tool_sharepoint_read(path: str) -> Dict[str, Any]:
    return {"source_uri": f"sharepoint://{path}", "content": "Draft policy template text...", "doc_hash": "abc123"}

def tool_occ_query(query: str) -> Dict[str, Any]:
    return {"source_uri": "occ://guidance/2024-xyz", "content": "OCC guidance excerpt...", "doc_hash": "def456"}

def tool_write_draft_doc(doc_id: str, text: str) -> Dict[str, Any]:
    return {"doc_id": doc_id, "status": "written_to_draft", "version_id": "v7"}

def tool_jira_create_task(title: str, description: str) -> Dict[str, Any]:
    return {"issue_key": "COMPL-123", "status": "created"}

TOOLS = {
    "sharepoint_read": tool_sharepoint_read,
    "occ_query": tool_occ_query,
    "write_draft": tool_write_draft_doc,
    "jira_create": tool_jira_create_task,
}


class ConstitutionalEnforcementUI:
    """Complete UI class for constitutional enforcement system."""
    
    # Gate definitions
    GATES = {
        "U-I": {"name": "User Inbound", "domain": "User", "direction": "Inbound", "icon": "👤"},
        "U-O": {"name": "User Outbound", "domain": "User", "direction": "Outbound", "icon": "👤"},
        "S-I": {"name": "System Inbound", "domain": "System", "direction": "Inbound", "icon": "⚙️"},
        "S-O": {"name": "System Outbound", "domain": "System", "direction": "Outbound", "icon": "⚙️"},
        "M-I": {"name": "Memory Inbound", "domain": "Memory", "direction": "Inbound", "icon": "💾"},
        "M-O": {"name": "Memory Outbound", "domain": "Memory", "direction": "Outbound", "icon": "💾"},
        "A-I": {"name": "Agent Inbound", "domain": "Agent", "direction": "Inbound", "icon": "🤖"},
        "A-O": {"name": "Agent Outbound", "domain": "Agent", "direction": "Outbound", "icon": "🤖"},
    }
    
    def __init__(self, policy_path: str = None):
        if policy_path is None:
            policy_path = os.environ.get("POLICY_PATH", "policy_bank_compliance_v1.json")
        self.policy_path = policy_path
    
    def initialize_session_state(self):
        """Initialize all session state variables."""
        if 'enforcer' not in st.session_state:
            try:
                st.session_state.enforcer = ConstitutionalEnforcer(self.policy_path)
            except FileNotFoundError:
                st.error(f"Policy file not found: {self.policy_path}")
                st.stop()
            except Exception as e:
                st.error(f"Error loading policy: {str(e)}")
                st.stop()
        
        if 'execution_log' not in st.session_state:
            st.session_state.execution_log = []
        
        if 'active_gate' not in st.session_state:
            st.session_state.active_gate = None
        
        if 'execution_in_progress' not in st.session_state:
            st.session_state.execution_in_progress = False
        
        if 'pending_approval' not in st.session_state:
            st.session_state.pending_approval = None
        
        if 'execution_results' not in st.session_state:
            st.session_state.execution_results = []
        
        if 'execution_state' not in st.session_state:
            st.session_state.execution_state = None
        
        if 'remaining_tool_calls' not in st.session_state:
            st.session_state.remaining_tool_calls = []
        
        if 'pending_response' not in st.session_state:
            st.session_state.pending_response = None
        
        if 'current_tool_index' not in st.session_state:
            st.session_state.current_tool_index = 0
        
        if 'scenario_user_id' not in st.session_state:
            st.session_state.scenario_user_id = None
    
    def render_gate_visualization(self, active_gate: str = None):
        """Render visual representation of gates with active highlighting."""
        st.markdown("### Gate Activation Status")
        
        # Group gates by domain
        domains = {}
        for gate_id, gate_info in self.GATES.items():
            domain = gate_info["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append((gate_id, gate_info))
        
        # Create columns for each domain
        cols = st.columns(len(domains))
        
        for idx, (domain, gates) in enumerate(domains.items()):
            with cols[idx]:
                st.markdown(f"**{domain}**")
                for gate_id, gate_info in gates:
                    is_active = (gate_id == active_gate)
                    
                    # Style based on active state
                    if is_active:
                        st.markdown(
                            f'<div style="background-color: #28a745; color: white; padding: 10px; '
                            f'border-radius: 5px; margin: 5px 0; border: 2px solid #20c997;">'
                            f'<strong>{gate_info["icon"]} {gate_info["name"]}</strong><br>'
                            f'<small>{gate_info["direction"]}</small></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div style="background-color: #f8f9fa; color: #6c757d; padding: 10px; '
                            f'border-radius: 5px; margin: 5px 0; border: 1px solid #dee2e6;">'
                            f'{gate_info["icon"]} {gate_info["name"]}<br>'
                            f'<small>{gate_info["direction"]}</small></div>',
                            unsafe_allow_html=True
                        )
    
    def render_approval_modal(self):
        """Render approval modal when action requires human approval."""
        if st.session_state.pending_approval:
            approval = st.session_state.pending_approval
            
            # Use container as modal equivalent
            with st.container():
                st.markdown("---")
                st.warning("⚠️ **APPROVAL REQUIRED**")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Gate:** {approval.get('gate', 'N/A')}")
                    st.markdown(f"**Action:** {approval.get('action', 'N/A')}")
                    if approval.get('details'):
                        st.json(approval['details'])
                    if approval.get('reason'):
                        st.info(f"**Policy Reason:** {approval['reason']}")
                
                with col2:
                    approve_btn = st.button("✅ Approve", key="approve_btn", type="primary", use_container_width=True)
                    deny_btn = st.button("❌ Deny", key="deny_btn", type="secondary", use_container_width=True)
                
                if approve_btn:
                    st.session_state.pending_approval = None
                    self.continue_execution_after_approval(True)
                    st.rerun()
                
                if deny_btn:
                    st.session_state.pending_approval = None
                    self.continue_execution_after_approval(False)
                    st.rerun()
    
    def render_live_audit_log(self):
        """Render live, append-only audit log."""
        st.markdown("### Live Audit Log")
        
        enforcer = st.session_state.enforcer
        audit_log = enforcer.get_audit_log()
        
        # Create a scrollable container for the log
        log_container = st.container()
        
        with log_container:
            if audit_log:
                # Display entries in reverse chronological order (newest first)
                for entry in reversed(audit_log[-50:]):  # Show last 50 entries
                    timestamp = entry.get('timestamp', 'N/A')
                    gate = entry.get('gate', 'N/A')
                    action = entry.get('action', 'N/A')
                    decision = entry.get('decision', 'N/A')
                    controls = entry.get('controls', [])
                    
                    # Color code by decision
                    if decision == 'ALLOW':
                        decision_color = "#28a745"
                        decision_icon = "✅"
                    elif decision == 'DENY':
                        decision_color = "#dc3545"
                        decision_icon = "❌"
                    elif decision in ['REQUIRE_APPROVAL', 'ESCALATE']:
                        decision_color = "#ffc107"
                        decision_icon = "⚠️"
                    else:
                        decision_color = "#6c757d"
                        decision_icon = "ℹ️"
                    
                    # Format entry
                    st.markdown(
                        f'<div style="background-color: #f8f9fa; padding: 8px; margin: 4px 0; '
                        f'border-left: 4px solid {decision_color}; border-radius: 3px;">'
                        f'<small><strong>{decision_icon} [{timestamp}]</strong> | '
                        f'<strong>{gate}</strong> | {action} | '
                        f'<span style="color: {decision_color}"><strong>{decision}</strong></span></small><br>'
                        f'<small>Controls: {", ".join(controls) if controls else "None"}</small></div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No audit log entries yet. Run a demo scenario to see enforcement activity.")
    
    def execute_tool_with_enforcement(self, tool_name: str, params: Dict[str, Any], user_id: str) -> Tuple[Decision, Dict[str, Any]]:
        """Execute a tool call through the enforcement layer."""
        enforcer = st.session_state.enforcer
        
        # Step 1: S-O Gate (pre_tool_call)
        st.session_state.active_gate = "S-O"
        
        pre = enforcer.pre_tool_call(tool_name, params, user_id)
        
        if pre.decision == Decision.DENY:
            st.session_state.active_gate = None
            return pre.decision, {"error": pre.denial_reason, "gate": pre.gate}
        
        if pre.decision == Decision.REQUIRE_APPROVAL:
            # Request approval
            action_id = str(uuid.uuid4())[:8]
            enforcer.request_approval(action_id, "S-O", tool_name, user_id, {"params": params})
            enforcer._log_audit("S-O", tool_name, "REQUIRE_APPROVAL", user_id, pre.controls_applied, pre.evidence)
            
            # Set pending approval in session state - execution will pause here
            st.session_state.pending_approval = {
                "action_id": action_id,
                "gate": "S-O",
                "action": tool_name,
                "details": params,
                "reason": "Policy requires human approval for this action"
            }
            
            # Store continuation state
            st.session_state.execution_state = {
                "step": "waiting_approval",
                "tool_name": tool_name,
                "params": params,
                "user_id": user_id,
                "action_id": action_id
            }
            
            return Decision.REQUIRE_APPROVAL, {"approval_id": action_id, "message": "Waiting for approval"}
        
        # Step 2: Execute tool
        if tool_name not in TOOLS:
            st.session_state.active_gate = None
            return Decision.DENY, {"error": f"Tool not registered: {tool_name}"}
        
        raw_result = TOOLS[tool_name](**params)
        
        # Step 3: S-I Gate (post_tool_result)
        st.session_state.active_gate = "S-I"
        
        post = enforcer.post_tool_result(tool_name, raw_result, user_id)
        
        if post.decision == Decision.DENY:
            st.session_state.active_gate = None
            return post.decision, {"error": post.denial_reason, "gate": post.gate}
        
        st.session_state.active_gate = None
        return Decision.ALLOW, raw_result
    
    def continue_execution_after_approval(self, approved: bool):
        """Continue execution after approval decision."""
        if 'execution_state' not in st.session_state:
            return
        
        state = st.session_state.execution_state
        enforcer = st.session_state.enforcer
        action_id = state.get("action_id")
        tool_name = state["tool_name"]
        params = state["params"]
        user_id = state["user_id"]
        
        if not approved:
            enforcer.deny_approval(action_id, "ui_user", "Denied via UI")
            enforcer._log_audit("S-O", tool_name, "DENIED_BY_HUMAN", "ui_user", ["human_denial"], {"action_id": action_id})
            st.session_state.execution_results.append({
                "step": f"Tool: {tool_name}",
                "decision": "DENY",
                "reason": "Action denied by user"
            })
            st.session_state.execution_in_progress = False
            st.session_state.active_gate = None
            del st.session_state.execution_state
            return
        
        # Approved - continue execution
        enforcer.approve(action_id, "ui_user")
        enforcer._log_audit("S-O", tool_name, "APPROVED", "ui_user", ["human_approval"], {"action_id": action_id})
        
        # Execute tool
        raw_result = TOOLS[tool_name](**params)
        
        # S-I Gate
        st.session_state.active_gate = "S-I"
        post = enforcer.post_tool_result(tool_name, raw_result, user_id)
        
        if post.decision == Decision.DENY:
            st.session_state.execution_results.append({
                "step": f"Tool: {tool_name}",
                "decision": "DENY",
                "reason": post.denial_reason
            })
            st.session_state.execution_in_progress = False
        else:
            st.session_state.execution_results.append({
                "step": f"Tool: {tool_name}",
                "decision": "ALLOW",
                "payload": raw_result
            })
            # Increment tool index and continue
            if 'current_tool_index' in st.session_state:
                st.session_state.current_tool_index += 1
        
        st.session_state.active_gate = None
        del st.session_state.execution_state
        
        # Continue with remaining steps if any
        if 'remaining_tool_calls' in st.session_state:
            self._process_remaining_tool_calls()
        elif 'pending_response' in st.session_state:
            self._process_response()
        else:
            st.session_state.execution_in_progress = False
    
    def _process_remaining_tool_calls(self):
        """Process remaining tool calls in the scenario."""
        tool_calls = st.session_state.remaining_tool_calls
        user_id = st.session_state.scenario_user_id
        
        # Get current tool index
        tool_index = st.session_state.get('current_tool_index', 0)
        
        if tool_index < len(tool_calls):
            tool_call = tool_calls[tool_index]
            tool_name = tool_call.get("tool")
            params = tool_call.get("params", {})
            
            decision, payload = self.execute_tool_with_enforcement(tool_name, params, user_id)
            
            if decision == Decision.REQUIRE_APPROVAL:
                # Execution paused for approval - don't increment index yet
                return
            
            # Tool call completed, record result
            st.session_state.execution_results.append({
                "step": f"Tool: {tool_name}",
                "decision": decision.value if hasattr(decision, 'value') else str(decision),
                "payload": payload
            })
            
            if decision == Decision.DENY:
                st.session_state.execution_in_progress = False
                return
            
            # Move to next tool
            st.session_state.current_tool_index = tool_index + 1
            
            # Continue with next tool call
            self._process_remaining_tool_calls()
            return
        
        # All tool calls done, check if response needed
        if 'pending_response' in st.session_state:
            self._process_response()
        else:
            st.session_state.execution_in_progress = False
    
    def _process_response(self):
        """Process response output."""
        response_config = st.session_state.pending_response
        user_id = st.session_state.scenario_user_id
        
        response_text = response_config.get("response_text", "Generated response with citations")
        citations = response_config.get("citations", [])
        
        st.session_state.active_gate = "U-O"
        enforcer = st.session_state.enforcer
        uo_result = enforcer.pre_response(response_text, citations, user_id)
        
        st.session_state.execution_results.append({
            "step": "Response Output",
            "decision": uo_result.decision.value if hasattr(uo_result.decision, 'value') else str(uo_result.decision),
            "reason": uo_result.denial_reason if uo_result.decision == Decision.DENY else None
        })
        
        st.session_state.active_gate = None
        del st.session_state.pending_response
        st.session_state.execution_in_progress = False
    
    def run_demo_scenario(self, scenario_name: str, scenario_config: Dict[str, Any]):
        """Execute a predefined demo scenario."""
        st.session_state.execution_in_progress = True
        st.session_state.execution_results = []
        st.session_state.active_gate = None
        st.session_state.pending_approval = None
        
        user_id = scenario_config.get("user_id", "analyst_123")
        st.session_state.scenario_user_id = user_id
        
        # Step 1: U-I Gate (post_user_input)
        user_input = scenario_config.get("user_input", "")
        if user_input:
            st.session_state.active_gate = "U-I"
            enforcer = st.session_state.enforcer
            ui_result = enforcer.post_user_input(user_input, user_id, "session_001")
            
            if ui_result.decision == Decision.DENY:
                st.session_state.execution_results.append({
                    "step": "User Input",
                    "decision": "DENY",
                    "reason": ui_result.denial_reason
                })
                st.session_state.execution_in_progress = False
                st.session_state.active_gate = None
                return
            st.session_state.active_gate = None
        
        # Step 2: Execute tool calls
        tool_calls = scenario_config.get("tool_calls", [])
        st.session_state.remaining_tool_calls = tool_calls.copy()
        st.session_state.current_tool_index = 0
        
        # Step 3: Store response config if needed (will be processed after tool calls)
        if scenario_config.get("generate_response"):
            st.session_state.pending_response = {
                "response_text": scenario_config.get("response_text", "Generated response with citations"),
                "citations": scenario_config.get("citations", [])
            }
        
        self._process_remaining_tool_calls()
    
    def get_evidence_pack(self) -> Dict[str, Any]:
        """Generate evidence pack for export."""
        enforcer = st.session_state.enforcer
        
        evidence = {
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "policy_file": self.policy_path,
            "session_audit_log": enforcer.get_audit_log(),
            "execution_results": st.session_state.execution_results,
            "pending_approvals": enforcer.pending_approvals,
            "gate_sequence": [
                {"gate": entry.get('gate'), "timestamp": entry.get('timestamp'), 
                 "decision": entry.get('decision'), "action": entry.get('action')}
                for entry in enforcer.get_audit_log()
            ]
        }
        
        return evidence
    
    def render_dashboard(self):
        """Render the main demo dashboard."""
        st.header("Constitutional Ontology Enforcement Dashboard")
        st.markdown("---")
        
        # Demo scenarios
        st.markdown("### Demo Scenarios")
        
        scenarios = {
            "Scenario 1: Allowed Tool Call": {
                "user_input": "Read the Q4 policy draft",
                "tool_calls": [
                    {"tool": "sharepoint_read", "params": {"path": "/policies/draft/q4-policy.md"}}
                ],
                "generate_response": True,
                "response_text": "Policy draft retrieved successfully.",
                "citations": [],
                "user_id": "analyst_123"
            },
            "Scenario 2: Tool Requiring Approval": {
                "user_input": "Create a Jira task for policy review",
                "tool_calls": [
                    {"tool": "jira_create", "params": {"title": "Review Q4 policy", "description": "Please review draft"}}
                ],
                "generate_response": False,
                "user_id": "analyst_123"
            },
            "Scenario 3: Denied Tool Call": {
                "user_input": "Send email to external recipient",
                "tool_calls": [
                    {"tool": "email_send", "params": {"to": "external@other.com", "subject": "Policy"}}
                ],
                "generate_response": False,
                "user_id": "analyst_123"
            },
            "Scenario 4: Full Workflow": {
                "user_input": "Draft a Q4 compliance policy update under OCC supervision",
                "tool_calls": [
                    {"tool": "sharepoint_read", "params": {"path": "/policies/draft/q4-policy.md"}},
                    {"tool": "occ_query", "params": {"query": "capital reserve requirements baseline"}},
                    {"tool": "jira_create", "params": {"title": "Review Q4 policy", "description": "Please review draft"}}
                ],
                "generate_response": True,
                "response_text": "OCC requires all banks to maintain capital reserves of 8%.",
                "citations": [{"source_uri": "occ://guidance/2024-xyz", "doc_hash": "def456"}],
                "user_id": "analyst_123"
            }
        }
        
        # Scenario selection and execution
        selected_scenario = st.selectbox("Select a demo scenario:", list(scenarios.keys()))
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.json(scenarios[selected_scenario])
        with col2:
            if st.button("▶️ Run Scenario", type="primary", use_container_width=True, 
                        disabled=st.session_state.execution_in_progress):
                self.run_demo_scenario(selected_scenario, scenarios[selected_scenario])
                st.rerun()
        
        # Approval modal (rendered if needed)
        if st.session_state.pending_approval:
            self.render_approval_modal()
        
        # Gate visualization
        st.markdown("---")
        self.render_gate_visualization(st.session_state.active_gate)
        
        # Execution results
        if st.session_state.execution_results:
            st.markdown("---")
            st.markdown("### Execution Results")
            for result in st.session_state.execution_results:
                decision = result.get("decision", "N/A")
                if decision == "DENY":
                    st.error(f"**{result['step']}**: DENIED - {result.get('reason', 'N/A')}")
                elif decision == "REQUIRE_APPROVAL":
                    st.warning(f"**{result['step']}**: Requires Approval")
                else:
                    st.success(f"**{result['step']}**: ALLOWED")
        
        # Two-column layout: Audit Log and Export
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_live_audit_log()
        
        with col2:
            st.markdown("### Export Evidence Pack")
            
            if st.session_state.enforcer.get_audit_log():
                evidence_pack = self.get_evidence_pack()
                evidence_json = json.dumps(evidence_pack, indent=2)
                
                st.download_button(
                    label="📥 Download Evidence Pack (JSON)",
                    data=evidence_json,
                    file_name=f"evidence_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.info("Run a scenario to generate evidence pack.")


def main():
    """Main entry point for the Streamlit application."""
    st.set_page_config(
        page_title="Constitutional Ontology Enforcement",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize UI
    ui = ConstitutionalEnforcementUI()
    ui.initialize_session_state()
    
    # Render main dashboard
    ui.render_dashboard()


if __name__ == "__main__":
    main()
