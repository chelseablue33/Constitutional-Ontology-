"""
Soft Ontology Page - Create and manage organization-specific documentation integration
"""

import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soft_ontology_manager import SoftOntologyManager


# Page configuration
st.set_page_config(
    page_title="Soft Ontology",
    page_icon="📄",
    layout="wide"
)

# Initialize session state for soft ontology manager
if "soft_ontology_manager" not in st.session_state:
    st.session_state.soft_ontology_manager = SoftOntologyManager()

manager = st.session_state.soft_ontology_manager

st.title("📄 Soft Ontology Management")
st.caption("Upload organization-specific documents (SOPs, marketing docs) to supplement hard ontology baseline")

st.markdown("---")

# Main content in two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Upload Documents")
    st.caption("Upload PDF, DOCX, TXT, or Markdown files containing organizational policies")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt", "md"],
        help="Upload documents containing organizational policies, SOPs, or compliance requirements"
    )
    
    if uploaded_file is not None:
        # Read file content
        file_content = uploaded_file.read()
        file_type = uploaded_file.type
        file_name = uploaded_file.name
        
        if st.button("Add Document", type="primary"):
            document = manager.add_document(file_name, file_content, file_type)
            st.success(f"Document '{file_name}' uploaded successfully!")
            st.rerun()
    
    st.markdown("---")
    
    # Document list
    st.markdown("### Uploaded Documents")
    
    if not manager.documents:
        st.info("No documents uploaded yet. Upload a document to get started.")
    else:
        for doc in manager.documents:
            with st.container():
                col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])
                
                with col_doc1:
                    st.write(f"**{doc['name']}**")
                    st.caption(f"Uploaded: {doc['upload_date'][:10]} | Size: {doc['size']:,} bytes | Status: {doc['status']}")
                
                with col_doc2:
                    if st.button("Extract Text", key=f"extract_{doc['id']}"):
                        extracted = manager.extract_text(doc['id'])
                        if extracted:
                            st.success("Text extracted!")
                            st.rerun()
                        else:
                            st.error("Failed to extract text")
                
                with col_doc3:
                    if st.button("Remove", key=f"remove_{doc['id']}"):
                        manager.remove_document(doc['id'])
                        st.success("Document removed")
                        st.rerun()
                
                # Show extracted text preview
                if doc.get("extracted_text"):
                    with st.expander(f"Preview: {doc['name']}", expanded=False):
                        text_preview = doc['extracted_text'][:500]  # First 500 chars
                        st.text_area("Extracted Text", text_preview, height=150, disabled=True, key=f"preview_{doc['id']}")
                        if len(doc['extracted_text']) > 500:
                            st.caption(f"... ({len(doc['extracted_text']) - 500} more characters)")
                
                st.markdown("---")

with col2:
    st.markdown("### Extracted Rules")
    st.caption("Policy-relevant information extracted from documents")
    
    # OpenAI API key status - improved detection
    api_key = None
    use_openai = True  # Default to OpenAI (heavily prioritize)
    
    try:
        # Try multiple methods to get API key
        if hasattr(st, 'secrets') and st.secrets:
            # Method 1: [openai].api_key
            try:
                if "openai" in st.secrets:
                    api_key = st.secrets["openai"].get("api_key")
            except (KeyError, AttributeError, TypeError):
                pass
            
            # Method 2: Top-level OPENAI_API_KEY
            if not api_key:
                try:
                    api_key = st.secrets.get("OPENAI_API_KEY")
                except (KeyError, AttributeError, TypeError):
                    pass
    except Exception:
        pass
    
    # Check environment variable as fallback
    if not api_key:
        import os
        api_key = os.environ.get("OPENAI_API_KEY")
    
    # Validate API key
    if api_key and not (api_key.startswith("sk-your-") or (api_key.startswith("sk-proj-") and len(api_key) < 50)):
        st.success("✓ OpenAI API key configured - Using GPT-4o for intelligent extraction")
        use_openai = st.checkbox("Use OpenAI for rule extraction", value=True, help="Uses GPT-4o for intelligent rule extraction. Uncheck to use simple keyword matching.", key="use_openai_checkbox")
    else:
        st.warning("⚠ OpenAI API key not found. Will use keyword-based extraction.")
        st.info("""
        **To enable OpenAI extraction:**
        1. Create `.streamlit/secrets.toml` file
        2. Add your API key:
        ```toml
        [openai]
        api_key = "sk-your-actual-key-here"
        ```
        3. Restart the Streamlit app
        """)
        use_openai = st.checkbox("Use OpenAI for rule extraction", value=False, help="OpenAI API key not configured. Will use keyword matching.", key="use_openai_checkbox")
    
    # Extract rules from all documents
    if st.button("Parse All Documents for Rules", type="primary"):
        if not manager.documents:
            st.warning("No documents uploaded. Please upload and extract text from documents first.")
        else:
            docs_with_text = [doc for doc in manager.documents if doc.get("extracted_text")]
            if not docs_with_text:
                st.warning("No documents have extracted text. Please extract text from documents first.")
            else:
                method_name = "OpenAI GPT-4o" if use_openai else "keyword matching"
                with st.spinner(f"Parsing {len(docs_with_text)} document(s) using {method_name}..."):
                    total_rules = 0
                    errors = []
                    openai_failures = []
                    
                    for doc in docs_with_text:
                        try:
                            rules = manager.parse_policy_rules(doc['id'], use_openai=use_openai)
                            rule_count = len(rules)
                            total_rules += rule_count
                            
                            if use_openai and rule_count == 0:
                                # OpenAI was requested but returned no rules - might have failed
                                openai_failures.append(doc['name'])
                        except Exception as e:
                            error_msg = f"Error parsing {doc['name']}: {str(e)}"
                            errors.append(error_msg)
                            st.error(error_msg)
                    
                    # Show results
                    if errors:
                        st.error(f"**Errors occurred:** {len(errors)} document(s) had errors")
                        for error in errors:
                            st.error(f"  • {error}")
                    
                    if openai_failures and use_openai:
                        st.warning(f"**OpenAI returned no rules for:** {len(openai_failures)} document(s)")
                        st.info("This might indicate: API key issues, rate limits, or documents without policy content. Falling back to keyword matching for these documents.")
                    
                    if total_rules > 0:
                        st.success(f"✅ Extracted **{total_rules} policy rule(s)** using {method_name}!")
                        st.rerun()
                    else:
                        if use_openai:
                            st.warning("OpenAI extraction returned no rules. This could mean:")
                            st.info("""
                            - Documents don't contain policy-related content
                            - API key is invalid or expired
                            - Rate limit reached
                            - Network/API error
                            
                            Try unchecking 'Use OpenAI' to use keyword-based extraction as a fallback.
                            """)
                        else:
                            st.info("No policy rules found using keyword matching. Try enabling OpenAI extraction for better results, or ensure documents contain policy-related keywords like 'retention', 'policy', 'compliance', etc.")
    
    if manager.extracted_rules:
        st.write(f"**{len(manager.extracted_rules)} rule(s) extracted**")
        
        for rule in manager.extracted_rules:
            with st.container():
                col_rule1, col_rule2 = st.columns([3, 1])
                
                with col_rule1:
                    st.markdown(f"**Rule {rule['id']}**")
                    source_name = rule.get('source_document_name') or next((d['name'] for d in manager.documents if d['id'] == rule['source_document']), 'Unknown')
                    extraction_method = rule.get('extraction_method', 'keyword_matching')
                    method_badge = "🤖 OpenAI" if extraction_method == "openai_gpt4o" else "🔍 Keywords"
                    st.caption(f"Source: {source_name} | {method_badge}")
                    
                    st.write("**Rule Text:**", rule['text'])
                    
                    if rule.get('rule_type'):
                        st.caption(f"**Type:** {rule['rule_type'].replace('_', ' ').title()}")
                    
                    if rule.get('key_requirements'):
                        with st.expander("Key Requirements", expanded=False):
                            for req in rule['key_requirements']:
                                st.write(f"• {req}")
                    
                    if rule.get('time_periods'):
                        st.caption(f"**Time Periods:** {', '.join(rule['time_periods'])}")
                    
                    if rule.get('context'):
                        st.caption(f"**Context:** {rule['context']}")
                
                with col_rule2:
                    confidence = rule.get('confidence', 0.5)
                    st.metric("Confidence", f"{confidence:.0%}")
                    if confidence >= 0.8:
                        st.success("High")
                    elif confidence >= 0.6:
                        st.info("Medium")
                    else:
                        st.warning("Low")
                
                st.markdown("---")
    else:
        st.info("No rules extracted yet. Upload documents and click 'Parse All Documents for Rules'.")
    
    st.markdown("---")
    
    # Conflict Resolution
    st.markdown("### Policy Conflict Resolution")
    st.caption("Resolve conflicts between hard ontology baseline and soft ontology rules")
    
    # Mock conflict detection - in production, this would check against actual hard ontology
    if st.button("Detect Conflicts"):
        st.info("Conflict detection requires integration with hard ontology policy. This feature will be enhanced in future updates.")
    
    if manager.conflict_resolutions:
        st.write(f"**{len(manager.conflict_resolutions)} conflict resolution(s)**")
        for resolution in manager.conflict_resolutions:
            with st.container():
                st.markdown(f"**Resolution {resolution['id']}**")
                st.write(f"Decision: {resolution.get('resolution', 'Pending')}")
                if resolution.get('resolution_notes'):
                    st.caption(f"Notes: {resolution['resolution_notes']}")
                st.markdown("---")
    
    st.markdown("---")
    
    # Integration Status
    st.markdown("### Integration Status")
    active_rules = manager.get_active_rules()
    st.write(f"**Active Rules:** {len(active_rules)}")
    st.write(f"**Total Documents:** {len(manager.documents)}")
    st.write(f"**Extracted Rules:** {len(manager.extracted_rules)}")
    st.write(f"**Resolved Conflicts:** {len(manager.conflict_resolutions)}")
    
    if len(active_rules) > 0:
        st.success("✓ Soft ontology is active and supplementing hard ontology baseline")
    else:
        st.info("Soft ontology is not yet active. Upload documents and extract rules to enable.")

# Export/Import section at bottom
st.markdown("---")
st.markdown("### Export/Import")
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    if st.button("Export Soft Ontology State"):
        state = manager.to_dict()
        import json
        state_json = json.dumps(state, indent=2)
        st.download_button(
            label="Download JSON",
            data=state_json,
            file_name=f"soft_ontology_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

with col_exp2:
    st.info("Import functionality coming soon")
