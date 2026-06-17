'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  status: 'IDLE' | 'THINKING' | 'DELEGATING' | 'ACTIVE' | 'SLEEPING';
  lastMessage: string;
  tags: string[];
}

export interface DebateMessage {
  sender: string;
  role: string;
  timestamp: string;
  content: string;
  sentiment: 'neutral' | 'critical' | 'alert' | 'success';
}

export interface TimelineEvent {
  time: string;
  title: string;
  description: string;
  module: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AuditLog {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  details: string;
}

export interface AlertInfo {
  id: string;
  timestamp: string;
  source: string;
  event_type: string;
  severity: string;
  title: string;
  description: string;
  status: string;
}

export interface RegionalStatus {
  name: string;
  status: 'OPTIMAL' | 'DEGRADED' | 'CRITICAL';
}

export interface CommandCenterState {
  scenarioState: 'INITIAL' | 'DETECTION' | 'INVESTIGATION' | 'RISK_LEGAL' | 'DEBATE_ACTIVE' | 'DECISION_TAKEN' | 'RECOVERY' | 'RESOLVED';
  scenarioId?: string;
  scenarioTitle?: string;
  severity: 'OPTIMAL' | 'ALPHA' | 'OMEGA' | 'P1';
  riskScore: number;
  revenueAtRisk: string;
  affectedUsers: number;
  nodesCompromised: number;
  activeIncidentsCount: number;
  regionalStatus: RegionalStatus[];
  timeline: TimelineEvent[];
  agents: AgentInfo[];
  debate: DebateMessage[];
  auditLogs: AuditLog[];
  decisionMatrix: {
    vector: string;
    shutdownScore: number;
    isolateScore: number;
  }[];
  postMortem: {
    rootCause: string;
    timelineAnalysis: string;
    businessImpact: string;
    complianceReport: string;
    lessonsLearned: string;
    preventionPlan: string;
  } | null;
  shutdownLabel?: string;
  isolationLabel?: string;
  simulationRunning: boolean;
  receivedAlerts?: AlertInfo[];
}

interface CommandCenterContextType {
  state: CommandCenterState;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  startDemo: () => void;
  startScenario: (scenarioId: string) => void;
  deployCountermeasures: (decision: 'SHUTDOWN' | 'ISOLATION') => void;
  resetDemo: () => void;
  focusOnAlert: (alert: AlertInfo) => void;
  apiBase: string;
  apiKey: string;
}

const initialStates: CommandCenterState = {
  scenarioState: 'INITIAL',
  scenarioId: 'INC-001',
  scenarioTitle: 'Customer Database Breach',
  severity: 'OPTIMAL',
  riskScore: 0,
  revenueAtRisk: '$0',
  affectedUsers: 0,
  nodesCompromised: 0,
  activeIncidentsCount: 0,
  regionalStatus: [
    { name: 'US-EAST-1', status: 'OPTIMAL' },
    { name: 'EU-WEST-2', status: 'OPTIMAL' },
    { name: 'AP-SOUTH-1', status: 'OPTIMAL' },
    { name: 'SA-EAST-1', status: 'OPTIMAL' }
  ],
  timeline: [],
  agents: [
    { id: 'detection', name: 'Threat Detection & Sentinel', role: 'IDS_Sentinel', status: 'IDLE', lastMessage: 'Scanning network logs and integrity hashes.', tags: ['LOG_ANALYZE', 'INTEGRITY_CHECK'] },
    { id: 'sec', name: 'Cyber Threat Containment Agent', role: 'Security_v4', status: 'IDLE', lastMessage: 'Monitoring traffic for signs of lateral intrusion.', tags: ['THREAT_HUNT', 'DEEP_SCAN'] },
    { id: 'infra', name: 'Cloud Infrastructure & Failover Architect', role: 'Infra_Link', status: 'IDLE', lastMessage: 'All system clusters active and balancing load.', tags: ['DNS_SHIFT', 'FAILOVER'] },
    { id: 'legal', name: 'Data Protection & Legal Compliance Shield', role: 'Legal_Mind', status: 'IDLE', lastMessage: 'Compliance scanning GDPR/CCPA regulations.', tags: ['GDPR_ART33', 'LIABILITY'] },
    { id: 'finance', name: 'Revenue Loss & Transaction Risk Auditor', role: 'Finance_Flow', status: 'IDLE', lastMessage: 'Monitoring liquidity pools and billing APIs.', tags: ['REVENUE_RISK', 'TX_AUDIT'] },
    { id: 'cx', name: 'Telemetry & Customer Churn Analyst', role: 'User_Telemetry', status: 'IDLE', lastMessage: 'Analyzing customer churn risk and active session drop-offs.', tags: ['CX_MONITOR', 'CHURN_PREDICT'] },
    { id: 'pr', name: 'Public Relations & Crisis Communications Officer', role: 'Comm_Ops', status: 'IDLE', lastMessage: 'Press hold templates ready.', tags: ['STMT_A1', 'PRESS_WIRE'] },
    { id: 'ciso', name: 'Chief Information Security Officer Agent', role: 'CISO', status: 'IDLE', lastMessage: 'Enforcing data protection policies.', tags: ['COMPLIANCE_GOV', 'SECURITY_POL'] },
    { id: 'cfo', name: 'Chief Financial Risk Strategist', role: 'CFO', status: 'IDLE', lastMessage: 'Analyzing cost structures and revenue lines.', tags: ['LIQUIDITY', 'LOSS_PREVENT'] },
    { id: 'ceo', name: 'Chief Executive Decision Agent', role: 'CEO', status: 'IDLE', lastMessage: 'Overseeing operational alignment and decision vectors.', tags: ['EXEC_AUTHORITY', 'STRATEGY'] }
  ],
  debate: [],
  auditLogs: [],
  decisionMatrix: [
    { vector: 'Security Risk', shutdownScore: 100, isolateScore: 28 },
    { vector: 'Revenue Impact', shutdownScore: 10, isolateScore: 85 },
    { vector: 'Recovery Time', shutdownScore: 30, isolateScore: 90 },
    { vector: 'Compliance Rating', shutdownScore: 95, isolateScore: 40 }
  ],
  postMortem: null,
  shutdownLabel: 'EXECUTE SHUTDOWN',
  isolationLabel: 'ATTEMPT ISOLATION',
  simulationRunning: false,
  receivedAlerts: [],
};

const CommandCenterContext = createContext<CommandCenterContextType | undefined>(undefined);

// Build agent lookup from initialStates to avoid duplicate data
const LOCAL_AGENTS_DB: Record<string, AgentInfo> = Object.fromEntries(
  initialStates.agents.map(a => [a.id, a])
);

// Scenarios Offline specifications
const LOCAL_SCENARIOS_DATA: Record<string, {
  title: string;
  severity: 'OPTIMAL' | 'ALPHA' | 'OMEGA' | 'P1';
  description: string;
  shutdownLabel: string;
  isolationLabel: string;
  agentsInvolved: string[];
  steps: {
    delay: number;
    update: (prev: CommandCenterState) => CommandCenterState;
  }[];
  postMortemGen: (decision: string) => NonNullable<CommandCenterState['postMortem']>;
}> = {
  "INC-001": {
    title: "Customer Database Breach",
    severity: "OMEGA",
    description: "Unauthorized SQL queries found on Customer PostgreSQL.",
    shutdownLabel: "EXECUTE SHUTDOWN",
    isolationLabel: "ATTEMPT ISOLATION",
    agentsInvolved: ["detection", "sec", "infra", "legal", "finance", "cx", "pr", "ciso", "cfo", "ceo"],
    postMortemGen: (decision) => ({
      rootCause: "PostgreSQL SQL Injection vulnerability in customer data access layer.",
      timelineAnalysis: `08:01 Initial access -> 08:11 Detection -> 08:40 C-suite debate -> 09:00 ${decision === 'SHUTDOWN' ? 'Full Shutdown' : 'Segment Isolation'} implemented.`,
      businessImpact: decision === 'SHUTDOWN' ? "Est: $3.8M revenue lost during 4h downtime." : "Est: $800k revenue lost, GDPR violation exposure potential.",
      complianceReport: "GDPR Article 33 notifications drafted.",
      lessonsLearned: "SQL queries must be fully parameterized.",
      preventionPlan: "Implement automated WAF rules and microsegmentation."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 70, revenueAtRisk: '$1.2M', affectedUsers: 25000, nodesCompromised: 2, activeIncidentsCount: 1,
          timeline: [{ time: '08:11', title: 'BREACH DETECTED', description: 'Unauthorized external queries found on Customer DB.', module: 'INCIDENT_SYS', severity: 'critical' }],
          agents: prev.agents.map(a => {
            if (a.id === 'detection') return { ...a, status: 'ACTIVE', lastMessage: 'ALERT: SQL Injection pattern detected on Customer PostgreSQL.' };
            if (a.id === 'sec') return { ...a, status: 'THINKING', lastMessage: 'Tracing active database connection logs and queries.' };
            if (a.id === 'infra') return { ...a, status: 'THINKING', lastMessage: 'Analyzing CPU spikes and network logs on DB clusters.' };
            return a;
          }),
          auditLogs: [{ id: '1', timestamp: '08:11:04', agent: 'Detection_Agent', action: 'CREATE_ROOM', details: 'War room created for PostgreSQL breach.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 85, revenueAtRisk: '$2.8M', affectedUsers: 95000, nodesCompromised: 4, activeIncidentsCount: 3,
          timeline: [...prev.timeline, { time: '08:15', title: 'THREAT TRACED', description: 'SQL injection confirmed. Exfiltration at 45GB/s.', module: 'BAND_SDK', severity: 'critical' }],
          agents: prev.agents.map(a => {
            if (a.id === 'detection') return { ...a, status: 'SLEEPING', lastMessage: 'Alert handoff confirmed. System telemetry monitoring active.' };
            if (a.id === 'sec') return { ...a, status: 'ACTIVE', lastMessage: 'SQL injection verified. Source IP: 185.220.101.4. Tracing exfiltration rates.' };
            if (a.id === 'infra') return { ...a, status: 'ACTIVE', lastMessage: 'Isolating database subnet G-9. Diverting operational API traffic.' };
            if (a.id === 'finance') return { ...a, status: 'THINKING', lastMessage: 'Auditing active billing APIs and calculating conversion drop rates.' };
            if (a.id === 'cx') return { ...a, status: 'THINKING', lastMessage: 'Scanning active customer checkout drop-offs and session timeouts.' };
            return a;
          }),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '08:15:12', agent: 'Security_Agent', action: 'LOG_IOC', details: 'Vulnerability vector logged.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 94, revenueAtRisk: '$4.2M', affectedUsers: 150000, nodesCompromised: 6, activeIncidentsCount: 7,
          regionalStatus: [{ name: 'US-EAST-1', status: 'CRITICAL' }, { name: 'EU-WEST-2', status: 'DEGRADED' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '08:30', title: 'GDPR OBLIGATIONS ACTIVE', description: 'Sensitive EU data involved. 72h notification window triggered.', module: 'LEGAL_SHIELD', severity: 'critical' }],
          agents: prev.agents.map(a => {
            if (a.id === 'sec') return { ...a, status: 'SLEEPING', lastMessage: 'Containment pending C-suite command. Network traps configured.' };
            if (a.id === 'infra') return { ...a, status: 'SLEEPING', lastMessage: 'Traffic diverted. Secondary subnets operating on backup routes.' };
            if (a.id === 'finance') return { ...a, status: 'ACTIVE', lastMessage: 'Revenue risk verified: $4.2M. Transaction conversion down 35%.' };
            if (a.id === 'cx') return { ...a, status: 'ACTIVE', lastMessage: '150,000 active EU customer accounts identified in scope of exposure.' };
            if (a.id === 'legal') return { ...a, status: 'THINKING', lastMessage: 'Analyzing GDPR Article 33 notifications and liability thresholds.' };
            if (a.id === 'pr') return { ...a, status: 'THINKING', lastMessage: 'Preparing crisis holding statements and internal notifications.' };
            return a;
          }),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '08:30:45', agent: 'Risk_Agent', action: 'CALC_LOSS', details: 'GDPR fine could reach 4% turnover.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'OMEGA',
          debate: [
            { sender: 'CISO_SHIELD', role: 'CISO', timestamp: '08:40:11', content: 'The exfiltration of Customer PostgreSQL is ongoing. I recommend an immediate database shutdown. The risks of further exfiltration exceed any operational costs.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '08:40:29', content: 'Shutting down the database halts all customer checkout processes. That represents -$12M/hr in liquidity. I recommend partial network isolation of Segment G-9.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '08:41:00', content: 'We need to act. Operator, please select whether to execute a full database shutdown or attempt network isolation.', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '08:40', title: 'C-SUITE WAR ROOM ACTIVE', description: 'Executive board debating response in Band room.', module: 'EXEC_BOARD', severity: 'critical' }],
          agents: prev.agents.map(a => {
            if (a.id === 'legal') return { ...a, status: 'ACTIVE', lastMessage: 'Compliance disclosure package finalized. EDPB ready for submit.' };
            if (a.id === 'pr') return { ...a, status: 'ACTIVE', lastMessage: 'Hold statement templates ready for distribution pending Board action.' };
            if (a.id === 'ciso') return { ...a, status: 'THINKING', lastMessage: 'CISO recommends immediate database shutdown to prevent further leaks.' };
            if (a.id === 'cfo') return { ...a, status: 'THINKING', lastMessage: 'CFO advises isolation over shutdown to prevent $12M/hr business loss.' };
            if (a.id === 'ceo') return { ...a, status: 'THINKING', lastMessage: 'Coordinating crisis command votes. Ready for operator input.' };
            return a;
          })
        })
      }
    ]
  },
  "INC-002": {
    title: "Regional Cloud Outage",
    severity: "ALPHA",
    description: "AWS us-east-1 connection dropped. Payment API failing.",
    shutdownLabel: "FAILOVER TO WEST",
    isolationLabel: "LOCAL RECOVERY",
    agentsInvolved: ["infra", "finance", "cx", "ceo", "cfo", "ciso"],
    postMortemGen: (decision) => ({
      rootCause: "EBS volume degradation lockup in AWS us-east-1.",
      timelineAnalysis: `10:05 Anomaly -> 10:15 Diagnostics complete -> 10:35 Debate -> 10:50 ${decision === 'SHUTDOWN' ? 'Failover' : 'Local Restart'} complete.`,
      businessImpact: decision === 'SHUTDOWN' ? "Est: $0 revenue loss after failover window." : "Est: $800k revenue loss due to degraded nodes.",
      complianceReport: "No data compliance breach detected.",
      lessonsLearned: "Build automated active-active failover mechanisms.",
      preventionPlan: "Distribute service pods across us-east-1 and us-west-2."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 55, revenueAtRisk: '$500K', affectedUsers: 18000, nodesCompromised: 1, activeIncidentsCount: 2,
          timeline: [{ time: '10:05', title: 'SERVICE HEALTH DROP', description: 'Payment API response times exceeded 15000ms. High packet loss detected in AWS us-east-1.', module: 'INFRA_MONITOR', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'THINKING', lastMessage: 'Checking cluster ping response.' } : a),
          auditLogs: [{ id: '1', timestamp: '10:05:30', agent: 'infra', action: 'POLL_PING', details: 'Health checks failing for load balancer nodes in us-east-1a.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 75, revenueAtRisk: '$1.8M', affectedUsers: 62000, nodesCompromised: 4, activeIncidentsCount: 4,
          timeline: [...prev.timeline, { time: '10:15', title: 'AWS NETWORK CORRUPTION', description: 'CISO identifies corrupted routing tables and EBS locks in us-east-1.', module: 'CTO_OFFICE', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'ACTIVE', lastMessage: 'Diagnostic complete: volumes locked.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '10:15:44', agent: 'ciso', action: 'DIAGNOSE_OUTAGE', details: 'AWS API endpoints reporting 503 errors.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 88, revenueAtRisk: '$2.9M', affectedUsers: 120000, nodesCompromised: 5, activeIncidentsCount: 5,
          regionalStatus: [{ name: 'US-EAST-1', status: 'CRITICAL' }, { name: 'EU-WEST-2', status: 'OPTIMAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '10:25', title: 'REVENUE LOSS MTG', description: 'Outage is blocking checkout flows. Cumulative losses growing.', module: 'FINANCE_DEPT', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'finance' ? { ...a, status: 'THINKING', lastMessage: 'Modeling checkout failure rates.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '10:25:12', agent: 'finance', action: 'CALC_LOSS', details: 'Estimated loss mounting at $40K/min.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'ALPHA',
          debate: [
            { sender: 'CTO_NODAL', role: 'CTO', timestamp: '10:35:12', content: 'us-east-1 is fully unresponsive. We must trigger a FAILOVER TO WEST immediately to restore Payment API stability.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '10:35:30', content: 'A failover sync will trigger a 15-minute window of complete data inconsistency. Can we attempt local recovery or wait for AWS?', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '10:36:00', content: 'We cannot wait for AWS. Operator, make the call: failover to us-west-2 or attempt local database sync?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '10:35', title: 'FAILOVER DEBATE', description: 'Board debates routing traffic to us-west-2 vs local container restarts.', module: 'EXEC_BOARD', severity: 'high' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-003": {
    title: "Enterprise Ransomware Incident",
    severity: "OMEGA",
    description: "LockBit 3.0 ransomware detected on corporate desktops.",
    shutdownLabel: "REBUILD BACKUPS",
    isolationLabel: "PAY THE RANSOM",
    agentsInvolved: ["sec", "legal", "finance", "ceo", "ciso", "pr"],
    postMortemGen: (decision) => ({
      rootCause: "Compromised Edge Gateway VPN credentials used to deploy Ransomware payload.",
      timelineAnalysis: `11:10 Detection -> 11:25 Backups check -> 11:40 Sanctions check -> 12:15 ${decision === 'SHUTDOWN' ? 'Rebuild' : 'Pay Ransom'} completed.`,
      businessImpact: decision === 'SHUTDOWN' ? "Offline rebuild. Defused ransom, compliance safe." : "Paid $500K. Decrypted nodes slowly, high audit scrutiny.",
      complianceReport: "Compliance verified under OFAC guidelines.",
      lessonsLearned: "VPN endpoints must require hardware MFA.",
      preventionPlan: "Deploy sentinel monitoring agent on all endpoints."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 80, revenueAtRisk: '$2.0M', affectedUsers: 5000, nodesCompromised: 45, activeIncidentsCount: 3,
          timeline: [{ time: '11:10', title: 'MASS ENCRYPTION DETECTED', description: "Ransomware signature 'LockBit 3.0' active on corporate desktops.", module: 'ENDPOINT_SEC', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'sec' ? { ...a, status: 'THINKING', lastMessage: 'Analyzing encryption hash.' } : a),
          auditLogs: [{ id: '1', timestamp: '11:10:15', agent: 'sec', action: 'QUARANTINE_IP', details: 'Shutting down file shares to stop spread.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 90, revenueAtRisk: '$3.5M', affectedUsers: 8000, nodesCompromised: 120, activeIncidentsCount: 12,
          timeline: [...prev.timeline, { time: '11:25', title: 'SHADOW COPIES DELETED', description: 'Attackers purged local system restore shadow copies.', module: 'RECOVERY_OPS', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'ACTIVE', lastMessage: 'Auditing offline tape backups.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '11:25:33', agent: 'infra', action: 'AUDIT_BACKUPS', details: 'Cold storage tapes remain uncompromised.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 95, revenueAtRisk: '$4.8M', affectedUsers: 12000, nodesCompromised: 320, activeIncidentsCount: 20,
          regionalStatus: [{ name: 'US-EAST-1', status: 'CRITICAL' }, { name: 'EU-WEST-2', status: 'CRITICAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '11:40', title: 'LEGAL SANCTION WARNING', description: 'Paying hacker wallet may violate sanctions compliance.', module: 'LEGAL_SHIELD', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'legal' ? { ...a, status: 'THINKING', lastMessage: 'Verifying sanctions databases.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '11:40:02', agent: 'legal', action: 'CHECK_OFAC', details: 'Checking Bitcoin address against OFAC list.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'OMEGA',
          debate: [
            { sender: 'CISO_SHIELD', role: 'CISO', timestamp: '11:50:20', content: 'We must never pay. Rebuilding from cold backups is the only compliant path, even if it takes 48 hours.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '11:50:45', content: '48 hours offline will cost us $5M in business outage and risk permanent customer churn. Paying the $500K is cheaper.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '11:51:10', content: 'If we pay, we violate regulatory codes. If we rebuild, the losses are massive. Operator, what is the path?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '11:50', title: 'RANSOM DEBATE ACTIVE', description: 'CISO objects to payment. CFO highlights recovery loss.', module: 'EXEC_BOARD', severity: 'critical' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-004": {
    title: "GDPR Compliance Violation",
    severity: "ALPHA",
    description: "Legacy server found retaining data past GDPR retention limits.",
    shutdownLabel: "SELF DISCLOSE",
    isolationLabel: "SILENT REMEDIATION",
    agentsInvolved: ["legal", "finance", "ceo", "cfo", "ciso"],
    postMortemGen: (decision) => ({
      rootCause: "Unpurged backup directory 'legacy_backup_2021' contained expired PII.",
      timelineAnalysis: "13:00 Found -> 13:15 Audited -> 13:30 Fine modeled -> 13:40 Board debate -> 14:00 Action complete.",
      businessImpact: decision === 'SHUTDOWN' ? "EDPB notification submitted. Legal rating protected." : "Wiped database secretly. Residual risk of discovery remains.",
      complianceReport: "Self-disclosure fully recorded. GDPR compliance logged.",
      lessonsLearned: "Automatic retention scripts must be scheduled and audited.",
      preventionPlan: "Implement automated data retention enforcement scanner."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 45, revenueAtRisk: '$0', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [{ time: '13:00', title: 'RETENTION EXPOSURE DETECTED', description: 'Compliance Agent flags legacy directory with 500,000 customer records.', module: 'COMPLIANCE_SYS', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'legal' ? { ...a, status: 'THINKING', lastMessage: 'Scanning backup retention logs.' } : a),
          auditLogs: [{ id: '1', timestamp: '13:00:10', agent: 'legal', action: 'FLAG_RECORDS', details: "Flagging legacy archive folder." }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 65, revenueAtRisk: '$1.0M', affectedUsers: 500000, nodesCompromised: 1, activeIncidentsCount: 1,
          timeline: [...prev.timeline, { time: '13:15', title: 'AUDIT VERIFICATION', description: 'CFO Agent verifies expired names and addresses are unencrypted.', module: 'RISK_CALC', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'cfo' ? { ...a, status: 'ACTIVE', lastMessage: 'Auditing data field contents.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '13:15:35', agent: 'cfo', action: 'VERIFY_DATA', details: 'PII confirmed.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 80, revenueAtRisk: '$2.5M', affectedUsers: 500000, nodesCompromised: 1, activeIncidentsCount: 1,
          regionalStatus: [{ name: 'US-EAST-1', status: 'OPTIMAL' }, { name: 'EU-WEST-2', status: 'DEGRADED' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '13:30', title: 'FINE ANALYSIS COMPILED', description: 'Finance Agent estimates potential GDPR penalty up to $2.2M.', module: 'FINANCE_DEPT', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'finance' ? { ...a, status: 'THINKING', lastMessage: 'Analyzing Article 83 parameters.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '13:30:12', agent: 'finance', action: 'ESTIMATE_FINE', details: 'Calculated baseline penalty probability.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'ALPHA',
          debate: [
            { sender: 'Compliance Shield', role: 'Legal', timestamp: '13:40:15', content: 'We must self-disclose immediately. If the regulator discovers this via audit first, the penalty will double.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '13:40:35', content: 'Self-disclosure will tank our stock price by 5%. Let\'s silently purge the records and document it as a scheduled cleanup.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '13:41:00', content: 'This is a serious governance question. Operator, do we self-disclose to the commissioner or implement a silent internal wipe?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '13:40', title: 'DISCLOSURE DEBATE ACTIVE', description: 'Board debates self-disclosure vs quiet wipe.', module: 'EXEC_BOARD', severity: 'high' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-005": {
    title: "Brand Reputation Crisis",
    severity: "ALPHA",
    description: "Trending viral hashtag claiming device shadow tracking.",
    shutdownLabel: "PUBLIC APOLOGY",
    isolationLabel: "COUNTER PROMOTION",
    agentsInvolved: ["pr", "cx", "ceo", "cfo", "legal"],
    postMortemGen: (decision) => ({
      rootCause: "Misinterpreted tracking diagnostic telemetry logs published by security researcher.",
      timelineAnalysis: "15:01 Trend noticed -> 15:15 Sentiment check -> 15:30 Churn warning -> 15:40 Debate -> 16:00 Response posted.",
      businessImpact: decision === 'SHUTDOWN' ? "Statement stabilized sentiment. 78% traffic defused." : "Counter ads deployed. Trend dropped slowly, some customer churn.",
      complianceReport: "No data violation found. Audit trail sealed.",
      lessonsLearned: "PR responses must be fast and data-backed.",
      preventionPlan: "Deploy active transparency report dashboard."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 35, revenueAtRisk: '$100K', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [{ time: '15:01', title: 'VIRAL HASHTAG DETECTED', description: 'Hashtag #CrisisCommandData trending. Allegations of customer tracking.', module: 'SOCIAL_LISTEN', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'pr' ? { ...a, status: 'THINKING', lastMessage: 'Scanning Twitter keywords.' } : a),
          auditLogs: [{ id: '1', timestamp: '15:01:15', agent: 'pr', action: 'START_MONITORING', details: 'Tracking social sentiment frequency.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 50, revenueAtRisk: '$300K', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [...prev.timeline, { time: '15:15', title: 'SENTIMENT CRASH', description: 'Brand sentiment dropped 65%. 12,000 negative posts active.', module: 'SENTIMENT_ENGINE', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'cx' ? { ...a, status: 'ACTIVE', lastMessage: 'Sentiment score dropped to 26.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '15:15:30', agent: 'cx', action: 'CALC_SENTIMENT', details: 'Brand index calculated.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 60, revenueAtRisk: '$800K', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          regionalStatus: [{ name: 'US-EAST-1', status: 'DEGRADED' }, { name: 'EU-WEST-2', status: 'OPTIMAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '15:30', title: 'CHURN RISK WARN', description: 'Potential 4% user churn if corporate response exceeds 1 hour.', module: 'RISK_CALC', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'cfo' ? { ...a, status: 'THINKING', lastMessage: 'Modeling user exit risk.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '15:30:45', agent: 'cfo', action: 'CALC_CHURN', details: 'Hourly revenue exposure modeled.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'ALPHA',
          debate: [
            { sender: 'Public Relations', role: 'PR', timestamp: '15:40:12', content: 'We need to issue a public apology immediately. Admitting the discrepancy and launching a transparency site is the only way to defuse this.', sentiment: 'alert' },
            { sender: 'Brand Marketing', role: 'Marketing', timestamp: '15:40:30', content: 'An apology validates their claims. We should run a counter-promotion highlight campaign emphasizing our security frameworks.', sentiment: 'neutral' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '15:41:00', content: 'Delay is hurting us. Operator, do we issue a public apology or launch a counter promotion campaign?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '15:40', title: 'RESPONSE STRATEGY DEBATE', description: 'PR suggests transparency apology. Marketing suggests ad campaign.', module: 'EXEC_BOARD', severity: 'medium' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-006": {
    title: "Malicious Insider Activity",
    severity: "OMEGA",
    description: "DBA credentials used for bulk data downloads.",
    shutdownLabel: "REVOKE ACCESS",
    isolationLabel: "MONITOR ACTIONS",
    agentsInvolved: ["sec", "legal", "ceo", "ciso", "pr"],
    postMortemGen: (decision) => ({
      rootCause: "Compromised credential of database administrator accessing database remotely.",
      timelineAnalysis: `17:05 Alert -> 17:15 HR check -> 17:30 IP warning -> 17:40 Debate -> 18:00 ${decision === 'SHUTDOWN' ? 'Suspended' : 'Tracked'} completed.`,
      businessImpact: decision === 'SHUTDOWN' ? "Suspended credentials. Halted exfiltration. Stolen data: 300 files." : "Tracked file hops. Traced receiver server, but files exfiltrated.",
      complianceReport: "Breach logged, law enforcement notified.",
      lessonsLearned: "Enforce automated VPN blocks on non-work hours.",
      preventionPlan: "Implement context-aware IAM access controls."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 60, revenueAtRisk: '$500K', affectedUsers: 0, nodesCompromised: 1, activeIncidentsCount: 1,
          timeline: [{ time: '17:05', title: 'SIPIHON DETECTED', description: 'DBA account siphoned 300 files at 3 AM.', module: 'FILE_AUDIT', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'sec' ? { ...a, status: 'THINKING', lastMessage: 'Scanning file hashes.' } : a),
          auditLogs: [{ id: '1', timestamp: '17:05:12', agent: 'sec', action: 'FLAG_DOWNLOAD', details: 'Anomalous volume found on user account.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 78, revenueAtRisk: '$1.2M', affectedUsers: 0, nodesCompromised: 1, activeIncidentsCount: 1,
          timeline: [...prev.timeline, { time: '17:15', title: 'HR LEAVE CHECKED', description: 'HR flags employee on vacation. IP resolving to overseas residential block.', module: 'HR_OPS', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'ciso' ? { ...a, status: 'ACTIVE', lastMessage: 'Checked personnel log status.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '17:15:30', agent: 'ciso', action: 'VERIFY_LEAVE', details: 'Employee confirmed on leave.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 85, revenueAtRisk: '$2.0M', affectedUsers: 0, nodesCompromised: 1, activeIncidentsCount: 1,
          regionalStatus: [{ name: 'US-EAST-1', status: 'OPTIMAL' }, { name: 'EU-WEST-2', status: 'CRITICAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '17:30', title: 'IP SYSTEM THREAT', description: 'Stolen data contains core proprietary software weights.', module: 'LEGAL_SHIELD', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'legal' ? { ...a, status: 'THINKING', lastMessage: 'Reviewing trade secret policies.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '17:30:45', agent: 'legal', action: 'EVAL_EXPOSURE', details: 'IP damage rating high.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'OMEGA',
          debate: [
            { sender: 'Security Sentinel', role: 'Security', timestamp: '17:40:11', content: 'I recommend immediate account termination and credential revocation. Every second we wait, more files are siphoned.', sentiment: 'critical' },
            { sender: 'Compliance Shield', role: 'Legal', timestamp: '17:40:35', content: 'If we suspend now, the attacker realizes they are caught and may delete evidence. Silent monitoring allows us to build a legal case.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '17:41:00', content: 'Both options are high-stakes. Operator, do we revoke access immediately or silently monitor their actions?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '17:40', title: 'CONTAINMENT DEBATE ACTIVE', description: 'Board debates suspending credentials vs silent tracking.', module: 'EXEC_BOARD', severity: 'critical' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-007": {
    title: "Global Product Recall",
    severity: "ALPHA",
    description: "Thermal defect discovered in production lot #412.",
    shutdownLabel: "GLOBAL RECALL",
    isolationLabel: "TARGETED SWAP",
    agentsInvolved: ["infra", "legal", "finance", "pr", "ceo"],
    postMortemGen: (decision) => ({
      rootCause: "Overheating battery components in lot #412 hardware units.",
      timelineAnalysis: `19:00 Fault identified -> 19:15 Audit distribution -> 19:30 Financial check -> 19:40 Recall debate -> 20:00 ${decision === 'SHUTDOWN' ? 'Global recall' : 'Targeted replacement'} active.`,
      businessImpact: decision === 'SHUTDOWN' ? "Recall launched. Reclaimed safety rating, high return costs." : "Regional swaps completed. Mitigated costs, residual liability in EU.",
      complianceReport: "Consumer safety notices compiled and filed.",
      lessonsLearned: "Establish thermal telemetry monitoring on hardware.",
      preventionPlan: "Implement secondary battery circuit breaker specs."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 50, revenueAtRisk: '$800K', affectedUsers: 5000, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [{ time: '19:00', title: 'QA FAULT DETECTED', description: 'Operations flags thermal runtimes in lot #412 battery nodes.', module: 'QA_MONITOR', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'THINKING', lastMessage: 'Scanning QA sensor logs.' } : a),
          auditLogs: [{ id: '1', timestamp: '19:00:15', agent: 'infra', action: 'FLAG_QA', details: 'Lot #412 battery units flagged.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 70, revenueAtRisk: '$2.1M', affectedUsers: 25000, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [...prev.timeline, { time: '19:15', title: 'DISTRIBUTION AUDITED', description: '75,000 compromised devices active in US, EU, and APAC.', module: 'SUPPLY_OPS', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'ACTIVE', lastMessage: 'Auditing distributor shipment logs.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '19:15:30', agent: 'infra', action: 'AUDIT_DISTRIBUTION', details: 'Identified 3 active regional batches.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 85, revenueAtRisk: '$3.8M', affectedUsers: 75000, nodesCompromised: 0, activeIncidentsCount: 1,
          regionalStatus: [{ name: 'US-EAST-1', status: 'DEGRADED' }, { name: 'EU-WEST-2', status: 'DEGRADED' }, { name: 'AP-SOUTH-1', status: 'DEGRADED' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '19:30', title: 'LIABILITY SCALE ESTIMATED', description: 'Finance estimates recall cost at $3.5M. Legal warns of lawsuit risks.', module: 'FINANCE_DEPT', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'finance' ? { ...a, status: 'THINKING', lastMessage: 'Structuring recovery budgets.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '19:30:45', agent: 'finance', action: 'CALC_RECALL_COST', details: 'Modeled recall logistic lines.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'ALPHA',
          debate: [
            { sender: 'Operations Core', role: 'Ops', timestamp: '19:40:12', content: 'Safety first. We must issue a full global recall. Targeted replacements leave high risk units active in EU and APAC.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '19:40:35', content: 'A global recall is financially destructive. Let\'s do a targeted swap for active commercial nodes and run firmware throttling on residential devices.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '19:41:00', content: 'Risk of thermal issue is critical. Operator, do we execute a global product recall or a targeted replacement swap?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '19:40', title: 'RECALL SCOPE DEBATE', description: 'Board debates global safety recall vs partial replacements.', module: 'EXEC_BOARD', severity: 'high' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-008": {
    title: "Large Scale Financial Fraud",
    severity: "OMEGA",
    description: "Suspicious API transfers bypassing threshold rules.",
    shutdownLabel: "FREEZE TRANSACTIONS",
    isolationLabel: "OBSERVE & REPORT",
    agentsInvolved: ["finance", "sec", "legal", "ceo", "cfo", "ciso"],
    postMortemGen: (decision) => ({
      rootCause: "Exfiltrated transaction token key used to bypass multi-factor threshold rules.",
      timelineAnalysis: `21:05 Pattern logged -> 21:15 Token traced -> 21:30 SAR prepared -> 21:40 Board debate -> 22:00 ${decision === 'SHUTDOWN' ? 'Transactions frozen' : 'Log monitoring'} implemented.`,
      businessImpact: decision === 'SHUTDOWN' ? "Gateway frozen. Recovered API credential. No capital lost." : "Observational logging allowed loss of $1.5M prior to IP blacklist.",
      complianceReport: "FinCEN Form 111 (SAR) submitted successfully.",
      lessonsLearned: "Billing API keys must require source IP binds.",
      preventionPlan: "Implement real-time transaction outlier detection."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 65, revenueAtRisk: '$1.0M', affectedUsers: 120, nodesCompromised: 2, activeIncidentsCount: 10,
          timeline: [{ time: '21:05', title: 'SUSPICIOUS TRANSACTIONS', description: 'Structured wire payments found bypassing transaction limits.', module: 'FINANCE_DEPT', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'finance' ? { ...a, status: 'THINKING', lastMessage: 'Auditing API key execution.' } : a),
          auditLogs: [{ id: '1', timestamp: '21:05:15', agent: 'finance', action: 'FLAG_ACCOUNTS', details: 'Detected structured transfers.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 80, revenueAtRisk: '$2.5M', affectedUsers: 450, nodesCompromised: 5, activeIncidentsCount: 24,
          timeline: [...prev.timeline, { time: '21:15', title: 'CREDENTIAL LEAK', description: 'Exfiltrated live billing token utilized in wire requests.', module: 'SECURITY_OPS', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'sec' ? { ...a, status: 'ACTIVE', lastMessage: 'Traced credential token usage.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '21:15:30', agent: 'sec', action: 'TRACE_CREDENTIALS', details: 'Compromised token identified.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 92, revenueAtRisk: '$4.2M', affectedUsers: 1200, nodesCompromised: 5, activeIncidentsCount: 24,
          regionalStatus: [{ name: 'US-EAST-1', status: 'CRITICAL' }, { name: 'EU-WEST-2', status: 'OPTIMAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '21:30', title: 'SAR FILING OBLIGATION', description: 'Compliance requirements dictate filing SAR (FinCEN).', module: 'LEGAL_SHIELD', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'legal' ? { ...a, status: 'THINKING', lastMessage: 'Drafting FinCEN reports.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '21:30:45', agent: 'legal', action: 'PREPARE_SAR', details: 'Structuring suspect profiles.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'OMEGA',
          debate: [
            { sender: 'Financial Auditor', role: 'Finance', timestamp: '21:40:12', content: 'Freeze transactions immediately. We have $4.2M exposed. Any delay is a direct liability to the balance sheet.', sentiment: 'critical' },
            { sender: 'Risk Assessment', role: 'Risk', timestamp: '21:40:35', content: 'If we freeze, we alert the syndicate. We should log transaction flows silently for another hour to map the target endpoints.', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '21:41:00', content: 'This decision impacts FinCEN audits. Operator, do we freeze transaction processing or observe and report?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '21:40', title: 'BOARD ACTION DEBATE', description: 'Board debates immediate freeze vs tracking logging.', module: 'EXEC_BOARD', severity: 'critical' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-009": {
    title: "Global Supply Chain Failure",
    severity: "ALPHA",
    description: "Port strike halting core component container logistics.",
    shutdownLabel: "HALT PRODUCTION",
    isolationLabel: "AIR FREIGHT SOURCE",
    agentsInvolved: ["infra", "finance", "ceo", "cfo", "ciso"],
    postMortemGen: (decision) => ({
      rootCause: "Long Beach port labor strike blocking supplier shipments.",
      timelineAnalysis: `22:05 Port strike flagged -> 22:15 Assembly delay logged -> 22:30 Cost analysis -> 22:40 Debate -> 23:00 ${decision === 'SHUTDOWN' ? 'Factory shutdown' : 'Air freight route'} complete.`,
      businessImpact: decision === 'SHUTDOWN' ? "Invoked Force Majeure. Backlog is high, saved air premium." : "Air freight sourced. Resumed assembly, erased Q3 profit margin.",
      complianceReport: "Supply contract SLA disclosures delivered.",
      lessonsLearned: "Maintain localized safety inventory stocks.",
      preventionPlan: "Establish manufacturing redundant locations in EU."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 40, revenueAtRisk: '$400K', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [{ time: '22:05', title: 'PORT DELAYS FLAGGED', description: 'Long Beach strike blocks 3 key supplier semiconductor lines.', module: 'LOGISTICS_SYS', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'THINKING', lastMessage: 'Checking shipment schedules.' } : a),
          auditLogs: [{ id: '1', timestamp: '22:05:12', agent: 'infra', action: 'CHECK_SHIPPINGS', details: 'Containers delayed in port harbor.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 65, revenueAtRisk: '$1.2M', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          timeline: [...prev.timeline, { time: '22:15', title: 'PRODUCTION BACKLOG ESTIMATE', description: 'Factory assembly lines face 21 days delay if unresolved.', module: 'SUPPLY_ANALYSIS', severity: 'medium' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'ACTIVE', lastMessage: 'Modeling assembly pipeline backlog.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '22:15:30', agent: 'infra', action: 'CALC_DELAY', details: 'Safety stock projected exhausted in 5 days.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 78, revenueAtRisk: '$2.4M', affectedUsers: 0, nodesCompromised: 0, activeIncidentsCount: 1,
          regionalStatus: [{ name: 'US-EAST-1', status: 'DEGRADED' }, { name: 'EU-WEST-2', status: 'OPTIMAL' }, { name: 'AP-SOUTH-1', status: 'OPTIMAL' }, { name: 'SA-EAST-1', status: 'OPTIMAL' }],
          timeline: [...prev.timeline, { time: '22:30', title: 'SLA PENALTIES ESTIMATED', description: 'Finance projects $2.4M SLA delivery penalty costs.', module: 'FINANCE_DEPT', severity: 'high' }],
          agents: prev.agents.map(a => a.id === 'finance' ? { ...a, status: 'THINKING', lastMessage: 'Analyzing delay penalty clauses.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '22:30:45', agent: 'finance', action: 'CALC_PENALTY', details: 'Modeled customer contract breach risk.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'ALPHA',
          debate: [
            { sender: 'Operations Core', role: 'Ops', timestamp: '22:40:12', content: 'We must source alternative semiconductors. Sourcing them locally via air freight prevents production line shutdown, saving customer trust.', sentiment: 'alert' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '22:40:35', content: 'Air freight at 3x premium wipes out Q3 profit margins entirely. Halting production for 21 days and invoking Force Majeure is cheaper.', sentiment: 'critical' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '22:41:00', content: 'We need to balance safety and budget. Operator, do we halt production or pay the air freight premium?', sentiment: 'neutral' }
          ],
          timeline: [...prev.timeline, { time: '22:40', title: 'SUPPLY CHAIN DEBATE', description: 'Board debates alternative air freight vs factory halt.', module: 'EXEC_BOARD', severity: 'high' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  },
  "INC-010": {
    title: "Enterprise Perfect Storm",
    severity: "OMEGA",
    description: "Simultaneous cyberattack, cloud outage, GDPR breach, and PR viral crisis.",
    shutdownLabel: "EMERGENCY LOCKDOWN",
    isolationLabel: "SEGMENT CONTAINMENT",
    agentsInvolved: ["detection", "sec", "infra", "legal", "finance", "cx", "pr", "ceo", "cfo", "ciso"],
    postMortemGen: (decision) => ({
      rootCause: "Coordinated state-sponsored cyberattack targeting active services with masking DDoS.",
      timelineAnalysis: `00:01 Alarms -> 00:15 Cross-room collaboration -> 00:30 GDPR collapse -> 00:40 Debate -> 01:00 ${decision === 'SHUTDOWN' ? 'Emergency lockdown' : 'Segmented containment'} complete.`,
      businessImpact: decision === 'SHUTDOWN' ? "Locked down all systems. Severed links. System integrity preserved." : "Fought segment-by-segment. Transaction flows online, but exfiltration persists.",
      complianceReport: "Regulatory audit reporting filed. Incident logged in blockchain.",
      lessonsLearned: "Prepare emergency air-gap protocols.",
      preventionPlan: "Implement zero-trust security architecture globally."
    }),
    steps: [
      {
        delay: 1000,
        update: (prev) => ({
          ...prev, scenarioState: 'DETECTION', riskScore: 85, revenueAtRisk: '$3.5M', affectedUsers: 80000, nodesCompromised: 15, activeIncidentsCount: 5,
          timeline: [{ time: '00:01', title: 'MULTI-VECTOR ALARMS DETECTED', description: 'Coordinated attacks launched. DDoS, cloud outages, and leak alarms detected.', module: 'MASTER_COMMAND', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'sec' ? { ...a, status: 'THINKING', lastMessage: 'Scanning multiple layers.' } : a),
          auditLogs: [{ id: '1', timestamp: '00:01:05', agent: 'Detection_Agent', action: 'SPAWN_WAR_ROOMS', details: 'Created Master war room and spawned sub-rooms.' }]
        })
      },
      {
        delay: 4000,
        update: (prev) => ({
          ...prev, scenarioState: 'INVESTIGATION', riskScore: 95, revenueAtRisk: '$8.2M', affectedUsers: 350000, nodesCompromised: 48, activeIncidentsCount: 14,
          timeline: [...prev.timeline, { time: '00:15', title: 'CROSS-ROOM CHANNEL COLLABORATION', description: '16 agents sync. Tracing malware shifts while Infra reports failure.', module: 'BAND_SDK', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'infra' ? { ...a, status: 'ACTIVE', lastMessage: 'AWS clusters report offline.' } : a),
          auditLogs: [...prev.auditLogs, { id: '2', timestamp: '00:15:30', agent: 'Security_Agent', action: 'CORRELATE_THREAT', details: 'Correlated DDoS patterns with data leak.' }]
        })
      },
      {
        delay: 7000,
        update: (prev) => ({
          ...prev, scenarioState: 'RISK_LEGAL', riskScore: 99, revenueAtRisk: '$12.5M', affectedUsers: 800000, nodesCompromised: 124, activeIncidentsCount: 32,
          regionalStatus: [{ name: 'US-EAST-1', status: 'CRITICAL' }, { name: 'EU-WEST-2', status: 'CRITICAL' }, { name: 'AP-SOUTH-1', status: 'DEGRADED' }, { name: 'SA-EAST-1', status: 'DEGRADED' }],
          timeline: [...prev.timeline, { time: '00:30', title: 'REGULATORY COLLAPSE', description: 'GDPR status non-compliant. Viral PR reaches 5M users.', module: 'LEGAL_SHIELD', severity: 'critical' }],
          agents: prev.agents.map(a => a.id === 'legal' ? { ...a, status: 'ACTIVE', lastMessage: 'High liability rating verified.' } : a),
          auditLogs: [...prev.auditLogs, { id: '3', timestamp: '00:30:45', agent: 'Risk_Agent', action: 'CALC_AGGREGATE_LOSS', details: 'Aggregate loss modeled at $42M/hr.' }]
        })
      },
      {
        delay: 10000,
        update: (prev) => ({
          ...prev, scenarioState: 'DEBATE_ACTIVE', severity: 'OMEGA',
          debate: [
            { sender: 'CISO_SHIELD', role: 'CISO', timestamp: '00:40:11', content: 'This is the perfect storm. The exfiltration is crossing all subnet borders. I recommend an immediate COMPLETE ENTERPRISE LOCKDOWN. Cut all internet connectivity.', sentiment: 'critical' },
            { sender: 'CTO_NODAL', role: 'CTO', timestamp: '00:40:25', content: 'A complete lockdown means shutting down all servers, factories, and VPNs globally. Recovery will take weeks. We must fight segment-by-segment.', sentiment: 'critical' },
            { sender: 'CFO_QUANT', role: 'CFO', timestamp: '00:40:40', content: 'Global shutdown drops our active transactions to zero. That represents a $50M daily balance sheet hit. Can we survive a segmented battle?', sentiment: 'alert' },
            { sender: 'CEO_ALPHA', role: 'CEO', timestamp: '00:41:00', content: 'Operator, the Board is split. The future of the enterprise is in your hands. Complete lockdown or segmented containment?', sentiment: 'critical' }
          ],
          timeline: [...prev.timeline, { time: '00:40', title: 'JOINT EMERGENCY DEBATE ACTIVE', description: 'All C-suite agents join active session debate.', module: 'EXEC_BOARD', severity: 'critical' }],
          agents: prev.agents.map(a => ({ ...a, status: 'SLEEPING' }))
        })
      }
    ]
  }
};

export function CommandCenterProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<CommandCenterState>(initialStates);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const apiBase = (() => {
    if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
    if (wsUrl) {
      try {
        const parsed = new URL(wsUrl);
        const protocol = parsed.protocol === 'wss:' ? 'https:' : 'http:';
        return `${protocol}//${parsed.host}`;
      } catch (e) {
        return wsUrl.replace(/^ws(s)?:\/\//, 'http$1://').split('/ws')[0];
      }
    }
    return 'http://localhost:8000';
  })();
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';

  useEffect(() => {
    let isMounted = true;
    fetch(`${apiBase}/api/incident/alerts`)
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Failed to fetch alerts');
      })
      .then(data => {
        if (isMounted) {
          setState(prev => ({
            ...prev,
            receivedAlerts: data
          }));
        }
      })
      .catch(err => console.error('Error fetching alerts history:', err));

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: NodeJS.Timeout | null = null;
    let isMounted = true;

    function connect() {
      if (!isMounted) return;
      // Build WebSocket URL — append api_key query param if configured
      const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
      const apiKey = process.env.NEXT_PUBLIC_API_KEY;
      const wsUrl = apiKey ? `${wsBase}?api_key=${encodeURIComponent(apiKey)}` : wsBase;
      console.log('Attempting WS connection to', wsUrl.replace(/api_key=([^&]+)/, 'api_key=***'));
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!isMounted) {
          ws?.close();
          return;
        }
        console.log('Connected to Crisis Command Center backend WS');
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'state_update' && isMounted) {
            setState((prev) => ({
              ...prev,
              ...data.payload,
            }));
          } else if (data.type === 'external_alert_received' && isMounted) {
            setState((prev) => ({
              ...prev,
              receivedAlerts: [data.payload, ...(prev.receivedAlerts || [])],
              simulationRunning: true,
              scenarioId: data.payload.id,
              scenarioTitle: data.payload.title,
            }));
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        if (!isMounted) return;
        console.log('Backend WS disconnected, retrying in 3s...');
        setSocket(null);
        timer = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      isMounted = false;
      if (ws) {
        ws.close();
      }
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, []);

  // Offline local simulation sequence to ensure visual feedback under all circumstances
  const runLocalScenarioSimulation = useCallback((scenarioId: string) => {
    const sData = LOCAL_SCENARIOS_DATA[scenarioId] || LOCAL_SCENARIOS_DATA['INC-001'];
    
    // Build initial agents list
    const activeAgents: AgentInfo[] = sData.agentsInvolved.map((name, idx) => {
      const aInfo = LOCAL_AGENTS_DB[name];
      return aInfo
        ? { ...aInfo, status: 'IDLE' as const }
        : { id: `agent_${idx}`, name, role: 'Operator', status: 'IDLE' as const, lastMessage: 'Monitoring status.', tags: ['SYNC'] };
    });

    // Reset and initialize state for the selected scenario
    setState({
      scenarioState: 'INITIAL',
      scenarioId,
      scenarioTitle: sData.title,
      severity: 'OPTIMAL',
      riskScore: 0,
      revenueAtRisk: '$0',
      affectedUsers: 0,
      nodesCompromised: 0,
      activeIncidentsCount: 0,
      regionalStatus: [
        { name: 'US-EAST-1', status: 'OPTIMAL' },
        { name: 'EU-WEST-2', status: 'OPTIMAL' },
        { name: 'AP-SOUTH-1', status: 'OPTIMAL' },
        { name: 'SA-EAST-1', status: 'OPTIMAL' },
      ],
      timeline: [],
      agents: activeAgents,
      debate: [],
      auditLogs: [],
      decisionMatrix: [
        { vector: 'Security Risk', shutdownScore: 90, isolateScore: 30 },
        { vector: 'Revenue Impact', shutdownScore: 15, isolateScore: 80 },
        { vector: 'Recovery Time', shutdownScore: 25, isolateScore: 85 },
        { vector: 'Compliance Rating', shutdownScore: 95, isolateScore: 50 },
      ],
      postMortem: null,
      shutdownLabel: sData.shutdownLabel,
      isolationLabel: sData.isolationLabel,
      simulationRunning: true,
    });
    
    // Schedule state updates
    sData.steps.forEach((step) => {
      setTimeout(() => {
        setState((current) => {
          if (!current.simulationRunning || current.scenarioState === 'RESOLVED' || current.scenarioId !== scenarioId) return current;
          return step.update(current);
        });
      }, step.delay);
    });
  }, []);

  const startDemo = useCallback(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: 'start_demo', payload: { scenario_id: 'INC-001' } }));
    } else {
      console.warn('Backend not connected. Running offline local demo simulation.');
      runLocalScenarioSimulation('INC-001');
    }
  }, [socket, runLocalScenarioSimulation]);

  const startScenario = useCallback((scenarioId: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: 'start_scenario', payload: { scenario_id: scenarioId } }));
    } else {
      console.warn(`Backend not connected. Running offline local simulation for ${scenarioId}.`);
      runLocalScenarioSimulation(scenarioId);
    }
  }, [socket, runLocalScenarioSimulation]);

  const deployCountermeasures = useCallback((decision: 'SHUTDOWN' | 'ISOLATION') => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: 'submit_decision', payload: { decision } }));
    } else {
      // Offline local flow handler
      setState((prev) => {
        const activeId = prev.scenarioId || 'INC-001';
        const sData = LOCAL_SCENARIOS_DATA[activeId] || LOCAL_SCENARIOS_DATA['INC-001'];
        const labelUsed = decision === 'SHUTDOWN' ? sData.shutdownLabel : sData.isolationLabel;

        const timelineEvent: TimelineEvent = {
          time: new Date().toLocaleTimeString().slice(0, 5),
          title: `COUNTERMEASURES: ${decision}`,
          description: `C-Suite consensus: ${labelUsed} executed. Containment sequence initiated.`,
          module: 'EXECUTIVE_DECISION',
          severity: decision === 'SHUTDOWN' ? 'medium' : 'high',
        };

        const postMortemReport = sData.postMortemGen(decision);

        return {
          ...prev,
          scenarioState: 'RESOLVED',
          severity: decision === 'SHUTDOWN' ? 'OPTIMAL' : 'ALPHA',
          riskScore: decision === 'SHUTDOWN' ? 12 : 45,
          revenueAtRisk: decision === 'SHUTDOWN' ? '$0' : '$1.2M',
          timeline: [...prev.timeline, timelineEvent],
          agents: prev.agents.map(a => ({
            ...a,
            status: 'SLEEPING',
            lastMessage: 'Crisis resolved. Monitoring post-recovery checks.'
          })),
          postMortem: postMortemReport,
          simulationRunning: false
        };
      });
    }
  }, [socket]);

  const resetDemo = useCallback(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: 'reset' }));
    }
    setState(initialStates);
  }, [socket]);

  const focusOnAlert = useCallback((alert: AlertInfo) => {
    setState(prev => ({
      ...prev,
      simulationRunning: true,
      scenarioId: alert.id,
      scenarioTitle: alert.title,
      scenarioState: 'DETECTION',
      severity: alert.severity?.toUpperCase() === 'CRITICAL' ? 'OMEGA' : 'ALPHA',
    }));
  }, []);

  return (
    <CommandCenterContext.Provider value={{ state, activeTab, setActiveTab, startDemo, startScenario, deployCountermeasures, resetDemo, focusOnAlert, apiBase, apiKey }}>
      {children}
    </CommandCenterContext.Provider>
  );
}

export function useCommandCenter() {
  const context = useContext(CommandCenterContext);
  if (context === undefined) {
    throw new Error('useCommandCenter must be used within a CommandCenterProvider');
  }
  return context;
}
