"""
Soft Ontology Manager - Handles organization-specific documentation integration
Manages document uploads, text extraction, and policy conflict resolution
"""

import io
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import streamlit as st
from openai import OpenAI


class SoftOntologyManager:
    """Manages soft ontology documents and their integration with hard ontology baseline"""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.extracted_rules: List[Dict[str, Any]] = []
        self.conflict_resolutions: List[Dict[str, Any]] = []
    
    def add_document(self, file_name: str, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Add a document to the soft ontology collection"""
        document = {
            "id": f"doc_{len(self.documents)}_{datetime.utcnow().timestamp()}",
            "name": file_name,
            "type": file_type,
            "upload_date": datetime.utcnow().isoformat() + "Z",
            "size": len(file_content),
            "content": file_content,
            "extracted_text": None,
            "status": "uploaded"
        }
        self.documents.append(document)
        return document
    
    def remove_document(self, document_id: str) -> bool:
        """Remove a document from the collection"""
        initial_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc["id"] != document_id]
        return len(self.documents) < initial_count
    
    def extract_text(self, document_id: str) -> Optional[str]:
        """Extract text from a document based on its type"""
        document = next((doc for doc in self.documents if doc["id"] == document_id), None)
        if not document:
            return None
        
        file_type = document["type"].lower()
        content = document["content"]
        
        try:
            if file_type == "text/plain" or file_type.endswith(".txt"):
                text = content.decode('utf-8')
            elif file_type == "application/pdf" or file_type.endswith(".pdf"):
                # Basic PDF text extraction - in production, use PyPDF2 or pdfplumber
                text = f"[PDF content from {document['name']} - PDF parsing not fully implemented]"
            elif file_type.endswith(".docx") or "wordprocessingml" in file_type:
                # Basic DOCX extraction - in production, use python-docx
                text = f"[DOCX content from {document['name']} - DOCX parsing not fully implemented]"
            elif file_type.endswith(".md") or "markdown" in file_type:
                text = content.decode('utf-8')
            else:
                text = f"[Unsupported file type: {file_type}]"
            
            document["extracted_text"] = text
            document["status"] = "extracted"
            return text
        except Exception as e:
            document["status"] = f"error: {str(e)}"
            return None
    
    def _get_openai_client(self) -> Optional[OpenAI]:
        """Get OpenAI client using Streamlit secrets"""
        try:
            # Try to get API key from secrets - multiple fallback methods
            api_key = None
            
            # Method 1: Try [openai].api_key
            try:
                if hasattr(st, 'secrets') and st.secrets:
                    if "openai" in st.secrets:
                        api_key = st.secrets["openai"].get("api_key")
            except (AttributeError, KeyError, TypeError):
                pass
            
            # Method 2: Try top-level OPENAI_API_KEY
            if not api_key:
                try:
                    if hasattr(st, 'secrets') and st.secrets:
                        api_key = st.secrets.get("OPENAI_API_KEY")
                except (AttributeError, KeyError, TypeError):
                    pass
            
            # Method 3: Try environment variable as last resort
            if not api_key:
                import os
                api_key = os.environ.get("OPENAI_API_KEY")
            
            if not api_key or api_key.startswith("sk-your-") or api_key.startswith("sk-proj-") and len(api_key) < 50:
                # Invalid or placeholder key
                return None
            
            return OpenAI(api_key=api_key)
        except Exception as e:
            # Log error but don't raise - return None to trigger fallback
            return None
    
    def parse_policy_rules(self, document_id: str, use_openai: bool = True) -> List[Dict[str, Any]]:
        """
        Parse policy-relevant information from extracted text using OpenAI.
        Falls back to simple keyword matching if OpenAI is unavailable.
        """
        document = next((doc for doc in self.documents if doc["id"] == document_id), None)
        if not document or not document.get("extracted_text"):
            return []
        
        text = document["extracted_text"]
        document_name = document.get("name", "Unknown")
        
        # Heavily prioritize OpenAI - try it first if enabled
        if use_openai:
            rules = self._parse_with_openai(text, document_id, document_name)
            if rules and len(rules) > 0:
                # Store extracted rules
                for rule in rules:
                    # Check if rule already exists (by text content to avoid duplicates)
                    existing_rule = next(
                        (r for r in self.extracted_rules if r.get("text") == rule.get("text") and r.get("source_document") == document_id),
                        None
                    )
                    if not existing_rule:
                        self.extracted_rules.append(rule)
                return rules
            # If OpenAI returned empty but was requested, still try keywords as fallback
            # but log that OpenAI was attempted
        
        # Fallback to simple keyword-based extraction
        return self._parse_with_keywords(text, document_id)
    
    def _parse_with_openai(self, text: str, document_id: str, document_name: str) -> List[Dict[str, Any]]:
        """Parse policy rules using OpenAI with structured output"""
        client = self._get_openai_client()
        if not client:
            # Return empty list to trigger fallback
            return []
        
        # Define the JSON schema for structured output
        schema = {
            "type": "object",
            "properties": {
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "rule_id": {
                                "type": "string",
                                "description": "Unique identifier for the rule (e.g., 'RETENTION_001')"
                            },
                            "rule_text": {
                                "type": "string",
                                "description": "The exact text or paraphrased statement of the policy rule"
                            },
                            "rule_type": {
                                "type": "string",
                                "enum": ["data_retention", "access_control", "compliance", "security", "privacy", "operational", "other"],
                                "description": "Category of the policy rule"
                            },
                            "key_requirements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific requirements or constraints extracted from the rule"
                            },
                            "time_periods": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Any time periods mentioned (e.g., '5 years', '30 days')"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Confidence score for rule extraction (0.0 to 1.0)"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context or scope for the rule"
                            }
                        },
                        "required": ["rule_id", "rule_text", "rule_type", "confidence"]
                    }
                }
            },
            "required": ["rules"]
        }
        
        # Truncate text if too long (keep last 15000 chars to preserve context)
        text_to_analyze = text if len(text) <= 15000 else text[-15000:]
        
        prompt = f"""Analyze the following organizational policy document and extract all policy rules, requirements, and compliance statements.

Document Name: {document_name}

Text Content:
{text_to_analyze}

Instructions:
1. Identify ALL policy rules, compliance requirements, data retention policies, access controls, security requirements, and operational procedures
2. Extract specific requirements including:
   - Time periods (e.g., "5 years", "30 days", "7-year retention")
   - Data types and classifications
   - Access levels and permissions
   - Constraints and restrictions
   - Compliance obligations
3. For each rule, provide:
   - A clear, concise rule_text (exact quote or paraphrased statement)
   - Appropriate rule_type categorization
   - Key requirements as a list
   - Any time periods mentioned
   - Confidence score (0.0-1.0) based on how explicit and clear the rule is
   - Context if needed to understand the rule's scope
4. Only extract rules that are clearly stated - avoid inferring rules that aren't explicitly mentioned
5. Be thorough - extract all relevant policy statements, not just a few

Return a JSON object with this exact structure:
{{
  "rules": [
    {{
      "rule_id": "RETENTION_001",
      "rule_text": "Customer data must be retained for 5 years",
      "rule_type": "data_retention",
      "key_requirements": ["5 year retention", "customer data"],
      "time_periods": ["5 years"],
      "confidence": 0.95,
      "context": "Applies to all customer data"
    }}
  ]
}}"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for better structured output support
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert policy analyst specializing in extracting structured policy rules from organizational documents. Your task is to identify and extract ALL policy rules, requirements, and compliance statements. Be thorough and extract every relevant policy statement you find. Extract only explicit, clearly stated rules and requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # Lower temperature for more consistent, thorough extraction
                max_tokens=4000
            )
            
            result = json.loads(response.choices[0].message.content)
            extracted_rules = result.get("rules", [])
            
            if not extracted_rules:
                # No rules found - return empty to trigger fallback
                return []
            
            # Transform OpenAI response to our rule format
            rules = []
            for idx, rule_data in enumerate(extracted_rules):
                # Validate required fields
                if not rule_data.get("rule_text"):
                    continue  # Skip invalid rules
                
                rule = {
                    "id": f"soft_rule_{len(self.extracted_rules) + len(rules)}",
                    "source_document": document_id,
                    "source_document_name": document_name,
                    "text": rule_data.get("rule_text", ""),
                    "rule_type": rule_data.get("rule_type", "other"),
                    "key_requirements": rule_data.get("key_requirements", []),
                    "time_periods": rule_data.get("time_periods", []),
                    "context": rule_data.get("context", ""),
                    "extracted_date": datetime.utcnow().isoformat() + "Z",
                    "confidence": float(rule_data.get("confidence", 0.7)),
                    "extraction_method": "openai_gpt4o"
                }
                rules.append(rule)
            
            return rules
            
        except json.JSONDecodeError as e:
            # JSON parsing error - log and return empty
            return []
        except Exception as e:
            # Other OpenAI errors - return empty to trigger fallback
            return []
    
    def _parse_with_keywords(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Fallback: Simple keyword-based rule extraction"""
        rules = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["retention", "retain", "policy", "compliance", "regulation"]):
                rule = {
                    "id": f"soft_rule_{len(self.extracted_rules) + len(rules)}",
                    "source_document": document_id,
                    "text": line.strip(),
                    "rule_type": "other",
                    "key_requirements": [],
                    "time_periods": [],
                    "context": "",
                    "extracted_date": datetime.utcnow().isoformat() + "Z",
                    "confidence": 0.5,  # Lower confidence for keyword-based extraction
                    "extraction_method": "keyword_matching"
                }
                rules.append(rule)
        
        # Store extracted rules
        for rule in rules:
            if rule not in self.extracted_rules:
                self.extracted_rules.append(rule)
        
        return rules
    
    def detect_conflicts(self, hard_ontology_rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts between hard ontology and soft ontology rules"""
        conflicts = []
        
        for soft_rule in self.extracted_rules:
            # Simple conflict detection - in production, use semantic similarity
            soft_text = soft_rule.get("text", "").lower()
            hard_text = str(hard_ontology_rule).lower()
            
            # Check for conflicting time periods (e.g., "5-year" vs "7-year")
            if "year" in soft_text or "retention" in soft_text:
                conflicts.append({
                    "id": f"conflict_{len(conflicts)}",
                    "hard_ontology_rule": hard_ontology_rule,
                    "soft_ontology_rule": soft_rule,
                    "conflict_type": "retention_period",
                    "detected_date": datetime.utcnow().isoformat() + "Z"
                })
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: str, resolution: str, resolution_notes: str = "") -> bool:
        """Record a conflict resolution decision"""
        conflict = next((c for c in self.conflict_resolutions if c.get("id") == conflict_id), None)
        if conflict:
            conflict["resolution"] = resolution
            conflict["resolution_notes"] = resolution_notes
            conflict["resolved_date"] = datetime.utcnow().isoformat() + "Z"
            return True
        
        # If conflict not in resolutions list, add it
        resolution_record = {
            "id": conflict_id,
            "resolution": resolution,
            "resolution_notes": resolution_notes,
            "resolved_date": datetime.utcnow().isoformat() + "Z"
        }
        self.conflict_resolutions.append(resolution_record)
        return True
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """Get all active soft ontology rules (non-conflicting or resolved)"""
        active_rules = []
        
        for rule in self.extracted_rules:
            # Check if rule has unresolved conflicts
            has_conflict = any(
                c.get("soft_ontology_rule", {}).get("id") == rule.get("id")
                for c in self.conflict_resolutions
                if c.get("resolution") != "use_soft_ontology"
            )
            
            if not has_conflict:
                active_rules.append(rule)
        
        return active_rules
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary for serialization"""
        return {
            "documents": [
                {k: v for k, v in doc.items() if k != "content"}  # Exclude binary content
                for doc in self.documents
            ],
            "extracted_rules": self.extracted_rules,
            "conflict_resolutions": self.conflict_resolutions,
            "active_rules_count": len(self.get_active_rules())
        }
