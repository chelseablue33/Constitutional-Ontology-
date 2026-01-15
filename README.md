# 🛡️ Governance Trust Layer (Constitutional Ontology)

> **A comprehensive governance framework for AI agents that ensures safe, compliant, and auditable AI operations through an 8-gate enforcement pipeline.**

---

## 📖 What is Constitutional Ontology?

Imagine you're building an AI assistant that needs to work with sensitive information—like drafting compliance documents for a bank, handling customer data, or creating content that must meet regulatory standards. How do you ensure this AI behaves correctly, respects privacy, follows regulations, and can be trusted?

**Constitutional Ontology** is a governance framework that acts like a "constitution" for your AI agent. Just as a country's constitution defines the fundamental rules and principles that govern behavior, this system defines the rules, controls, and boundaries that govern how your AI agent operates.

### The Core Concept

Instead of hoping your AI will "do the right thing," Constitutional Ontology **enforces** the right behavior at every step. It intercepts actions, evaluates them against policy rules, applies security controls, and makes decisions—all while maintaining a complete audit trail.

Think of it as having a **guardian system** that:
- ✅ Validates every user request before processing
- ✅ Checks permissions and data sensitivity
- ✅ Applies security controls automatically
- ✅ Requires human approval for risky actions
- ✅ Records everything for compliance audits
- ✅ Prevents unauthorized or dangerous operations

---

## 🚪 The 8-Gate Pipeline

Every request flows through **8 sequential gates**, each serving a specific purpose in the governance process:

### **Pre-Flight Gates (1-4): Understanding & Classification**

**Gate 1: Input Validation** 🔍
- Validates the format and structure of user requests
- Detects potential security threats like prompt injection attacks
- Ensures requests meet basic schema requirements

**Gate 2: Intent Classification** 🎯
- Determines what the user is trying to accomplish
- Categorizes requests (e.g., content creation, data retrieval, task management)
- Helps route the request to appropriate handlers

**Gate 3: Data Classification** 🏷️
- Identifies sensitive data types in the request
- Detects PII (Personally Identifiable Information), PHI (Protected Health Information), and regulated data
- Assesses the sensitivity level of the content

**Gate 4: Policy Lookup** 📚
- Selects applicable policy rules based on context
- Matches intent and data classification to relevant regulations
- Determines which controls and constraints apply

### **Verdict Gates (5-6): Decision Making**

**Gate 5: Permission Check** 🔐
- Verifies if the user/agent has permission for the requested action
- Checks if the data classification level allows the operation
- Evaluates role-based access controls

**Gate 6: Action Approval** ⚖️
- Makes the final verdict: **ALLOW**, **ESCALATE** (require human approval), or **DENY**
- Considers all previous gate results and policy rules
- Determines the risk level and appropriate response

### **Evidence Gates (7-8): Audit & Compliance**

**Gate 7: Evidence Capture** 📸
- Records all signals, policies applied, and decisions made
- Captures timestamps, user IDs, and context
- Creates a complete audit trail for compliance

**Gate 8: Audit Export** 📦
- Prepares comprehensive evidence packets
- Packages all trace data, decisions, and metadata
- Enables export for compliance reviews and audits

---

## 🌐 Trust Surfaces: The 8 Communication Channels

The system monitors **8 trust surfaces**—the communication channels between different components of your AI system:

| Surface | Direction | Description |
|---------|-----------|-------------|
| **U-I** | User → Agent | User input, instructions, and feedback |
| **U-O** | Agent → User | Agent responses, drafts, and notifications |
| **S-I** | System → Agent | Data retrieved from systems (databases, APIs, files) |
| **S-O** | Agent → System | Agent actions on systems (tool calls, writes, executions) |
| **M-I** | Memory → Agent | Data retrieved from agent memory |
| **M-O** | Agent → Memory | Data stored in agent memory |
| **A-I** | Other Agent → Agent | Communication from other agents |
| **A-O** | Agent → Other Agent | Communication to other agents |

Each surface has its own set of **allow rules**, **controls**, and **deny rules** defined in your policy. This ensures that data flows are monitored and controlled at every boundary.

---

## 🏛️ Hard Ontology vs. Soft Ontology

### **Hard Ontology** (Baseline)
The **hard ontology** consists of strict, foundational policies that provide the baseline governance framework. These are typically:
- Industry-standard compliance rules (e.g., banking regulations, healthcare HIPAA)
- Security best practices
- Core ethical principles
- Regulatory requirements

These policies are **non-negotiable** and form the foundation of your governance system.

### **Soft Ontology** (Customization)
The **soft ontology** allows organizations to supplement the hard ontology with their own:
- Internal Standard Operating Procedures (SOPs)
- Marketing documentation
- Organization-specific policies
- Custom compliance requirements

This enables organizations to:
- Resolve conflicts between internal policies and baseline rules
- Integrate legacy documentation without perfect data cleanup
- Customize governance to match organizational needs
- Maintain flexibility while preserving the baseline foundation

**Example:** If your organization has a 5-year data retention policy but encounters 7-year-old conflicting data, the soft ontology helps resolve this without requiring perfect data cleanup.

---

## 📱 Application Pages & Functionality

### 🏠 **Main Dashboard** (`app.py`)
The central hub where you interact with the system:
- **Policy Selection**: Choose from available policy files (JSON format)
- **Request Submission**: Enter prompts or requests to process
- **Mode Toggle**: Switch between **SIMULATE** (testing) and **ENFORCE** (production) modes
- **Pipeline Visualization**: See the 8-gate flow with real-time status
- **Trust Surface Activation**: View which communication channels are active
- **Verdict Display**: See the final decision (ALLOW, ESCALATE, DENY)
- **Cognitive Onramp**: Visual representation of gate progress and surface activations

### 🧭 **Pipeline Trace** (`pages/pipeline_trace.py`)
Review detailed information about request processing:
- **Current Trace Details**: View the active trace ID, verdict, and resolution
- **Request Data**: See the original request and its metadata
- **Trace History**: Browse all previous traces
- **Gate Results**: Examine results from each of the 8 gates
- **Replay Functionality**: Replay previous traces to understand decision-making

### ✅ **Approval Queue** (`pages/approval_queue.py`)
Manage requests that require human approval:
- **Pending Approvals**: View all requests flagged for human review
- **Approval Details**: See why approval is required, what rules triggered it, and the risk assessment
- **Approve/Deny Actions**: Make decisions on pending requests with optional reasoning
- **Approval History**: Track all approval decisions and their outcomes

### 📜 **Audit Log** (`pages/audit_log.py`)
Complete decision history and evidence:
- **Filterable Entries**: Filter by verdict, gate, user, or timestamp
- **Decision History**: View all decisions made by the system
- **Evidence Records**: Access complete evidence for each decision
- **Trace Replay**: Replay traces directly from audit log entries
- **Compliance Review**: Export audit data for compliance reviews

### 📦 **Export** (`pages/export.py`)
Generate evidence packets for compliance and auditing:
- **Export Options**: Configure what to include (traces, audit logs, policy versions)
- **Trace Selection**: Export specific traces or all traces
- **Evidence Packet Generation**: Create comprehensive JSON evidence packets
- **Download Functionality**: Download evidence packets for external review
- **Policy Version Tracking**: Include policy version hashes for reproducibility

### 🚪 **Gate Details** (`pages/gate_details.py`)
Deep dive into individual gate results:
- **Trace Selection**: Choose which trace to examine
- **Gate-by-Gate Analysis**: View detailed results for each of the 8 gates
- **Phase Organization**: Gates organized by phase (Pre-Flight, Verdict, Evidence)
- **Signal Inspection**: Examine signals detected at each gate
- **Policy References**: See which policies were applied
- **Export Evidence**: Generate evidence packets for specific gates

### ⚙️ **Policy Editor** (`pages/policy_editor.py`)
Edit and customize policy rules:
- **Policy Selection**: Choose which policy file to edit
- **Rule Management**: Enable/disable individual rules
- **Gate Configuration**: Modify gate settings, controls, and allow/deny lists
- **Overlay Management**: Configure regulatory overlays (e.g., OCC MRM, EU AI Act)
- **Baseline vs. Customization View**: Compare baseline policies with customizations
- **Policy Validation**: Ensure policy changes are valid before saving

### 📄 **Soft Ontology** (`pages/soft_ontology.py`)
Manage organization-specific documentation:
- **Document Upload**: Upload PDF, DOCX, TXT, or Markdown files
- **Text Extraction**: Extract text from uploaded documents
- **Policy Integration**: Integrate organizational SOPs and documentation
- **Document Management**: View, edit, and delete uploaded documents
- **Conflict Resolution**: Use soft ontology to resolve policy conflicts

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Constitutional-Ontology-
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure secrets** (if needed)
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Add your API keys and configuration

5. **Run the application**
   ```bash
   streamlit run app/app.py
   ```

6. **Access the application**
   - Open your browser to `http://localhost:8501`
   - Select a policy file from the sidebar
   - Start submitting requests!

### Policy Files

Policy files are JSON files located in the root directory. They define:
- Gate configurations (allow/deny rules, controls)
- Regulatory overlays
- Rule states and constraints
- Constitutional pillars (dignity, hope, agency)

Example policy files:
- `policy_bank_compliance_v1.json` - Banking compliance baseline
- `policy_bank_compliance_strict.json` - Stricter banking policies

---

## 🎯 Use Cases

This system is designed for organizations that need:

- **Regulated Industries**: Banking, healthcare, legal, pharmaceuticals
- **Compliance Requirements**: GDPR, HIPAA, OCC, EU AI Act, FDA regulations
- **Audit Trails**: Complete decision history for compliance reviews
- **Risk Management**: Human-in-the-loop approval for consequential actions
- **Data Protection**: PII/PHI detection and handling
- **Policy Enforcement**: Automated application of organizational policies

---

## 🏗️ Architecture Overview

```
User Request
    ↓
[Gate 1: Input Validation]
    ↓
[Gate 2: Intent Classification]
    ↓
[Gate 3: Data Classification]
    ↓
[Gate 4: Policy Lookup]
    ↓
[Gate 5: Permission Check]
    ↓
[Gate 6: Action Approval]
    ↓
[Gate 7: Evidence Capture]
    ↓
[Gate 8: Audit Export]
    ↓
Response + Audit Trail
```

Each gate evaluates the request against policy rules, applies controls, and either:
- **ALLOW**: Proceed to next gate
- **DENY**: Block the request and stop
- **ESCALATE**: Require human approval before proceeding

---

## 🔒 Security & Compliance Features

- **Authentication**: SSO-based user authentication
- **Authorization**: Role-based access controls
- **Data Loss Prevention (DLP)**: Automatic scanning for sensitive data
- **Malware Scanning**: Protection against malicious content
- **Provenance Tracking**: Complete source tracking for all data
- **Encryption**: Data encryption at rest and in transit
- **Audit Logging**: Immutable audit trail of all decisions
- **Policy Versioning**: Track policy changes over time

---

## 📚 Key Concepts

### **Constitutional Pillars**

The system is built on three foundational pillars:

1. **Dignity**: Respect for user autonomy, no deception, transparent limitations
2. **Hope**: Accurate information, cited sources, uncertainty acknowledgment
3. **Agency**: User control, opt-out options, permission revocation

### **Regulatory Overlays**

Additional compliance layers that can be enabled:
- **OCC MRM**: Office of the Comptroller Model Risk Management
- **EU AI Act**: European Union AI Act High-Risk requirements
- **FDA GMLP**: FDA Good Machine Learning Practice

### **Dials (Autonomy Levels)**

Configurable autonomy settings:
- **Autonomy**: How independently the agent can act
- **Tool Access**: What tools the agent can use
- **Personalization**: Level of user personalization
- **Memory**: How persistent memory is managed
- **Inter-Agent**: Whether agents can communicate with each other

---

## 🤝 Contributing

This is a governance framework designed for enterprise use. For questions, issues, or contributions, please refer to the project maintainers.

---

## 📄 License

[Specify your license here]

---

## 🙏 Acknowledgments

Built for organizations that need trustworthy, auditable, and compliant AI operations.

---

**🛡️ Governance Trust Layer** - Ensuring AI you can trust, with evidence you can verify.
