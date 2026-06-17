import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentResponse(BaseModel):
    agent_id: str
    name: str
    role: str
    status: str
    message: str
    tags: List[str]

class CrisisScenarioStep(BaseModel):
    step_name: str
    risk_score: int
    revenue_at_risk: str
    affected_users: int
    nodes_compromised: int
    active_incidents: int
    timeline_event: Optional[Dict[str, Any]] = None
    audit_log: Optional[Dict[str, Any]] = None
    agent_update: Optional[Any] = None
    debate_messages: List[Dict[str, Any]] = []

class ScenarioDefinition(BaseModel):
    id: str
    title: str
    severity: str
    description: str
    estimated_impact: str
    agents_involved: List[str]
    initial_data: Dict[str, Any]
    shutdown_label: str = "EXECUTE SHUTDOWN"
    isolation_label: str = "ATTEMPT ISOLATION"
    steps: List[CrisisScenarioStep]
    resolutions: Dict[str, CrisisScenarioStep]

# Registry of all potential AI agents inside the war room
ALL_AGENTS = {
    "Incident Detection Agent": {
        "id": "detection",
        "name": "Threat Detection & Sentinel",
        "role": "IDS_Sentinel",
        "status": "IDLE",
        "lastMessage": "Scanning network logs and integrity hashes.",
        "tags": ["LOG_ANALYZE", "INTEGRITY_CHECK"]
    },
    "Cybersecurity Agent": {
        "id": "sec",
        "name": "Cyber Threat Containment Agent",
        "role": "Security_v4",
        "status": "IDLE",
        "lastMessage": "Monitoring traffic for signs of lateral intrusion.",
        "tags": ["THREAT_HUNT", "DEEP_SCAN"]
    },
    "Infrastructure Agent": {
        "id": "infra",
        "name": "Cloud Infrastructure & Failover Architect",
        "role": "Infra_Link",
        "status": "IDLE",
        "lastMessage": "All system clusters active and balancing load.",
        "tags": ["DNS_SHIFT", "FAILOVER"]
    },
    "Legal Compliance Agent": {
        "id": "legal",
        "name": "Data Protection & Legal Compliance Shield",
        "role": "Legal_Mind",
        "status": "IDLE",
        "lastMessage": "Compliance scanning GDPR/CCPA regulations.",
        "tags": ["GDPR_ART33", "LIABILITY"]
    },
    "Finance Agent": {
        "id": "finance",
        "name": "Revenue Loss & Transaction Risk Auditor",
        "role": "Finance_Flow",
        "status": "IDLE",
        "lastMessage": "Monitoring liquidity pools and billing APIs.",
        "tags": ["REVENUE_RISK", "TX_AUDIT"]
    },
    "Customer Impact Agent": {
        "id": "cx",
        "name": "Telemetry & Customer Churn Analyst",
        "role": "User_Telemetry",
        "status": "IDLE",
        "lastMessage": "Analyzing customer churn risk and active session drop-offs.",
        "tags": ["CX_MONITOR", "CHURN_PREDICT"]
    },
    "Public Relations Agent": {
        "id": "pr",
        "name": "Public Relations & Crisis Communications Officer",
        "role": "Comm_Ops",
        "status": "IDLE",
        "lastMessage": "Press hold templates ready.",
        "tags": ["STMT_A1", "PRESS_WIRE"]
    },
    "Recovery Agent": {
        "id": "recovery",
        "name": "Data Recovery & System Reconstruction Agent",
        "role": "Recovery_Ops",
        "status": "IDLE",
        "lastMessage": "Shadow volume and database replication points verified.",
        "tags": ["BACKUP_RESTORE", "CLUSTER_REBUILD"]
    },
    "Risk Assessment Agent": {
        "id": "risk",
        "name": "Enterprise Risk Multi-Vector Calculator",
        "role": "Risk_Calc",
        "status": "IDLE",
        "lastMessage": "Risk vector assessment at base level.",
        "tags": ["FINANCIAL_EST", "IMPACT_PROJ"]
    },
    "HR Agent": {
        "id": "hr",
        "name": "Insider Threat & Access Controller (HR)",
        "role": "HR_Ops",
        "status": "IDLE",
        "lastMessage": "Access logs tied to physical building card swipe checks.",
        "tags": ["PERSONNEL_LOCK", "COMP_INSIDER"]
    },
    "Operations Agent": {
        "id": "ops",
        "name": "Supply Chain & Logistics Resiliency Agent",
        "role": "Ops_Core",
        "status": "IDLE",
        "lastMessage": "Supply lines and logistical pipelines monitored.",
        "tags": ["SUPPLY_RCA", "LOGISTICS"]
    },
    "Marketing Agent": {
        "id": "marketing",
        "name": "Brand Sentiment & Counter-Promotion Manager",
        "role": "Marketing_Ops",
        "status": "IDLE",
        "lastMessage": "Reviewing ad placement pauses and campaign responses.",
        "tags": ["BRAND_RESCUE", "AD_PAUSE"]
    },
    "CTO Agent": {
        "id": "cto",
        "name": "Chief Technology Architect Agent",
        "role": "CTO",
        "status": "IDLE",
        "lastMessage": "Evaluating engineering architecture health.",
        "tags": ["ARCH_INTEGRITY", "TECH_DEBT"]
    },
    "CEO Agent": {
        "id": "ceo",
        "name": "Chief Executive Decision Agent",
        "role": "CEO",
        "status": "IDLE",
        "lastMessage": "Overseeing operational alignment and decision vectors.",
        "tags": ["EXEC_AUTHORITY", "STRATEGY"]
    },
    "CFO Agent": {
        "id": "cfo",
        "name": "Chief Financial Risk Strategist",
        "role": "CFO",
        "status": "IDLE",
        "lastMessage": "Analyzing cost structures and revenue lines.",
        "tags": ["LIQUIDITY", "LOSS_PREVENT"]
    },
    "CISO Agent": {
        "id": "ciso",
        "name": "Chief Information Security Officer Agent",
        "role": "CISO",
        "status": "IDLE",
        "lastMessage": "Enforcing data protection policies.",
        "tags": ["COMPLIANCE_GOV", "SECURITY_POL"]
    }
}

SCENARIOS: Dict[str, ScenarioDefinition] = {
    # Scenario 1: Customer Data Breach
    "INC-001": ScenarioDefinition(
        id="INC-001",
        title="Customer Database Breach",
        severity="Critical",
        description="Unauthorized access detected in the production customer database.",
        estimated_impact="150,000 users affected (European Union)",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-001",
            "incident_type": "Data Breach",
            "severity": "Critical",
            "affected_users": 150000,
            "region": "European Union",
            "database": "Customer PostgreSQL",
            "sensitive_data": ["Emails", "Phone Numbers", "Addresses"]
        },
        shutdown_label="EXECUTE SHUTDOWN",
        isolation_label="ATTEMPT ISOLATION",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION",
                risk_score=70,
                revenue_at_risk="$1.2M",
                affected_users=25000,
                nodes_compromised=2,
                active_incidents=1,
                timeline_event={"time": "08:11", "title": "BREACH DETECTED", "description": "Unauthorized SQL queries originating from external VPN IP found on Customer PostgreSQL.", "module": "INCIDENT_SYS", "severity": "critical"},
                audit_log={"timestamp": "08:11:04", "agent": "Detection_Agent", "action": "CREATE_ROOM", "details": "Crisis war room opened for PostgreSQL data breach."},
                agent_update=[
                    {"id": "detection", "status": "ACTIVE", "lastMessage": "ALERT: SQL Injection pattern detected on Customer PostgreSQL."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Tracing active database connection logs and queries."},
                    {"id": "infra", "status": "THINKING", "lastMessage": "Analyzing CPU spikes and network logs on DB clusters."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION",
                risk_score=85,
                revenue_at_risk="$2.8M",
                affected_users=95000,
                nodes_compromised=4,
                active_incidents=3,
                timeline_event={"time": "08:15", "title": "THREAT TRACED", "description": "Cybersecurity Agent confirms SQL injection vulnerability leveraged on DB Gateway. Exfiltration rate: 45GB/s.", "module": "BAND_SDK", "severity": "critical"},
                audit_log={"timestamp": "08:15:12", "agent": "Security_Agent", "action": "LOG_IOC", "details": "SQL Injection pattern logged. Source IP: 185.220.101.4."},
                agent_update=[
                    {"id": "detection", "status": "SLEEPING", "lastMessage": "Alert handoff confirmed. System telemetry monitoring active."},
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "SQL injection verified. Source IP: 185.220.101.4. Tracing exfiltration rates."},
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Isolating database subnet G-9. Diverting operational API traffic."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Auditing active billing APIs and calculating conversion drop rates."},
                    {"id": "cx", "status": "THINKING", "lastMessage": "Scanning active customer checkout drop-offs and session timeouts."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL",
                risk_score=94,
                revenue_at_risk="$4.2M",
                affected_users=150000,
                nodes_compromised=6,
                active_incidents=7,
                timeline_event={"time": "08:30", "title": "GDPR OBLIGATIONS MANDATED", "description": "Legal Agent identifies EU region sensitive data. Mandates GDPR Article 33 notification (72h limit).", "module": "LEGAL_SHIELD", "severity": "critical"},
                audit_log={"timestamp": "08:30:45", "agent": "Risk_Agent", "action": "CALC_LOSS", "details": "Hourly exfiltration rate indicates GDPR fine could reach 4% of global turnover."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Containment pending C-suite command. Network traps configured."},
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Traffic diverted. Secondary subnets operating on backup routes."},
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Revenue risk verified: $4.2M. Transaction conversion down 35%."},
                    {"id": "cx", "status": "ACTIVE", "lastMessage": "150,000 active EU customer accounts identified in scope of exposure."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Analyzing GDPR Article 33 notifications and liability thresholds."},
                    {"id": "pr", "status": "THINKING", "lastMessage": "Preparing crisis holding statements and internal notifications."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE",
                risk_score=96,
                revenue_at_risk="$4.2M",
                affected_users=150000,
                nodes_compromised=6,
                active_incidents=7,
                timeline_event={"time": "08:40", "title": "C-SUITE WAR ROOM ACTIVE", "description": "Executive board agents actively debating database lockdown vs. network segment isolation in Band Room.", "module": "EXEC_BOARD", "severity": "critical"},
                audit_log={"timestamp": "08:40:02", "agent": "CEO_ALPHA", "action": "POLL_CONVICTION", "details": "Requesting immediate conviction votes for DB containment."},
                debate_messages=[
                    {"sender": "CISO_SHIELD", "role": "CISO", "timestamp": "08:40:11", "content": "The exfiltration of Customer PostgreSQL is ongoing. I recommend an immediate database shutdown. The risks of further exfiltration exceed any operational costs.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "08:40:29", "content": "Shutting down the database halts all customer checkout processes. That represents -$12M/hr in liquidity. I recommend partial network isolation of Segment G-9.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "08:41:00", "content": "We need to act. Operator, please select whether to execute a full database shutdown or attempt network isolation.", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Revenue risk report finalized. Standing by."},
                    {"id": "cx", "status": "SLEEPING", "lastMessage": "Telemetry metrics synced. Directives received."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "Compliance disclosure package finalized. EDPB ready for submit."},
                    {"id": "pr", "status": "ACTIVE", "lastMessage": "Hold statement templates ready for distribution pending Board action."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends immediate database shutdown to prevent further leaks."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises isolation over shutdown to prevent $12M/hr business loss."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Coordinating crisis command votes. Ready for operator input."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=12, revenue_at_risk="$0", affected_users=150000, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "09:00", "title": "SHUTDOWN EXECUTED", "description": "C-Suite consensus: Customer DB terminated. Containment successful. Data leak halted.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "09:00:15", "agent": "CISO_Agent", "action": "EXECUTE_SHUTDOWN", "details": "PostgreSQL database connection pools closed."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=45, revenue_at_risk="$1.2M", affected_users=150000, nodes_compromised=2, active_incidents=2,
                timeline_event={"time": "09:00", "title": "ISOLATION EXECUTED", "description": "C-Suite consensus: Segment G-9 isolated. DB remains online but secondary breach vectors remain active.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "09:00:22", "agent": "CISO_Agent", "action": "ISOLATE_SEGMENT", "details": "Subnet G-9 isolated. SQL injection vector mitigated but session logs show secondary threats."}
            )
        }
    ),

    # Scenario 2: Cloud Infrastructure Outage
    "INC-002": ScenarioDefinition(
        id="INC-002",
        title="Regional Cloud Outage",
        severity="High",
        description="Critical cloud infrastructure failure affecting customer services.",
        estimated_impact="Payment API, Dashboard, Auth down (AWS us-east-1)",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-002",
            "incident_type": "Infrastructure Outage",
            "severity": "High",
            "affected_region": "AWS us-east-1",
            "services_impacted": ["Payment API", "Customer Dashboard", "Authentication Service"]
        },
        shutdown_label="FAILOVER TO WEST",
        isolation_label="LOCAL RECOVERY",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=55, revenue_at_risk="$500K", affected_users=18000, nodes_compromised=1, active_incidents=2,
                timeline_event={"time": "10:05", "title": "SERVICE HEALTH DROP", "description": "Payment API response times exceeded 15000ms. High packet loss detected in AWS us-east-1.", "module": "INFRA_MONITOR", "severity": "medium"},
                audit_log={"timestamp": "10:05:30", "agent": "Infrastructure_Agent", "action": "POLL_PING", "details": "Health checks failing for load balancer nodes in us-east-1a."},
                agent_update=[
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Checking cluster ping response."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Analyzing security group rules and routing anomalies."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=75, revenue_at_risk="$1.8M", affected_users=62000, nodes_compromised=4, active_incidents=4,
                timeline_event={"time": "10:15", "title": "AWS NETWORK CORRUPTION", "description": "CISO Agent identifies root cause as corrupted routing tables and EBS volume lockup in AWS us-east-1.", "module": "CTO_OFFICE", "severity": "high"},
                audit_log={"timestamp": "10:15:44", "agent": "CTO_NODAL", "action": "DIAGNOSE_OUTAGE", "details": "AWS API endpoints in us-east-1 reporting 503 Service Unavailable."},
                agent_update=[
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Diagnostics complete: volumes locked."},
                    {"id": "ciso", "status": "ACTIVE", "lastMessage": "AWS API endpoints reporting 503 errors. Routing tables corrupted."},
                    {"id": "cx", "status": "THINKING", "lastMessage": "Scanning active customer checkout drop-offs and session timeouts."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=88, revenue_at_risk="$2.9M", affected_users=120000, nodes_compromised=5, active_incidents=5,
                timeline_event={"time": "10:25", "title": "REVENUE DEGRADATION REPORTED", "description": "Finance Agent reports outage is blocking customer conversions, losing $400K every 10 minutes.", "module": "FINANCE_DEPT", "severity": "high"},
                audit_log={"timestamp": "10:25:12", "agent": "Finance_Agent", "action": "CALC_LOSS", "details": "Estimated revenue losses mounting. CX telemetry confirms checkout errors."},
                agent_update=[
                    {"id": "ciso", "status": "SLEEPING", "lastMessage": "Outage diagnostics finalized. Standby for recovery routes."},
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Modeling checkout failure rates. Losses mounting at $40K/min."},
                    {"id": "cx", "status": "ACTIVE", "lastMessage": "Checkout drop-off verified. High volume of failing API pings."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=90, revenue_at_risk="$2.9M", affected_users=120000, nodes_compromised=5, active_incidents=5,
                timeline_event={"time": "10:35", "title": "FAILOVER DEBATE", "description": "CTO recommends routing traffic to us-west-2, which requires a 15-minute sync. CEO weighs sync risks.", "module": "EXEC_BOARD", "severity": "high"},
                audit_log={"timestamp": "10:35:05", "agent": "CEO_ALPHA", "action": "DEBATE_CHOICE", "details": "Debating local database patch vs full active-passive failover."},
                debate_messages=[
                    {"sender": "CTO_NODAL", "role": "CISO", "timestamp": "10:35:12", "content": "us-east-1 is fully unresponsive. We must trigger a FAILOVER TO WEST immediately to restore Payment API stability.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "10:35:30", "content": "A failover sync will trigger a 15-minute window of complete data inconsistency. Can we attempt local recovery or wait for AWS?", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "10:36:00", "content": "We cannot wait for AWS. Operator, make the call: failover to us-west-2 or attempt local database sync?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Financial loss models finalized. Waiting for decision."},
                    {"id": "cx", "status": "SLEEPING", "lastMessage": "Customer impact package ready. Redirect logic tested."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises local database sync to prevent Q3 balance sheet hit."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Coordinating failover decision. Ready for operator input."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=10, revenue_at_risk="$0", affected_users=120000, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "10:50", "title": "WEST FAILOVER COMPLETE", "description": "Traffic successfully routed to us-west-2. Payment API response times normalized.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "10:50:20", "agent": "Recovery_Agent", "action": "FAILOVER_ROUTE", "details": "Route53 DNS switched to us-west-2. Backups synced successfully."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=35, revenue_at_risk="$800K", affected_users=120000, nodes_compromised=2, active_incidents=1,
                timeline_event={"time": "10:50", "title": "LOCAL CONTAINER RESTART", "description": "Attempted local container restart in us-east-1. Systems partially up, but stability is low.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "10:50:25", "agent": "Infrastructure_Agent", "action": "REBOOT_PODS", "details": "Restarted 3 Kubernetes pods in us-east-1. Network degradation remains."}
            )
        }
    ),

    # Scenario 3: Ransomware Attack
    "INC-003": ScenarioDefinition(
        id="INC-003",
        title="Enterprise Ransomware Incident",
        severity="Critical",
        description="Multiple internal systems encrypted by ransomware.",
        estimated_impact="320 devices compromised, $500,000 ransom.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-003",
            "incident_type": "Ransomware",
            "severity": "Critical",
            "affected_devices": 320,
            "ransom_amount": 500000
        },
        shutdown_label="REBUILD BACKUPS",
        isolation_label="PAY THE RANSOM",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=80, revenue_at_risk="$2.0M", affected_users=5000, nodes_compromised=45, active_incidents=3,
                timeline_event={"time": "11:10", "title": "MASS ENCRYPTION DETECTED", "description": "Ransomware signature 'LockBit 3.0' detected across 45 virtual desktop nodes.", "module": "ENDPOINT_SEC", "severity": "critical"},
                audit_log={"timestamp": "11:10:15", "agent": "Security_Agent", "action": "QUARANTINE_IP", "details": "Isolating active file shares to prevent further encryption spread."},
                agent_update=[
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "LockBit 3.0 ransomware detected on corporate desktops."},
                    {"id": "detection", "status": "THINKING", "lastMessage": "Scanning endpoint logs for ransomware signature matches."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=90, revenue_at_risk="$3.5M", affected_users=8000, nodes_compromised=120, active_incidents=12,
                timeline_event={"time": "11:25", "title": "SHADOW COPIES DELETED", "description": "Recovery Agent reports attacker deleted all local Windows shadow volume copies.", "module": "RECOVERY_OPS", "severity": "critical"},
                audit_log={"timestamp": "11:25:33", "agent": "Recovery_Agent", "action": "AUDIT_BACKUPS", "details": "Local backups compromised. Offline backups in cold storage remain intact."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Isolating file shares. Spread contained."},
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Auditing offline tape backups. Cold storage tapes remain intact."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Reviewing data exfiltration clauses and notification limits."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=95, revenue_at_risk="$4.8M", affected_users=1200, nodes_compromised=320, active_incidents=20,
                timeline_event={"time": "11:40", "title": "LEGAL SANCTION WARNING", "description": "Legal Agent warns that paying ransom to this threat actor group may violate OFAC compliance sanctions.", "module": "LEGAL_MIND", "severity": "critical"},
                audit_log={"timestamp": "11:40:02", "agent": "Legal_Agent", "action": "CHECK_OFAC", "details": "Checking hacker cryptocurrency wallet address against sanctions lists."},
                agent_update=[
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Disaster recovery cluster initialized. Ready for tape sync."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "Checking hacker Bitcoin address against OFAC sanctions database."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Evaluating ransom cost-benefit versus restoration downtime."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=98, revenue_at_risk="$4.8M", affected_users=1200, nodes_compromised=320, active_incidents=20,
                timeline_event={"time": "11:50", "title": "RANSOM DEBATE ACTIVE", "description": "CISO recommends refusing payment and rebuilding from cold backups. CFO fears a 3-day recovery window.", "module": "EXEC_BOARD", "severity": "critical"},
                audit_log={"timestamp": "11:50:11", "agent": "CEO_ALPHA", "action": "POLL_BOARD", "details": "Gathering votes on whether to negotiate payment or trigger disaster recovery rebuild."},
                debate_messages=[
                    {"sender": "CISO_SHIELD", "role": "CISO", "timestamp": "11:50:20", "content": "We must never pay. Rebuilding from cold backups is the only compliant path, even if it takes 48 hours.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "11:50:45", "content": "48 hours offline will cost us $5M in business outage and risk permanent customer churn. Paying the $500K is cheaper.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "11:51:10", "content": "If we pay, we violate regulatory codes. If we rebuild, the losses are massive. Operator, what is the path?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "OFAC audit trail sealed. Regulatory warnings submitted."},
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Loss projection report compiled. Awaiting Board vote."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends refusing payment and rebuilding from cold backups."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises negotiating payment to prevent massive business outage."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Polling executive board. Ready for operator input."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=15, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "12:15", "title": "COLD STORAGE REBUILD INITIATED", "description": "Refused ransom. Recovery Agent restoring systems from cold backup. Rebuild complete in 36 hours.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "12:15:30", "agent": "Recovery_Agent", "action": "REBUILD_ALL", "details": "Re-imaging compromised nodes. Restoring system state from June 14 backup."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=50, revenue_at_risk="$1.0M", affected_users=5000, nodes_compromised=80, active_incidents=2,
                timeline_event={"time": "12:15", "title": "RANSOM PAID", "description": "Paid $500K via crypto. Decryption tool received, but restoration is slow and compliance audits are triggered.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "12:15:40", "agent": "CEO_ALPHA", "action": "SEND_TRANSACTION", "details": "Crypto transaction completed. Decryption keys received. Beginning scanning."}
            )
        }
    ),

    # Scenario 4: Regulatory Compliance Violation
    "INC-004": ScenarioDefinition(
        id="INC-004",
        title="GDPR Compliance Violation",
        severity="High",
        description="Unauthorized retention of customer data discovered.",
        estimated_impact="500,000 records affected, regulatory penalty risk.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-004",
            "incident_type": "Compliance Violation",
            "severity": "High",
            "regulation": "GDPR",
            "affected_records": 500000
        },
        shutdown_label="SELF DISCLOSE",
        isolation_label="SILENT REMEDIATION",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=45, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "13:00", "title": "RETENTION EXPOSURE DETECTED", "description": "Compliance Agent discovers legacy server keeping 500,000 unencrypted customer records past the retention limit.", "module": "COMPLIANCE_SYS", "severity": "medium"},
                audit_log={"timestamp": "13:00:10", "agent": "Legal_Agent", "action": "FLAG_RECORDS", "details": "Flagging data store volume 'legacy_backup_2021'."},
                agent_update=[
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "Compliance scanner flags legacy directory with 500,000 records."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Retrieving customer billing geo-distribution logs."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=65, revenue_at_risk="$1.0M", affected_users=500000, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "13:15", "title": "AUDIT VERIFICATION", "description": "Risk Agent confirms database contains names, phone numbers, and addresses. GDPR delete mandates were ignored.", "module": "RISK_CALC", "severity": "high"},
                audit_log={"timestamp": "13:15:35", "agent": "Risk_Agent", "action": "VERIFY_DATA", "details": "Identified sensitive PII on unencrypted network volume."},
                agent_update=[
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "PII exposure confirmed. Data mapping logged."},
                    {"id": "cfo", "status": "ACTIVE", "lastMessage": "Verifying expired names, phone numbers, and addresses in backup."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Modeling liability exposure values under GDPR Article 83 parameters."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=80, revenue_at_risk="$2.5M", affected_users=500000, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "13:30", "title": "REGULATORY PENALTY ESTIMATED", "description": "Finance Agent models potential GDPR fine at $2.2M based on records volume and severity.", "module": "FINANCE_DEPT", "severity": "high"},
                audit_log={"timestamp": "13:30:12", "agent": "Finance_Agent", "action": "ESTIMATE_FINE", "details": "Calculated GDPR Article 83 penalty probability at 78%."},
                agent_update=[
                    {"id": "cfo", "status": "SLEEPING", "lastMessage": "Financial exposure logged. Preparing compliance report."},
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Estimated potential GDPR penalty up to $2.2M (4% of global turnover)."},
                    {"id": "pr", "status": "THINKING", "lastMessage": "Drafting disclosure templates for supervisory authorities."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=82, revenue_at_risk="$2.5M", affected_users=500000, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "13:40", "title": "DISCLOSURE DEBATE ACTIVE", "description": "Board debates voluntary self-disclosure to Commissioner vs silent wipe and patch of internal logs.", "module": "EXEC_BOARD", "severity": "high"},
                audit_log={"timestamp": "13:40:02", "agent": "CEO_ALPHA", "action": "INITIATE_VOTE", "details": "Polling board on self-disclosure strategy."},
                debate_messages=[
                    {"sender": "Compliance Shield", "role": "CISO", "timestamp": "13:40:15", "content": "We must self-disclose immediately. If the regulator discovers this via audit first, the penalty will double.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "13:40:35", "content": "Self-disclosure will tank our stock price by 5%. Let's silently purge the records and document it as a scheduled cleanup.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "13:41:00", "content": "This is a serious governance question. Operator, do we self-disclose to the commissioner or implement a silent internal wipe?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "GDPR penalty modeling finalized. Awaiting board decision."},
                    {"id": "pr", "status": "SLEEPING", "lastMessage": "Holding statements prepared. PR wire integration active."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO advises immediate self-disclosure to minimize brand impact."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises silent wipe and patching to protect stock valuation."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Polling board for self-disclosure strategy. Awaiting choice."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=20, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "14:00", "title": "SELF-DISCLOSURE FILED", "description": "Disclosed violation to European Data Protection Board. Purged database volume. Compliance rating secured.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "14:00:20", "agent": "Legal_Agent", "action": "DISCLOSE_EDPB", "details": "GDPR compliance report submitted to regulatory portal."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=40, revenue_at_risk="$500K", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "14:00", "title": "SILENT WIPE EXECUTED", "description": "Database volume purged. Internal records updated. High residual risk of discovery during next external audit.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "14:00:25", "agent": "CTO_NODAL", "action": "WIPE_VOLUME", "details": "Secure erase command executed on volume 'legacy_backup_2021'."}
            )
        }
    ),

    # Scenario 5: Brand Reputation Crisis
    "INC-005": ScenarioDefinition(
        id="INC-005",
        title="Brand Reputation Crisis",
        severity="Medium",
        description="Negative viral campaign targeting company reputation.",
        estimated_impact="12,000 viral posts, 5,000,000 reach.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-005",
            "incident_type": "PR Crisis",
            "severity": "Medium",
            "viral_posts": 12000,
            "estimated_reach": 5000000
        },
        shutdown_label="PUBLIC APOLOGY",
        isolation_label="COUNTER PROMOTION",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=35, revenue_at_risk="$100K", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "15:01", "title": "VIRAL HASHTAG DETECTED", "description": "PR Agent flags trending social hashtag #CrisisCommandData alleging shadow tracking on customer devices.", "module": "SOCIAL_LISTEN", "severity": "medium"},
                audit_log={"timestamp": "15:01:15", "agent": "PR_Agent", "action": "START_MONITORING", "details": "Tracking keyword frequency and sentiment indices on Twitter."},
                agent_update=[
                    {"id": "pr", "status": "ACTIVE", "lastMessage": "Hashtag #CrisisCommandData trending. Allegations of tracking."},
                    {"id": "cx", "status": "THINKING", "lastMessage": "Analyzing telemetry traffic for diagnostic loop spikes."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=50, revenue_at_risk="$300K", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "15:15", "title": "SENTIMENT CRASH", "description": "Customer Impact Agent confirms overall brand sentiment has dropped 65%. 12,000 viral posts identified.", "module": "SENTIMENT_ENGINE", "severity": "medium"},
                audit_log={"timestamp": "15:15:30", "agent": "cx", "action": "CALC_SENTIMENT", "details": "Brand score dropped from 74 to 26 in under 2 hours."},
                agent_update=[
                    {"id": "pr", "status": "SLEEPING", "lastMessage": "Keyword sentiment monitored. Press release template queued."},
                    {"id": "cx", "status": "ACTIVE", "lastMessage": "Brand sentiment index dropped 65%. 12k viral posts confirmed."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "Calculating customer churn value and subscription impact."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=60, revenue_at_risk="$800K", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "15:30", "title": "CHURN RISK ASCENDING", "description": "Risk Agent reports potential 4% user churn if corporate response is delayed beyond 1 hour.", "module": "RISK_CALC", "severity": "high"},
                audit_log={"timestamp": "15:30:45", "agent": "Risk_Agent", "action": "CALC_CHURN", "details": "Projecting $80K daily recurring revenue churn risk."},
                agent_update=[
                    {"id": "cx", "status": "SLEEPING", "lastMessage": "Customer sentiment metrics finalized. Retargeting group built."},
                    {"id": "cfo", "status": "ACTIVE", "lastMessage": "Projecting $80K daily recurring revenue churn risk if delayed."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Checking Terms of Service clauses for diagnostic disclosure obligations."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=65, revenue_at_risk="$800K", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "15:40", "title": "RESPONSE STRATEGY DEBATE", "description": "PR recommends a public apology and bug bounty program launch. Marketing prefers counter-promotions and ads.", "module": "EXEC_BOARD", "severity": "medium"},
                audit_log={"timestamp": "15:40:02", "agent": "CEO_ALPHA", "action": "VOTE_REPLY", "details": "Polling options for public statement response."},
                debate_messages=[
                    {"sender": "Public Relations", "role": "PR", "timestamp": "15:40:12", "content": "We need to issue a public apology immediately. Admitting the discrepancy and launching a transparency site is the only way to defuse this.", "sentiment": "alert"},
                    {"sender": "Brand Marketing", "role": "CFO", "timestamp": "15:40:30", "content": "An apology validates their claims. We should run a counter-promotion highlight campaign emphasizing our security frameworks.", "sentiment": "neutral"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "15:41:00", "content": "Delay is hurting us. Operator, do we issue a public apology or launch a counter promotion campaign?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "cfo", "status": "SLEEPING", "lastMessage": "Churn metrics logged. Waiting for public response strategy."},
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "Legal review of disclosure policy completed."},
                    {"id": "pr", "status": "ACTIVE", "lastMessage": "PR recommends a public apology and bug bounty program launch."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "Marketing team suggests counter-promotion ads over apology."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Coordinating response strategy. Awaiting operator input."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=10, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "16:00", "title": "PUBLIC APOLOGY ISSUED", "description": "Apology statement issued. Brand score stabilizing. 78% of viral traffic defused.", "module": "EXECUTIVE_DECISION", "severity": "low"},
                audit_log={"timestamp": "16:00:15", "agent": "PR_Agent", "action": "RELEASE_STATEMENT", "details": "Public statement released on corporate news wire."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=25, revenue_at_risk="$200K", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "16:00", "title": "COUNTER CAMPAIGN LAUNCHED", "description": "Counter promotion live. Hashtag trend is slowly dropping, but negative sub-threads persist.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "16:00:20", "agent": "marketing", "action": "LAUNCH_ADS", "details": "Google/Social Security ad campaign activated."}
            )
        }
    ),

    # Scenario 6: Insider Threat
    "INC-006": ScenarioDefinition(
        id="INC-006",
        title="Malicious Insider Activity",
        severity="Critical",
        description="Employee detected accessing confidential data without authorization.",
        estimated_impact="DBA role, 300 sensitive files accessed.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-006",
            "incident_type": "Insider Threat",
            "severity": "Critical",
            "employee_role": "Database Administrator",
            "sensitive_files_accessed": 300
        },
        shutdown_label="REVOKE ACCESS",
        isolation_label="MONITOR ACTIONS",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=60, revenue_at_risk="$500K", affected_users=0, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "17:05", "title": "CONFIDENTIAL DATA SIPHON", "description": "Security Agent flags anomalous file downloads from DBA account 'j_doe' at 03:00 AM.", "module": "FILE_AUDIT", "severity": "medium"},
                audit_log={"timestamp": "17:05:12", "agent": "Security_Agent", "action": "FLAG_DOWNLOAD", "details": "Account downloaded 300 intellectual property files."},
                agent_update=[
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "Anomalous file downloads flagged on DBA account 'j_doe' at 3 AM."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "Auditing administrator access logs and session cookies."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=78, revenue_at_risk="$1.2M", affected_users=0, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "17:15", "title": "NON-COMPANY IP VERIFIED", "description": "HR Agent confirms employee is currently on annual leave. IP address resolves to a residential subnet in a different country.", "module": "HR_OPS", "severity": "high"},
                audit_log={"timestamp": "17:15:30", "agent": "hr", "action": "VERIFY_LEAVE", "details": "Employee confirmed out-of-office. No business reason for database downloads."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Session token quarantined. Lateral scan complete."},
                    {"id": "ciso", "status": "ACTIVE", "lastMessage": "DBA confirmed on leave. Session IP resolves to residential VPN node."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Verifying proprietary intellectual property exfiltration rating."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=85, revenue_at_risk="$2.0M", affected_users=0, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "17:30", "title": "INTELLECTUAL PROPERTY LOSS", "description": "Legal Agent warns that stolen data contains proprietary model weights and codebases. High legal exposure.", "module": "LEGAL_SHIELD", "severity": "critical"},
                audit_log={"timestamp": "17:30:45", "agent": "Legal_Agent", "action": "EVAL_EXPOSURE", "details": "Proprietary IP code loss risk high. Preparing injunction templates."},
                agent_update=[
                    {"id": "ciso", "status": "SLEEPING", "lastMessage": "Admin account locked. VPN routing tables updated."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "Proprietary model weights compromised. Preparing legal injunction."},
                    {"id": "pr", "status": "THINKING", "lastMessage": "Drafting internal employee notification guidelines."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=90, revenue_at_risk="$2.0M", affected_users=0, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "17:40", "title": "CONTAINMENT DEBATE ACTIVE", "description": "Board debates immediate account revocation vs silent monitoring to identify transfer destination and accomplice.", "module": "EXEC_BOARD", "severity": "critical"},
                audit_log={"timestamp": "17:40:02", "agent": "CEO_ALPHA", "action": "INITIATE_VOTE", "details": "Board reviewing risk of account suspension vs intelligence gathering."},
                debate_messages=[
                    {"sender": "Security Sentinel", "role": "CISO", "timestamp": "17:40:11", "content": "I recommend immediate account termination and credential revocation. Every second we wait, more files are siphoned.", "sentiment": "critical"},
                    {"sender": "Compliance Shield", "role": "Legal", "timestamp": "17:40:35", "content": "If we suspend now, the attacker realizes they are caught and may delete evidence. Silent monitoring allows us to build a legal case.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "17:41:00", "content": "Both options are high-stakes. Operator, do we revoke access immediately or silently monitor their actions?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "IP exfiltration legal templates ready. Injunction drafted."},
                    {"id": "pr", "status": "SLEEPING", "lastMessage": "Internal memo ready. Communication templates active."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends immediate account termination and AD lockout."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO recommends silent monitoring to trace download destination."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Reviewing security policy. Awaiting decision: Revoke or Monitor."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=10, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "18:00", "title": "CREDENTIALS REVOKED", "description": "DBA account suspended. Active connections killed. Attacker locked out. File exfiltration halted.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "18:00:20", "agent": "Security_Agent", "action": "SUSPEND_USER", "details": "Active sessions terminated. Credentials disabled in Active Directory."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=35, revenue_at_risk="$400K", affected_users=0, nodes_compromised=1, active_incidents=1,
                timeline_event={"time": "18:00", "title": "SILENT TRACKING LOGGED", "description": "Monitored credentials. Attacker transferred siphoned files to external server. IP locked. Suspect identified.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "18:00:25", "agent": "Security_Agent", "action": "TRACE_FILE", "details": "Recorded file transfer destination: sf_upload_external.net."}
            )
        }
    ),

    # Scenario 7: Product Recall
    "INC-007": ScenarioDefinition(
        id="INC-007",
        title="Global Product Recall",
        severity="High",
        description="Critical defect discovered in released product.",
        estimated_impact="75,000 customers affected (US, EU, APAC).",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-007",
            "incident_type": "Product Recall",
            "severity": "High",
            "customers_impacted": 75000,
            "regions": ["US", "EU", "APAC"]
        },
        shutdown_label="GLOBAL RECALL",
        isolation_label="TARGETED SWAP",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=50, revenue_at_risk="$800K", affected_users=5000, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "19:00", "title": "DEFECT DETECTED", "description": "Operations Agent flags overheating hardware issues in production lot #412. Safety thresholds violated.", "module": "QA_MONITOR", "severity": "medium"},
                audit_log={"timestamp": "19:00:15", "agent": "Operations_Agent", "action": "FLAG_QA", "details": "QA sensor reporting thermal runtime spikes."},
                agent_update=[
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Thermal runtime warnings triggered on Lot #412 battery nodes."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Checking firmware signing keys for unauthorized modification."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=70, revenue_at_risk="$2.1M", affected_users=25000, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "19:15", "title": "LOT SCOPE EXPANDED", "description": "Operations Agent identifies that 75,000 units are currently deployed to customers in US, EU, and APAC.", "module": "SUPPLY_OPS", "severity": "high"},
                audit_log={"timestamp": "19:15:30", "agent": "ops", "action": "AUDIT_DISTRIBUTION", "details": "Confirmed lot #412 units shipped to 3 major distribution channels."},
                agent_update=[
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Battery safety limits configured in registry."},
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "No malware found. Overheating confirmed as QA hardware defect."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Scanning regulatory safety codes and class-action exposure."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=85, revenue_at_risk="$3.8M", affected_users=75000, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "19:30", "title": "LIABILITY RATING LOGGED", "description": "Legal Agent warns of class-action risks. Finance Agent calculates total recall cost at $3.5M.", "module": "FINANCE_DEPT", "severity": "high"},
                audit_log={"timestamp": "19:30:45", "agent": "Finance_Agent", "action": "CALC_RECALL_COST", "details": "Model includes return logistics, processing, and restocking."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Hardware diagnostic signature database updated."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "Consumer safety violation risk high. Advising immediate recall."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Calculating total recall logistics and restocking expense."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=88, revenue_at_risk="$3.8M", affected_users=75000, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "19:40", "title": "RECALL SCOPE DEBATE", "description": "CEO and Operations debate global recall vs targeted replacement. Global recall has high immediate cost.", "module": "EXEC_BOARD", "severity": "high"},
                audit_log={"timestamp": "19:40:02", "agent": "CEO_ALPHA", "action": "POLL_BOARD", "details": "Requesting vote on product recall scope."},
                debate_messages=[
                    {"sender": "Operations Core", "role": "CISO", "timestamp": "19:40:12", "content": "Safety first. We must issue a full global recall. Targeted replacements leave high risk units active in EU and APAC.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "19:40:35", "content": "A global recall is financially destructive. Let's do a targeted swap for active commercial nodes and run firmware throttling on residential devices.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "19:41:00", "content": "Risk of thermal issue is critical. Operator, do we execute a global product recall or a targeted replacement swap?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "Recall notification packages drafted. Regulators notified."},
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Recall financial impact report ready. Awaiting vote."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO advises global safety recall to protect consumer trust."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises targeted replacement swap to minimize EBITDA hit."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Coordinating recall authorization. Awaiting choice."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=10, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "20:00", "title": "GLOBAL recall INITIATED", "description": "Consensus approved. Full global recall launched. Customers notified. Defect contained.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "20:00:20", "agent": "PR_Agent", "action": "RELEASE_NOTICE", "details": "Global safety recall notification published."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=35, revenue_at_risk="$1.0M", affected_users=25000, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "20:00", "title": "TARGETED SWAP EXECUTED", "description": "Targeted swap active. Firmware patch throttled residential devices. Cost minimized, safety risk remains.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "20:00:25", "agent": "ops", "action": "EXECUTE_SWAP", "details": "Recall restricted to lot #412-Commercial units."}
            )
        }
    ),

    # Scenario 8: Large Scale Financial Fraud
    "INC-008": ScenarioDefinition(
        id="INC-008",
        title="Large Scale Financial Fraud",
        severity="Critical",
        description="Suspicious transactions detected across multiple accounts.",
        estimated_impact="1,200 suspicious transactions, $4.2M exposure.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-008",
            "incident_type": "Financial Fraud",
            "severity": "Critical",
            "suspected_transactions": 1200,
            "estimated_exposure": 4200000
        },
        shutdown_label="FREEZE TRANSACTIONS",
        isolation_label="OBSERVE & REPORT",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=65, revenue_at_risk="$1.0M", affected_users=120, nodes_compromised=2, active_incidents=10,
                timeline_event={"time": "21:05", "title": "FRAUD PATTERN DETECTED", "description": "Finance Agent flags automated multi-account structured transactions bypassing daily limits.", "module": "FINANCE_DEPT", "severity": "medium"},
                audit_log={"timestamp": "21:05:15", "agent": "Finance_Agent", "action": "FLAG_ACCOUNTS", "details": "Detected 1,200 transactions with structured signature."},
                agent_update=[
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Structured payments bypassing daily API limits flagged on gateway."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Tracing originating transaction requests and authentication tokens."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=80, revenue_at_risk="$2.5M", affected_users=450, nodes_compromised=5, active_incidents=24,
                timeline_event={"time": "21:15", "title": "GATEWAY EXPOSURE VERIFIED", "description": "Security Agent discovers compromised database credentials utilized to authorize transactions.", "module": "SECURITY_OPS", "severity": "high"},
                audit_log={"timestamp": "21:15:30", "agent": "Security_Agent", "action": "TRACE_CREDENTIALS", "details": "Compromised billing API key found in request headers."},
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Transaction logging mode set to verbosity level 3."},
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "Compromised billing API key verified in transaction headers."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Reviewing FinCEN SAR filing thresholds and compliance rules."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=92, revenue_at_risk="$4.2M", affected_users=1200, nodes_compromised=5, active_incidents=24,
                timeline_event={"time": "21:30", "title": "SAR FILING MANDATED", "description": "Legal Agent reports compliance obligation to file a Suspicious Activity Report (SAR) with FinCEN.", "module": "LEGAL_SHIELD", "severity": "critical"},
                audit_log={"timestamp": "21:30:45", "agent": "Legal_Agent", "action": "PREPARE_SAR", "details": "Drafting FinCEN Form 111."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Compromised billing token revoked. Firewall rules updated."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "FinCEN Suspicious Activity Report (SAR) Form 111 drafted."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "Calculating total exposure value. Restructuring gateway limits."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=94, revenue_at_risk="$4.2M", affected_users=1200, nodes_compromised=5, active_incidents=24,
                timeline_event={"time": "21:40", "title": "BOARD ACTION DEBATE", "description": "Board debates freezing all suspected transactions immediately vs observing transfers to trace destination nodes.", "module": "EXEC_BOARD", "severity": "critical"},
                audit_log={"timestamp": "21:40:02", "agent": "CEO_ALPHA", "action": "POLL_BOARD", "details": "Polling on immediate account freeze vs transaction tracking."},
                debate_messages=[
                    {"sender": "Financial Auditor", "role": "Finance", "timestamp": "21:40:12", "content": "Freeze transactions immediately. We have $4.2M exposed. Any delay is a direct liability to the balance sheet.", "sentiment": "critical"},
                    {"sender": "Risk Assessment", "role": "CFO", "timestamp": "21:40:35", "content": "If we freeze, we alert the syndicate. We should log transaction flows silently for another hour to map the target endpoints.", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "21:41:00", "content": "This decision impacts FinCEN audits. Operator, do we freeze transaction processing or observe and report?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "FinCEN submission packages ready. Compliance audit logs sealed."},
                    {"id": "cfo", "status": "SLEEPING", "lastMessage": "Restructured transaction cap policies drafted. Waiting for vote."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends freezing all financial transactions immediately."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises observing funds to trace destination networks."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Reviewing FinCEN SAR filing compliance. Awaiting choice."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=10, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "22:00", "title": "TRANSACTIONS FROZEN", "description": "Consensus approved. Financial gateway frozen. Billing API credentials recycled. Leak contained.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "22:00:20", "agent": "Finance_Agent", "action": "FREEZE_API", "details": "Suspended billing token billing_key_live_512."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=45, revenue_at_risk="$1.5M", affected_users=1200, nodes_compromised=3, active_incidents=8,
                timeline_event={"time": "22:00", "title": "MONITORING SYSTEM DEPLOYED", "description": "Observed transactions. Syndicate siphoned $1.5M before endpoint block. Detailed routing report compiled.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "22:00:25", "agent": "Security_Agent", "action": "LOG_ROUTING", "details": "Traced funds to Cayman holding addresses."}
            )
        }
    ),

    # Scenario 9: Supply Chain Disruption
    "INC-009": ScenarioDefinition(
        id="INC-009",
        title="Global Supply Chain Failure",
        severity="High",
        description="Critical supplier unable to fulfill commitments.",
        estimated_impact="3 key suppliers affected, 21 days delay.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-009",
            "incident_type": "Supply Chain",
            "severity": "High",
            "suppliers_affected": 3,
            "production_delay_days": 21
        },
        shutdown_label="HALT PRODUCTION",
        isolation_label="AIR FREIGHT SOURCE",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=40, revenue_at_risk="$400K", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "22:05", "title": "PORT FORCE MAJEURE", "description": "Operations Agent flags port strike halting 3 major semiconductor supplier shipments.", "module": "LOGISTICS_SYS", "severity": "medium"},
                audit_log={"timestamp": "22:05:12", "agent": "Operations_Agent", "action": "CHECK_SHIPPINGS", "details": "Vessel carrier delayed indefinitely at Port of Long Beach."},
                agent_update=[
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Port strike halts 3 carrier shipments containing semiconductors."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Auditing hardware vendor supply authenticity hashes."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=65, revenue_at_risk="$1.2M", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "22:15", "title": "PRODUCTION DELAY ASSESSED", "description": "Operations Agent reports 21-day production delay unless local supplier backups are utilized.", "module": "SUPPLY_ANALYSIS", "severity": "medium"},
                audit_log={"timestamp": "22:15:30", "agent": "ops", "action": "CALC_DELAY", "details": "Factory backlog will reach 15,000 units by day 7."},
                agent_update=[
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Supply shipment logs stored in database."},
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "Vendor integrity verified. Disruption purely logistical."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Modeling delay penalty charges and assembly downtime."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=78, revenue_at_risk="$2.4M", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "22:30", "title": "REVENUE IMPACT ESTIMATED", "description": "Finance Agent models $2.4M customer delivery penalty charges due to contract SLA delays.", "module": "FINANCE_DEPT", "severity": "high"},
                audit_log={"timestamp": "22:30:45", "agent": "Finance_Agent", "action": "CALC_PENALTY", "details": "Model accounts for contract breach SLAs with enterprise clients."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Vendor audit trail sealed. No threat active."},
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Contract SLA delay penalty modeled at $2.4M after 14 days."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "Reviewing Force Majeure contract clauses and SLAs."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=82, revenue_at_risk="$2.4M", affected_users=0, nodes_compromised=0, active_incidents=1,
                timeline_event={"time": "22:40", "title": "SUPPLY CHAIN DEBATE", "description": "Board debates paying a 3x premium for air freight alternative semiconductor supplies vs halting production.", "module": "EXEC_BOARD", "severity": "high"},
                audit_log={"timestamp": "22:40:02", "agent": "CEO_ALPHA", "action": "POLL_BOARD", "details": "Reviewing air freight vs factory shutdown costs."},
                debate_messages=[
                    {"sender": "Operations Core", "role": "CISO", "timestamp": "22:40:12", "content": "We must source alternative semiconductors. Sourcing them locally via air freight prevents production line shutdown, saving customer trust.", "sentiment": "alert"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "22:40:35", "content": "Air freight at 3x premium wipes out Q3 profit margins entirely. Halting production for 21 days and invoking Force Majeure is cheaper.", "sentiment": "critical"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "22:41:00", "content": "We need to balance safety and budget. Operator, do we halt production or pay the air freight premium?", "sentiment": "neutral"}
                ],
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "SLA penalty models finalized. Waiting for decision."},
                    {"id": "legal", "status": "SLEEPING", "lastMessage": "Force Majeure filing packages prepared for legal counsel."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends emergency assembly halt to protect capital."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO recommends paying air freight premium to keep lines active."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Evaluating manufacturing budget and client delivery window."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=30, revenue_at_risk="$800K", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "23:00", "title": "PRODUCTION HALTED", "description": "Consensus approved. Production line halted. Force Majeure invoked. Customer SLAs paused.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "23:00:20", "agent": "CEO_ALPHA", "action": "HALT_ASSEMBLY", "details": "Manufacturing facility locked down. Staff sent to maintenance shift."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=15, revenue_at_risk="$0", affected_users=0, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "23:00", "title": "AIR FREIGHT LAUNCHED", "description": "Alternative sourcing approved. Semiconductor parts air shipped. Production resumed.", "module": "EXECUTIVE_DECISION", "severity": "low"},
                audit_log={"timestamp": "23:00:25", "agent": "ops", "action": "AIR_FREIGHT", "details": "Alternative supply contract signed with local supplier."}
            )
        }
    ),

    # Scenario 10: Ultimate Multi-Crisis Event (Flagship Demo)
    "INC-010": ScenarioDefinition(
        id="INC-010",
        title="Enterprise Perfect Storm",
        severity="Maximum",
        description="Simultaneous cyberattack, cloud outage, compliance violation, and PR crisis.",
        estimated_impact="Simultaneous collapse across all core business sectors.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": "INC-010",
            "incident_type": "Multi-Crisis",
            "severity": "Maximum",
            "events": ["Data Breach", "Cloud Outage", "GDPR Violation", "Social Media Crisis"]
        },
        shutdown_label="EMERGENCY LOCKDOWN",
        isolation_label="SEGMENT CONTAINMENT",
        steps=[
            CrisisScenarioStep(
                step_name="DETECTION", risk_score=85, revenue_at_risk="$3.5M", affected_users=80000, nodes_compromised=15, active_incidents=5,
                timeline_event={"time": "00:01", "title": "MULTI-VECTOR ALARMS DETECTED", "description": "Master Crisis Room spawned. Simultaneous DDoS, data leaks, and us-east-1 regional failure detected.", "module": "MASTER_COMMAND", "severity": "critical"},
                audit_log={"timestamp": "00:01:05", "agent": "Detection_Agent", "action": "SPAWN_WAR_ROOMS", "details": "Created Master Room and spawned sub-war rooms #SUB-01, #SUB-02."},
                agent_update=[
                    {"id": "detection", "status": "ACTIVE", "lastMessage": "Simultaneous DDoS and data leak alarms active on core subnet."},
                    {"id": "sec", "status": "THINKING", "lastMessage": "Scanning network layers. Multi-vector breach active."},
                    {"id": "infra", "status": "THINKING", "lastMessage": "AWS us-east-1 routing table degradation detected."}
                ]
            ),
            CrisisScenarioStep(
                step_name="INVESTIGATION", risk_score=95, revenue_at_risk="$8.2M", affected_users=350000, nodes_compromised=48, active_incidents=14,
                timeline_event={"time": "00:15", "title": "CROSS-ROOM AGENT COLLABORATION", "description": "All agents join Band channels. Security traces ransomware lateral shifts while Infra attempts failover.", "module": "BAND_SDK", "severity": "critical"},
                audit_log={"timestamp": "00:15:30", "agent": "Security_Agent", "action": "CORRELATE_THREAT", "details": "Correlated SQL injection exfiltration with DDoS traffic masking."},
                agent_update=[
                    {"id": "detection", "status": "SLEEPING", "lastMessage": "DDoS telemetry forwarded to security team. Active monitor."},
                    {"id": "sec", "status": "ACTIVE", "lastMessage": "Correlating SQL exfiltration with masking DDoS traffic. Containment live."},
                    {"id": "infra", "status": "ACTIVE", "lastMessage": "Database locked. Traffic failover failed due to network blocks."},
                    {"id": "finance", "status": "THINKING", "lastMessage": "Auditing all active billing gateways and regional conversions."},
                    {"id": "cx", "status": "THINKING", "lastMessage": "Tracing customer checkout errors and high packet drop counts."}
                ]
            ),
            CrisisScenarioStep(
                step_name="RISK_LEGAL", risk_score=99, revenue_at_risk="$12.5M", affected_users=800000, nodes_compromised=124, active_incidents=32,
                timeline_event={"time": "00:30", "title": "REGULATORY & REPUTATIONAL COLLAPSE", "description": "GDPR compliance status degraded to non-compliant. Viral social hashtags reach 5,000,000 users. Loss models display $12M at risk.", "module": "LEGAL_SHIELD", "severity": "critical"},
                audit_log={"timestamp": "00:30:45", "agent": "Risk_Agent", "action": "CALC_AGGREGATE_LOSS", "details": "Aggregate hourly loss is calculated at $42.5M/hr if offline."},
                agent_update=[
                    {"id": "sec", "status": "SLEEPING", "lastMessage": "Subnet isolation rules configured. Traps active."},
                    {"id": "infra", "status": "SLEEPING", "lastMessage": "Failover routing suspended pending Board order."},
                    {"id": "finance", "status": "ACTIVE", "lastMessage": "Aggregate loss modeled at $42.5M/hr if offline. High risk."},
                    {"id": "cx", "status": "ACTIVE", "lastMessage": "500k customer records exposed. Brand sentiment at critical levels."},
                    {"id": "legal", "status": "THINKING", "lastMessage": "GDPR compliance status degraded. 72h notification window active."},
                    {"id": "pr", "status": "THINKING", "lastMessage": "Drafting global multi-channel holding statements."}
                ]
            ),
            CrisisScenarioStep(
                step_name="DEBATE_ACTIVE", risk_score=100, revenue_at_risk="$12.5M", affected_users=800000, nodes_compromised=124, active_incidents=32,
                timeline_event={"time": "00:40", "title": "JOINT EMERGENCY DEBATE ACTIVE", "description": "Joint emergency board session. All executive agents debating absolute corporate shutdown vs segmented container battle.", "module": "EXEC_BOARD", "severity": "critical"},
                audit_log={"timestamp": "00:40:02", "agent": "CEO_ALPHA", "action": "VOTE_LOCKDOWN", "details": "Calling for final vote: Complete lockdown vs Segmented battle."},
                debate_messages=[
                    {"sender": "CISO_SHIELD", "role": "CISO", "timestamp": "00:40:11", "content": "This is the perfect storm. The exfiltration is crossing all subnet borders. I recommend an immediate COMPLETE ENTERPRISE LOCKDOWN. Cut all internet connectivity.", "sentiment": "critical"},
                    {"sender": "CTO_NODAL", "role": "CISO", "timestamp": "00:40:25", "content": "A complete lockdown means shutting down all servers, factories, and VPNs globally. Recovery will take weeks. We must fight segment-by-segment.", "sentiment": "critical"},
                    {"sender": "CFO_QUANT", "role": "CFO", "timestamp": "00:40:40", "content": "Global shutdown drops our active transactions to zero. That represents a $50M daily balance sheet hit. Can we survive a segmented battle?", "sentiment": "alert"},
                    {"sender": "CEO_ALPHA", "role": "CEO", "timestamp": "00:41:00", "content": "Operator, the Board is split. The future of the enterprise is in your hands. Complete lockdown or segmented containment?", "sentiment": "critical"}
                ],
                agent_update=[
                    {"id": "finance", "status": "SLEEPING", "lastMessage": "Aggregate loss model finalized. Awaiting board decision."},
                    {"id": "cx", "status": "SLEEPING", "lastMessage": "Customer exposure database sealed. Press office notified."},
                    {"id": "legal", "status": "ACTIVE", "lastMessage": "GDPR disclosure packages finalized. Ready for submission."},
                    {"id": "pr", "status": "ACTIVE", "lastMessage": "Press hold templates ready for distribution pending Board action."},
                    {"id": "ciso", "status": "THINKING", "lastMessage": "CISO recommends immediate global database lockdown."},
                    {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises segmented defense to protect transaction revenue."},
                    {"id": "ceo", "status": "THINKING", "lastMessage": "Coordinating emergency perfect storm response. Awaiting choice."}
                ]
            )
        ],
        resolutions={
            "SHUTDOWN": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=18, revenue_at_risk="$0", affected_users=800000, nodes_compromised=0, active_incidents=0,
                timeline_event={"time": "01:00", "title": "EMERGENCY LOCKDOWN EXECUTED", "description": "C-Suite consensus: COMPLETE GLOBAL LOCKDOWN executed. All connections severed. Threat contained.", "module": "EXECUTIVE_DECISION", "severity": "medium"},
                audit_log={"timestamp": "01:00:15", "agent": "CTO_NODAL", "action": "POWER_DOWN", "details": "All DNS nodes dereferenced. Active routing tables wiped. VPN links offline."}
            ),
            "ISOLATION": CrisisScenarioStep(
                step_name="RESOLVED", risk_score=55, revenue_at_risk="$4.8M", affected_users=800000, nodes_compromised=12, active_incidents=3,
                timeline_event={"time": "01:00", "title": "SEGMENTED DEFENSE ACTIVE", "description": "Segmented defense executed. Main transactions online, but active threats continue in internal subnet segments.", "module": "EXECUTIVE_DECISION", "severity": "high"},
                audit_log={"timestamp": "01:00:22", "agent": "Security_Agent", "action": "CONTAIN_SEGMENT", "details": "Quarantined 14 subnets. Tracing remaining active exfiltration points."}
            )
        }
    )
}


def get_resolution_step(decision: str, scenario_id: str = "INC-001") -> CrisisScenarioStep:
    scenario = SCENARIOS.get(scenario_id, SCENARIOS["INC-001"])
    return scenario.resolutions.get(decision, scenario.resolutions["SHUTDOWN"])
