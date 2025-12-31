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
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple, Optional, List
import io

from constitutional_enforcement_interactive import ConstitutionalEnforcer, Decision

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

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
    
    def handle_policy_selection(self, policy_file: str):
        """Handle policy file selection and reload enforcer."""
        policy_path = os.path.join(os.path.dirname(__file__), policy_file)
        if os.path.exists(policy_path):
            try:
                st.session_state.enforcer = ConstitutionalEnforcer(policy_path)
                st.session_state.policy_file = policy_file
                st.session_state.policy_path = policy_path
                # Clear audit log when policy changes
                st.session_state.enforcer.audit_log = []
                st.session_state.gate_history = []
                st.session_state.evidence_cache = {}
                st.success(f"Policy loaded: {policy_file}")
                return True
            except Exception as e:
                st.error(f"Error loading policy: {str(e)}")
                return False
        else:
            st.error(f"Policy file not found: {policy_file}")
            return False
    
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
        
        if 'policy_file' not in st.session_state:
            st.session_state.policy_file = self.policy_path
        if 'policy_path' not in st.session_state:
            st.session_state.policy_path = self.policy_path
        if 'gate_history' not in st.session_state:
            st.session_state.gate_history = []  # Track gate activations
        if 'evidence_cache' not in st.session_state:
            st.session_state.evidence_cache = {}  # Cache EnforcementResults
        if 'approval_comment' not in st.session_state:
            st.session_state.approval_comment = ""
        if 'demo_results' not in st.session_state:
            st.session_state.demo_results = []
    
    def render_gate_visualization(self, active_gate: str = None):
        """Render visual representation of gates with active highlighting, flow diagram, and statistics."""
        st.markdown("### Gate Activation Status")
        
        # Get gate statistics from audit log
        enforcer = st.session_state.enforcer
        audit_log = enforcer.get_audit_log()
        gate_stats = {}
        gate_status = {}
        
        for entry in audit_log:
            gate = entry.get('gate', '')
            decision = entry.get('decision', '')
            if gate not in gate_stats:
                gate_stats[gate] = {'total': 0, 'allow': 0, 'deny': 0, 'approval': 0}
                gate_status[gate] = 'passed'
            gate_stats[gate]['total'] += 1
            if decision == 'ALLOW' or decision == 'ALLOW_WITH_CONTROLS':
                gate_stats[gate]['allow'] += 1
            elif decision == 'DENY' or decision == 'DENIED_BY_HUMAN':
                gate_stats[gate]['deny'] += 1
            elif decision in ['REQUIRE_APPROVAL', 'APPROVED']:
                gate_stats[gate]['approval'] += 1
        
        # Determine current gate status
        if active_gate:
            gate_status[active_gate] = 'active'
        if st.session_state.pending_approval:
            approval_gate = st.session_state.pending_approval.get('gate')
            if approval_gate:
                gate_status[approval_gate] = 'waiting'
        
        # Render flow diagram
        st.markdown("#### Gate Flow Sequence")
        flow_gates = ["U-I", "S-O", "S-I", "U-O"]
        flow_cols = st.columns(len(flow_gates))
        
        for idx, gate_id in enumerate(flow_gates):
            with flow_cols[idx]:
                gate_info = self.GATES.get(gate_id, {})
                status = gate_status.get(gate_id, 'inactive')
                stats = gate_stats.get(gate_id, {'total': 0, 'allow': 0, 'deny': 0, 'approval': 0})
                
                # Determine styling based on status
                if status == 'active':
                    bg_color = "#28a745"
                    text_color = "white"
                    border_color = "#20c997"
                    border_width = "3px"
                    pulse_animation = "animation: pulse 2s infinite;"
                elif status == 'waiting':
                    bg_color = "#ffc107"
                    text_color = "black"
                    border_color = "#ff9800"
                    border_width = "3px"
                    pulse_animation = ""
                elif status == 'passed':
                    bg_color = "#d4edda"
                    text_color = "#155724"
                    border_color = "#28a745"
                    border_width = "2px"
                    pulse_animation = ""
                else:
                    bg_color = "#f8f9fa"
                    text_color = "#6c757d"
                    border_color = "#dee2e6"
                    border_width = "1px"
                    pulse_animation = ""
                
                # Status badge
                if status == 'active':
                    status_badge = "🟢 Active"
                elif status == 'waiting':
                    status_badge = "⏸️ Waiting"
                elif stats['total'] > 0:
                    status_badge = "✅ Passed"
                else:
                    status_badge = "⚪ Inactive"
                
                st.markdown(
                    f'<div style="background-color: {bg_color}; color: {text_color}; padding: 12px; '
                    f'border-radius: 8px; margin: 5px 0; border: {border_width} solid {border_color}; {pulse_animation}">'
                    f'<strong>{gate_info.get("icon", "")} {gate_info.get("name", gate_id)}</strong><br>'
                    f'<small>{gate_info.get("direction", "")}</small><br>'
                    f'<small><strong>{status_badge}</strong></small><br>'
                    f'<small>Total: {stats["total"]} | ✅ {stats["allow"]} | ❌ {stats["deny"]} | ⚠️ {stats["approval"]}</small>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Add expander for gate details
                with st.expander(f"Details: {gate_info.get('name', gate_id)}"):
                    if stats['total'] > 0:
                        st.metric("Total Activations", stats['total'])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Allowed", stats['allow'], delta=None)
                        with col2:
                            st.metric("Denied", stats['deny'], delta=None)
                        with col3:
                            st.metric("Approvals", stats['approval'], delta=None)
                    else:
                        st.info("No activations yet")
        
        # Add CSS for pulse animation
        st.markdown("""
        <style>
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Group gates by domain (original view)
        st.markdown("#### All Gates by Domain")
        domains = {}
        for gate_id, gate_info in self.GATES.items():
            domain = gate_info["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append((gate_id, gate_info))
        
        cols = st.columns(len(domains))
        
        for idx, (domain, gates) in enumerate(domains.items()):
            with cols[idx]:
                st.markdown(f"**{domain}**")
                for gate_id, gate_info in gates:
                    status = gate_status.get(gate_id, 'inactive')
                    stats = gate_stats.get(gate_id, {'total': 0})
                    
                    if status == 'active':
                        bg_color = "#28a745"
                        text_color = "white"
                        border = "2px solid #20c997"
                    elif status == 'waiting':
                        bg_color = "#ffc107"
                        text_color = "black"
                        border = "2px solid #ff9800"
                    elif stats['total'] > 0:
                        bg_color = "#d4edda"
                        text_color = "#155724"
                        border = "1px solid #28a745"
                    else:
                        bg_color = "#f8f9fa"
                        text_color = "#6c757d"
                        border = "1px solid #dee2e6"
                    
                    st.markdown(
                        f'<div style="background-color: {bg_color}; color: {text_color}; padding: 8px; '
                        f'border-radius: 5px; margin: 3px 0; border: {border};">'
                        f'{gate_info["icon"]} {gate_info["name"]}<br>'
                        f'<small>{gate_info["direction"]} ({stats["total"]} activations)</small></div>',
                        unsafe_allow_html=True
                    )
    
    def render_approval_modal(self):
        """Render enhanced approval modal when action requires human approval."""
        if st.session_state.pending_approval:
            approval = st.session_state.pending_approval
            
            # Use container as modal (st.dialog may not be available in all versions)
            with st.container():
                st.markdown("---")
                st.warning("⚠️ **APPROVAL REQUIRED**")
                self._render_approval_content(approval)
    
    def _render_approval_content(self, approval: Dict[str, Any]):
        """Render the content of the approval modal."""
        gate_id = approval.get('gate', 'N/A')
        gate_info = self.GATES.get(gate_id, {})
        
        # Header with gate icon and name
        st.markdown(f"### {gate_info.get('icon', '⚠️')} Approval Required")
        st.markdown(f"**Gate:** {gate_info.get('name', gate_id)} ({gate_id})")
        
        # Action details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Action Details")
            st.markdown(f"**Action ID:** `{approval.get('action_id', 'N/A')}`")
            st.markdown(f"**Tool/Action:** `{approval.get('action', 'N/A')}`")
            
            if approval.get('details'):
                st.markdown("**Parameters:**")
                st.json(approval['details'])
            
            if approval.get('evidence'):
                with st.expander("View Evidence"):
                    st.json(approval['evidence'])
            
            if approval.get('controls'):
                st.markdown("**Controls Applied:**")
                for control in approval.get('controls', []):
                    st.markdown(f"- {control}")
            
            if approval.get('reason'):
                st.info(f"**Policy Reason:** {approval['reason']}")
        
        with col2:
            st.markdown("#### Decision")
            
            # Comment field
            comment = st.text_area(
                "Add comment (optional):",
                value=st.session_state.get('approval_comment', ''),
                key="approval_comment_input",
                height=100
            )
            st.session_state.approval_comment = comment
            
            # Approval history preview
            enforcer = st.session_state.enforcer
            audit_log = enforcer.get_audit_log()
            similar_approvals = [
                e for e in audit_log 
                if e.get('gate') == gate_id and e.get('action') == approval.get('action')
            ]
            
            if similar_approvals:
                with st.expander(f"Similar Past Approvals ({len(similar_approvals)})"):
                    for entry in similar_approvals[-5:]:  # Show last 5
                        st.markdown(f"**{entry.get('timestamp', 'N/A')}** - {entry.get('decision', 'N/A')}")
            
            # Action buttons
            col_approve, col_deny = st.columns(2)
            
            with col_approve:
                approve_btn = st.button(
                    "✅ Approve", 
                    key="approve_btn", 
                    type="primary", 
                    use_container_width=True
                )
            
            with col_deny:
                deny_btn = st.button(
                    "❌ Deny", 
                    key="deny_btn", 
                    type="secondary", 
                    use_container_width=True
                )
            
            if approve_btn:
                st.session_state.pending_approval = None
                st.session_state.approval_comment = ""
                self.continue_execution_after_approval(True, comment)
                st.rerun()
            
            if deny_btn:
                st.session_state.pending_approval = None
                deny_reason = comment if comment else "Denied via UI"
                st.session_state.approval_comment = ""
                self.continue_execution_after_approval(False, deny_reason)
                st.rerun()
    
    def render_live_audit_log(self):
        """Render enhanced live audit log with filtering, search, and expandable entries."""
        st.markdown("### Live Audit Log")
        
        enforcer = st.session_state.enforcer
        audit_log = enforcer.get_audit_log()
        
        if not audit_log:
            st.info("No audit log entries yet. Run a scenario to see enforcement activity.")
            return
        
        # Filtering controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Gate filter
            all_gates = ["All"] + list(self.GATES.keys())
            selected_gate = st.selectbox("Filter by Gate:", all_gates, key="audit_gate_filter")
        
        with col2:
            # Decision filter
            all_decisions = ["All", "ALLOW", "ALLOW_WITH_CONTROLS", "DENY", "DENIED_BY_HUMAN", "REQUIRE_APPROVAL", "APPROVED"]
            selected_decision = st.selectbox("Filter by Decision:", all_decisions, key="audit_decision_filter")
        
        with col3:
            # Time range filter
            time_range = st.selectbox("Time Range:", ["All", "Last Hour", "Last Day", "Last Week"], key="audit_time_filter")
        
        # Search
        search_query = st.text_input("Search (action, user_id, etc.):", key="audit_search", placeholder="Enter search term...")
        
        # Apply filters
        filtered_log = audit_log.copy()
        
        if selected_gate != "All":
            filtered_log = [e for e in filtered_log if e.get('gate') == selected_gate]
        
        if selected_decision != "All":
            filtered_log = [e for e in filtered_log if e.get('decision') == selected_decision]
        
        if search_query:
            search_lower = search_query.lower()
            filtered_log = [
                e for e in filtered_log
                if search_lower in str(e.get('action', '')).lower()
                or search_lower in str(e.get('user_id', '')).lower()
                or search_lower in str(e.get('gate', '')).lower()
            ]
        
        if time_range != "All":
            now = datetime.now(timezone.utc)
            if time_range == "Last Hour":
                cutoff = now.timestamp() - 3600
            elif time_range == "Last Day":
                cutoff = now.timestamp() - 86400
            elif time_range == "Last Week":
                cutoff = now.timestamp() - 604800
            
            filtered_log = [
                e for e in filtered_log
                if self._parse_timestamp(e.get('timestamp', '')) >= cutoff
            ]
        
        # Pagination
        entries_per_page = 50
        total_pages = (len(filtered_log) + entries_per_page - 1) // entries_per_page
        
        if 'audit_page' not in st.session_state:
            st.session_state.audit_page = 1
        
        if total_pages > 1:
            page = st.selectbox(f"Page (1-{total_pages}):", range(1, total_pages + 1), key="audit_page_select")
            st.session_state.audit_page = page
        else:
            st.session_state.audit_page = 1
        
        start_idx = (st.session_state.audit_page - 1) * entries_per_page
        end_idx = start_idx + entries_per_page
        page_log = filtered_log[start_idx:end_idx]
        
        # Display count
        st.caption(f"Showing {len(page_log)} of {len(filtered_log)} entries (Page {st.session_state.audit_page} of {total_pages})")
        
        # Create a scrollable container for the log
        log_container = st.container()
        
        with log_container:
            # Display entries in reverse chronological order (newest first)
            for entry in reversed(page_log):
                timestamp = entry.get('timestamp', 'N/A')
                gate = entry.get('gate', 'N/A')
                action = entry.get('action', 'N/A')
                decision = entry.get('decision', 'N/A')
                controls = entry.get('controls', [])
                user_id = entry.get('user_id', 'N/A')
                evidence = entry.get('evidence', {})
                
                # Color code by decision
                if decision in ['ALLOW', 'ALLOW_WITH_CONTROLS']:
                    decision_color = "#28a745"
                    decision_icon = "✅"
                elif decision in ['DENY', 'DENIED_BY_HUMAN']:
                    decision_color = "#dc3545"
                    decision_icon = "❌"
                elif decision in ['REQUIRE_APPROVAL', 'APPROVED']:
                    decision_color = "#ffc107"
                    decision_icon = "⚠️"
                else:
                    decision_color = "#6c757d"
                    decision_icon = "ℹ️"
                
                # Format entry with expander
                with st.expander(
                    f"{decision_icon} [{timestamp}] {gate} | {action} | {decision}",
                    expanded=False
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Gate:** {gate}")
                        st.markdown(f"**Action:** {action}")
                        st.markdown(f"**Decision:** <span style='color: {decision_color}'>{decision}</span>", unsafe_allow_html=True)
                        st.markdown(f"**User ID:** {user_id}")
                    
                    with col2:
                        st.markdown(f"**Timestamp:** {timestamp}")
                        st.markdown(f"**Controls Applied:** {', '.join(controls) if controls else 'None'}")
                    
                    if evidence:
                        st.markdown("**Evidence:**")
                        st.json(evidence)
                
                # Compact view (always visible)
                st.markdown(
                    f'<div style="background-color: #f8f9fa; padding: 8px; margin: 4px 0; '
                    f'border-left: 4px solid {decision_color}; border-radius: 3px;">'
                    f'<small><strong>{decision_icon} [{timestamp}]</strong> | '
                    f'<strong>{gate}</strong> | {action} | '
                    f'<span style="color: {decision_color}"><strong>{decision}</strong></span> | '
                    f'User: {user_id}</small><br>'
                    f'<small>Controls: {", ".join(controls) if controls else "None"}</small></div>',
                    unsafe_allow_html=True
                )
        
        # Export filtered log button
        if filtered_log:
            st.download_button(
                label="📥 Export Filtered Log (JSON)",
                data=json.dumps(filtered_log, indent=2),
                file_name=f"audit_log_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse ISO timestamp string to Unix timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except:
            return 0.0
    
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
                "reason": "Policy requires human approval for this action",
                "evidence": pre.evidence,
                "controls": pre.controls_applied
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
    
    def continue_execution_after_approval(self, approved: bool, comment: str = ""):
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
            deny_reason = comment if comment else "Denied via UI"
            enforcer.deny_approval(action_id, "ui_user", deny_reason)
            enforcer._log_audit("S-O", tool_name, "DENIED_BY_HUMAN", "ui_user", ["human_denial"], {"action_id": action_id, "comment": comment})
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
        enforcer._log_audit("S-O", tool_name, "APPROVED", "ui_user", ["human_approval"], {"action_id": action_id, "comment": comment})
        
        # Check if this is part of demo tests
        if state.get("demo_test"):
            # Continue demo tests
            demo_start_from = state.get("demo_start_from", 3)
            # Execute tool
            def simulate_tool(tool_name: str, params: dict):
                if tool_name == "sharepoint_read":
                    return {"source": "sharepoint", "path": params.get("path"), "content": "Draft policy template v3.2"}
                if tool_name == "occ_query":
                    return {"source": "occ_fdic_db", "query": params.get("q"), "content": "OCC interpretive letter excerpt..."}
                if tool_name == "write_draft":
                    return {"source": "draft_doc", "doc_id": "DOC-001", "status": "written"}
                if tool_name == "jira_create":
                    return {"source": "jira_create_task", "issue_id": "JIRA-101", "status": "created", "title": params.get("title")}
                return {"source": tool_name, "status": "ok"}
            
            raw_result = simulate_tool(tool_name, params)
            st.session_state.active_gate = "S-I"
            post = enforcer.post_tool_result(tool_name, raw_result, user_id)
            st.session_state.active_gate = None
            
            # Update demo result for test 2
            if st.session_state.get('demo_results'):
                for result in st.session_state.demo_results:
                    if result.get("test", "").startswith("2."):
                        result["status"] = "complete"
                        result["decision"] = post.decision.value
                        break
            
            # Continue with remaining demo tests
            self.run_demo_tests(start_from=demo_start_from)
            st.session_state.execution_in_progress = False
            
            del st.session_state.execution_state
            st.rerun()
            return
        
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
        if 'remaining_tool_calls' in st.session_state and st.session_state.remaining_tool_calls:
            self._process_remaining_tool_calls()
        elif 'pending_response' in st.session_state and st.session_state.pending_response is not None:
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
        if 'pending_response' in st.session_state and st.session_state.pending_response is not None:
            self._process_response()
        else:
            st.session_state.execution_in_progress = False
    
    def _process_response(self):
        """Process response output."""
        if 'pending_response' not in st.session_state or st.session_state.pending_response is None:
            st.session_state.execution_in_progress = False
            return
        
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
        if 'pending_response' in st.session_state:
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
    
    def get_evidence_pack(self, time_range: Tuple[Optional[datetime], Optional[datetime]] = None, include_evidence: bool = True) -> Dict[str, Any]:
        """Generate evidence pack for export."""
        enforcer = st.session_state.enforcer
        audit_log = enforcer.get_audit_log()
        
        # Filter by time range if provided
        if time_range and time_range[0] and time_range[1]:
            start_time = time_range[0]
            end_time = time_range[1]
            audit_log = [
                e for e in audit_log
                if start_time <= self._parse_datetime(e.get('timestamp', '')) <= end_time
            ]
        
        # Build evidence pack
        evidence = {
            "export_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "policy_file": st.session_state.get('policy_file', self.policy_path),
            "policy_path": st.session_state.get('policy_path', self.policy_path),
            "session_audit_log": audit_log,
            "execution_results": st.session_state.execution_results,
            "pending_approvals": enforcer.pending_approvals,
            "gate_sequence": [
                {"gate": entry.get('gate'), "timestamp": entry.get('timestamp'), 
                 "decision": entry.get('decision'), "action": entry.get('action')}
                for entry in audit_log
            ],
            "include_evidence": include_evidence
        }
        
        # Include full evidence if requested
        if include_evidence:
            evidence["evidence_cache"] = st.session_state.get('evidence_cache', {})
            evidence["gate_history"] = st.session_state.get('gate_history', [])
        
        # Load policy config
        try:
            with open(st.session_state.get('policy_path', self.policy_path), 'r') as f:
                evidence["policy_config"] = json.load(f)
        except:
            evidence["policy_config"] = None
        
        return evidence
    
    def _parse_datetime(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp string to datetime object."""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.now(timezone.utc)
    
    def export_evidence_pack_pdf(self, evidence_pack: Dict[str, Any]) -> bytes:
        """Generate PDF evidence pack using reportlab."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is not installed. Install it with: pip install reportlab")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
        )
        
        # Cover page
        story.append(Paragraph("Constitutional Enforcement Evidence Pack", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Export metadata
        story.append(Paragraph(f"<b>Export Timestamp:</b> {evidence_pack.get('export_timestamp', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Policy File:</b> {evidence_pack.get('policy_file', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive summary
        story.append(Paragraph("<b>Executive Summary</b>", styles['Heading2']))
        audit_log = evidence_pack.get('session_audit_log', [])
        total_decisions = len(audit_log)
        allow_count = len([e for e in audit_log if e.get('decision') in ['ALLOW', 'ALLOW_WITH_CONTROLS']])
        deny_count = len([e for e in audit_log if e.get('decision') in ['DENY', 'DENIED_BY_HUMAN']])
        approval_count = len([e for e in audit_log if e.get('decision') in ['REQUIRE_APPROVAL', 'APPROVED']])
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Decisions', str(total_decisions)],
            ['Allowed', str(allow_count)],
            ['Denied', str(deny_count)],
            ['Approvals Required', str(approval_count)],
            ['Approval Rate', f"{(allow_count/total_decisions*100):.1f}%" if total_decisions > 0 else "0%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        story.append(summary_table)
        story.append(PageBreak())
        
        # Gate activity timeline
        story.append(Paragraph("<b>Gate Activity Timeline</b>", styles['Heading2']))
        gate_sequence = evidence_pack.get('gate_sequence', [])
        if gate_sequence:
            timeline_data = [['Timestamp', 'Gate', 'Action', 'Decision']]
            for entry in gate_sequence[:50]:  # Limit to first 50 for PDF
                timeline_data.append([
                    entry.get('timestamp', 'N/A')[:19],  # Truncate timestamp
                    entry.get('gate', 'N/A'),
                    entry.get('action', 'N/A')[:30],  # Truncate long actions
                    entry.get('decision', 'N/A')
                ])
            
            timeline_table = Table(timeline_data, colWidths=[1.5*inch, 0.8*inch, 2*inch, 1.2*inch])
            timeline_table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            story.append(timeline_table)
        else:
            story.append(Paragraph("No gate activity recorded.", styles['Normal']))
        
        story.append(PageBreak())
        
        # Detailed audit log
        story.append(Paragraph("<b>Detailed Audit Log</b>", styles['Heading2']))
        for idx, entry in enumerate(audit_log[:100]):  # Limit to first 100 entries
            story.append(Paragraph(f"<b>Entry {idx + 1}</b>", styles['Heading3']))
            story.append(Paragraph(f"Timestamp: {entry.get('timestamp', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Gate: {entry.get('gate', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Action: {entry.get('action', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Decision: {entry.get('decision', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"User ID: {entry.get('user_id', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Controls: {', '.join(entry.get('controls', []))}", styles['Normal']))
            
            if entry.get('evidence') and evidence_pack.get('include_evidence', True):
                story.append(Paragraph("Evidence:", styles['Normal']))
                evidence_str = json.dumps(entry.get('evidence', {}), indent=2)
                story.append(Paragraph(f"<font face='Courier' size='8'>{evidence_str}</font>", styles['Normal']))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Policy configuration summary
        if evidence_pack.get('policy_config'):
            story.append(PageBreak())
            story.append(Paragraph("<b>Policy Configuration Summary</b>", styles['Heading2']))
            policy = evidence_pack['policy_config']
            story.append(Paragraph(f"Policy ID: {policy.get('policy_id', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Version: {policy.get('policy_version', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Description: {policy.get('description', 'N/A')}", styles['Normal']))
            
            # Dials summary
            if policy.get('dials'):
                story.append(Paragraph("<b>Dials Configuration:</b>", styles['Heading3']))
                for dial_name, dial_config in policy.get('dials', {}).items():
                    story.append(Paragraph(f"{dial_name}: {dial_config.get('label', 'N/A')} (Level {dial_config.get('level', 'N/A')})", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def run_demo_tests(self, start_from: int = 1):
        """Run the demo tests from constitutional_enforcement_interactive.py."""
        enforcer = st.session_state.enforcer
        user_id = "analyst_123"
        results = st.session_state.get('demo_results', [])
        
        # Simulate tool function (same as in the script)
        def simulate_tool(tool_name: str, params: dict):
            if tool_name == "sharepoint_read":
                return {"source": "sharepoint", "path": params.get("path"), "content": "Draft policy template v3.2"}
            if tool_name == "occ_query":
                return {"source": "occ_fdic_db", "query": params.get("q"), "content": "OCC interpretive letter excerpt..."}
            if tool_name == "write_draft":
                return {"source": "draft_doc", "doc_id": "DOC-001", "status": "written"}
            if tool_name == "jira_create":
                return {"source": "jira_create_task", "issue_id": "JIRA-101", "status": "created", "title": params.get("title")}
            return {"source": tool_name, "status": "ok"}
        
        # Demo 1: Allowed tool call (SharePoint read)
        if start_from <= 1:
            results.append({"test": "1. Testing S-O: SharePoint Read (should ALLOW)", "status": "running"})
            st.session_state.active_gate = "S-O"
            result = enforcer.pre_tool_call("sharepoint_read", {"path": "/policies/draft"}, user_id)
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["controls"] = result.controls_applied
        
        # Demo 2: Tool call requiring approval (Jira create)
        if start_from <= 2:
            if len(results) < 2:
                results.append({"test": "2. Testing S-O: Jira Create (should REQUIRE_APPROVAL)", "status": "running"})
            st.session_state.active_gate = "S-O"
            pre = enforcer.pre_tool_call("jira_create", {"title": "Review Q4 policy", "project": "COMP"}, user_id)
            
            if pre.decision == Decision.REQUIRE_APPROVAL:
                # Set up approval request
                action_id = str(uuid.uuid4())[:8]
                enforcer.request_approval(action_id, "S-O", "jira_create", user_id, {"params": {"title": "Review Q4 policy", "project": "COMP"}})
                enforcer._log_audit("S-O", "jira_create", "REQUIRE_APPROVAL", user_id, pre.controls_applied, pre.evidence)
                
                st.session_state.pending_approval = {
                    "action_id": action_id,
                    "gate": "S-O",
                    "action": "jira_create",
                    "details": {"title": "Review Q4 policy", "project": "COMP"},
                    "reason": "Policy requires human approval for this action",
                    "evidence": pre.evidence,
                    "controls": pre.controls_applied
                }
                
                st.session_state.execution_state = {
                    "step": "waiting_approval",
                    "tool_name": "jira_create",
                    "params": {"title": "Review Q4 policy", "project": "COMP"},
                    "user_id": user_id,
                    "action_id": action_id,
                    "demo_test": 2,
                    "demo_start_from": 3
                }
                
                if len(results) >= 2:
                    results[1]["status"] = "waiting_approval"
                    results[1]["decision"] = "REQUIRE_APPROVAL"
                else:
                    results[-1]["status"] = "waiting_approval"
                    results[-1]["decision"] = "REQUIRE_APPROVAL"
                st.session_state.active_gate = None
                st.session_state.demo_results = results
                return results  # Pause for approval
            
            # If approved or allowed, continue
            tool_result = simulate_tool("jira_create", {"title": "Review Q4 policy", "project": "COMP"})
            st.session_state.active_gate = "S-I"
            post = enforcer.post_tool_result("jira_create", tool_result, user_id)
            st.session_state.active_gate = None
            if len(results) >= 2:
                results[1]["status"] = "complete"
                results[1]["decision"] = post.decision.value
            else:
                results[-1]["status"] = "complete"
                results[-1]["decision"] = post.decision.value
        
        # Demo 3: Email Send (should DENY)
        if start_from <= 3:
            results.append({"test": "3. Testing S-O: Email Send (should DENY - not in allowlist)", "status": "running"})
            st.session_state.active_gate = "S-O"
            result = enforcer.pre_tool_call("email_send", {"to": "external@other.com"}, user_id)
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["reason"] = result.denial_reason
        
        # Demo 4: Response with regulatory claim but no citation
        if start_from <= 4:
            results.append({"test": "4. Testing U-O: Response with regulatory claim, no citation (should DENY)", "status": "running"})
            st.session_state.active_gate = "U-O"
            result = enforcer.pre_response(
                "OCC requires all banks to maintain capital reserves of 8%.",
                citations=[],
                user_id=user_id
            )
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["reason"] = result.denial_reason
        
        # Demo 5: Response with citation (should pass)
        if start_from <= 5:
            results.append({"test": "5. Testing U-O: Response with citation (should ALLOW)", "status": "running"})
            st.session_state.active_gate = "U-O"
            result = enforcer.pre_response(
                "OCC requires all banks to maintain capital reserves of 8%.",
                citations=[{"source": "OCC Bulletin 2023-01", "url": "https://occ.gov/..."}],
                user_id=user_id
            )
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["controls"] = result.controls_applied
        
        # Demo 6: Inter-agent communication (should DENY)
        if start_from <= 6:
            results.append({"test": "6. Testing A-O: Send to another agent (should DENY)", "status": "running"})
            st.session_state.active_gate = "A-O"
            result = enforcer.agent_outbound("research_agent", {"query": "find precedents"}, user_id)
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["reason"] = result.denial_reason
        
        # Demo 7: Memory write of allowed preference
        if start_from <= 7:
            results.append({"test": "7. Testing M-O: Store citation format (should ALLOW)", "status": "running"})
            st.session_state.active_gate = "M-O"
            result = enforcer.memory_write("citation_format", "APA 7th edition", user_id)
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["controls"] = result.controls_applied
        
        # Demo 8: Memory write of regulated data
        if start_from <= 8:
            results.append({"test": "8. Testing M-O: Store customer SSN (should DENY)", "status": "running"})
            st.session_state.active_gate = "M-O"
            result = enforcer.memory_write("customer_info", "SSN: 123-45-6789", user_id)
            st.session_state.active_gate = None
            results[-1]["status"] = "complete"
            results[-1]["decision"] = result.decision.value
            results[-1]["reason"] = result.denial_reason
        
        st.session_state.demo_results = results
        return results
    
    def render_dashboard(self):
        """Render the main demo dashboard."""
        st.header("Constitutional Ontology Enforcement Dashboard")
        st.markdown("---")
        
        # Run demo tests button
        st.markdown("### Run Demo Tests")
        st.caption("Run the demo tests from constitutional_enforcement_interactive.py with the selected policy")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Current Policy:** {st.session_state.get('policy_file', 'N/A')}")
        with col2:
            if st.button("▶️ Run Demo Tests", type="primary", use_container_width=True,
                        disabled=st.session_state.get('execution_in_progress', False) or st.session_state.get('pending_approval') is not None):
                st.session_state.execution_in_progress = True
                st.session_state.demo_results = []
                st.session_state.demo_results = self.run_demo_tests()
                if not st.session_state.pending_approval:
                    st.session_state.execution_in_progress = False
                st.rerun()
        
        # Approval modal (rendered if needed)
        if st.session_state.pending_approval:
            self.render_approval_modal()
        
        # Gate visualization
        st.markdown("---")
        self.render_gate_visualization(st.session_state.active_gate)
        
        # Demo test results
        if st.session_state.get('demo_results'):
            st.markdown("---")
            st.markdown("### Demo Test Results")
            for result in st.session_state.demo_results:
                test_name = result.get("test", "Unknown test")
                status = result.get("status", "unknown")
                decision = result.get("decision", "N/A")
                
                if status == "waiting_approval":
                    st.warning(f"**{test_name}** - ⏸️ Waiting for approval")
                elif decision in ["allow", "allow_with_controls"]:
                    st.success(f"**{test_name}** - ✅ {decision.upper()}")
                    if result.get("controls"):
                        st.caption(f"Controls: {', '.join(result['controls'])}")
                elif decision == "deny":
                    st.error(f"**{test_name}** - ❌ DENY")
                    if result.get("reason"):
                        st.caption(f"Reason: {result['reason']}")
                elif decision == "require_approval":
                    st.warning(f"**{test_name}** - ⚠️ REQUIRES APPROVAL")
                else:
                    st.info(f"**{test_name}** - {decision}")
        
        # Two-column layout: Audit Log and Export
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_live_audit_log()
        
        with col2:
            st.markdown("### Export Evidence Pack")
            
            if st.session_state.enforcer.get_audit_log():
                # Export format selector
                export_format = st.radio(
                    "Export Format:",
                    ["JSON", "PDF"],
                    key="export_format",
                    horizontal=True
                )
                
                # Time range picker
                time_range_option = st.selectbox(
                    "Time Range:",
                    ["All Time", "Last Hour", "Last Day", "Last Week"],
                    key="export_time_range"
                )
                
                # Include evidence checkbox
                include_evidence = st.checkbox(
                    "Include Full Evidence",
                    value=True,
                    key="export_include_evidence"
                )
                
                # Calculate time range
                time_range = None
                if time_range_option != "All Time":
                    now = datetime.now(timezone.utc)
                    if time_range_option == "Last Hour":
                        time_range = (now - timedelta(hours=1), now)
                    elif time_range_option == "Last Day":
                        time_range = (now - timedelta(days=1), now)
                    elif time_range_option == "Last Week":
                        time_range = (now - timedelta(weeks=1), now)
                
                # Preview
                evidence_pack = self.get_evidence_pack(time_range=time_range, include_evidence=include_evidence)
                audit_count = len(evidence_pack.get('session_audit_log', []))
                st.caption(f"Preview: {audit_count} audit log entries will be included")
                
                # Export buttons
                if export_format == "JSON":
                    evidence_json = json.dumps(evidence_pack, indent=2)
                    st.download_button(
                        label="📥 Download Evidence Pack (JSON)",
                        data=evidence_json,
                        file_name=f"evidence_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:  # PDF
                    if REPORTLAB_AVAILABLE:
                        try:
                            pdf_data = self.export_evidence_pack_pdf(evidence_pack)
                            st.download_button(
                                label="📥 Download Evidence Pack (PDF)",
                                data=pdf_data,
                                file_name=f"evidence_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
                    else:
                        st.warning("PDF export requires reportlab. Install with: pip install reportlab")
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
    
    # Sidebar with policy selector
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Policy file selector
        policy_files = [
            "policy_bank_compliance_v1.json",
            "policy_bank_compliance_v2_restrictive.json",
            "policy_bank_compliance_v2_permissive.json"
        ]
        
        # Check which files exist
        existing_policies = []
        for policy_file in policy_files:
            policy_path = os.path.join(os.path.dirname(__file__), policy_file)
            if os.path.exists(policy_path):
                existing_policies.append(policy_file)
        
        if not existing_policies:
            st.error("No policy files found!")
            st.stop()
        
        # Get current policy or default
        current_policy = st.session_state.get('policy_file', existing_policies[0])
        if current_policy not in existing_policies:
            current_policy = existing_policies[0]
        
        selected_policy = st.selectbox(
            "Select Policy File:",
            existing_policies,
            index=existing_policies.index(current_policy) if current_policy in existing_policies else 0,
            key="policy_selector"
        )
        
        # Load policy if changed
        if selected_policy != current_policy:
            ui = ConstitutionalEnforcementUI(selected_policy)
            if ui.handle_policy_selection(selected_policy):
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        if 'enforcer' in st.session_state:
            audit_log = st.session_state.enforcer.get_audit_log()
            st.metric("Total Decisions", len(audit_log))
            
            if audit_log:
                allow_count = len([e for e in audit_log if e.get('decision') in ['ALLOW', 'ALLOW_WITH_CONTROLS']])
                deny_count = len([e for e in audit_log if e.get('decision') in ['DENY', 'DENIED_BY_HUMAN']])
                st.metric("Allowed", allow_count)
                st.metric("Denied", deny_count)
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("Constitutional Ontology Enforcement System")
        st.caption("8-Gate Policy Interceptor for AI Agent Governance")
    
    # Initialize UI
    ui = ConstitutionalEnforcementUI(selected_policy)
    ui.initialize_session_state()
    
    # Render main dashboard
    ui.render_dashboard()


if __name__ == "__main__":
    main()
