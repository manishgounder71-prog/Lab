'use client';

import React, { useEffect } from 'react';
import { useCommandCenter } from '../context/CommandCenterContext';
import dynamic from 'next/dynamic';
import SpaceBackground from '../components/SpaceBackground';
import NeuralGraph from '../components/NeuralGraph';

// Lazy-load Three.js component to reduce initial bundle size
const SeverityOrb = dynamic(() => import('../components/SeverityOrb'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 rounded-full border-2 border-[#c6c6c6] border-t-transparent animate-spin" />
    </div>
  ),
});

// Lazy-load Recharts — only used during active simulations
const PredictiveChart = dynamic(() => import('../components/PredictiveChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 rounded-full border-2 border-[#c6c6c6] border-t-transparent animate-spin" />
    </div>
  ),
});
import { motion } from 'framer-motion';
import { 
  Shield, Cpu, Gavel, Award, TrendingUp, 
  ShieldCheck, Radio, Database,
  Radar, CheckCircle, AlertCircle, ChevronRight, ChevronDown,
  Coins, Users, Megaphone, RefreshCw, AlertTriangle,
  ScanFace, Binary, Activity
} from 'lucide-react';
// Recharts is dynamically imported below where it's used


interface ScenarioCard {
  id: string;
  title: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Maximum';
  description: string;
  impact: string;
  agents: string[];
  isFlagship?: boolean;
}

const SCENARIOS_LIST: ScenarioCard[] = [
  {
    id: "INC-001",
    title: "Customer Database Breach",
    severity: "Critical",
    description: "Unauthorized SQL queries detected on the production customer database.",
    impact: "150k users (EU) | Sensitive PII exposed",
    agents: ["Detection", "Security", "Infra", "Legal", "Finance", "CX", "PR", "CEO", "CFO", "CISO"]
  },
  {
    id: "INC-002",
    title: "Regional Cloud Outage",
    severity: "High",
    description: "AWS us-east-1 connection drops affecting multiple transaction API nodes.",
    impact: "Payment API, Dashboard, Auth down in us-east-1",
    agents: ["Infra", "Recovery", "Finance", "CX", "CTO", "CEO"]
  },
  {
    id: "INC-003",
    title: "Enterprise Ransomware Incident",
    severity: "Critical",
    description: "LockBit 3.0 ransomware active. Core local shadow backups purged.",
    impact: "320 desktop nodes compromised | $500K ransom",
    agents: ["Security", "Legal", "Recovery", "Finance", "CEO", "CISO"]
  },
  {
    id: "INC-004",
    title: "GDPR Compliance Violation",
    severity: "High",
    description: "Audit flags unpurged legacy volume retaining 500,000 customer records.",
    impact: "500k expired records | Risk of 4% turnover fine",
    agents: ["Legal", "Risk", "Finance", "CEO", "CFO"]
  },
  {
    id: "INC-005",
    title: "Brand Reputation Crisis",
    severity: "Medium",
    description: "Negative viral campaign trending on social channels alleging device tracking.",
    impact: "12,000 posts | 5M reach | 65% brand index drop",
    agents: ["PR", "Risk", "CX", "CEO", "Marketing"]
  },
  {
    id: "INC-006",
    title: "Malicious Insider Activity",
    severity: "Critical",
    description: "Suspicious database downloads flagged on administrator credentials at 3 AM.",
    impact: "DBA account | 300 sensitive file downloads",
    agents: ["Security", "Legal", "HR", "CEO", "CISO"]
  },
  {
    id: "INC-007",
    title: "Global Product Recall",
    severity: "High",
    description: "QA flags thermal runtimes in shipped Lot #412 battery nodes.",
    impact: "75,000 active devices | Class-action lawsuit risk",
    agents: ["Operations", "Legal", "Finance", "PR", "CEO"]
  },
  {
    id: "INC-008",
    title: "Large Scale Financial Fraud",
    severity: "Critical",
    description: "Structured wire payments bypassing API daily caps found on gateway.",
    impact: "1,200 transactions | $4.2M exposure risk",
    agents: ["Finance", "Risk", "Security", "Legal", "CEO", "CFO"]
  },
  {
    id: "INC-009",
    title: "Global Supply Chain Failure",
    severity: "High",
    description: "Long Beach port strike halts semiconductor carrier supply shipments.",
    impact: "3 key suppliers affected | 21-day assembly delay",
    agents: ["Operations", "Finance", "Risk", "CEO", "CFO", "CTO"]
  },
  {
    id: "INC-010",
    title: "Enterprise Perfect Storm",
    severity: "Maximum",
    description: "Coordinated state-sponsored attack. Simultaneous cyber breach, cloud outage, GDPR audit failure, and social panic.",
    impact: "ALL systems degraded | Active cross-room board debate",
    agents: ["Detection", "Security", "Infra", "Recovery", "Risk", "Legal", "HR", "Operations", "Finance", "CX", "PR", "Marketing", "CEO", "CFO", "CTO", "CISO"],
    isFlagship: true
  }
];

// Static data — extracted outside component to avoid re-creation

function getSeverityStyle(severity: string): string {
  switch (severity) {
    case 'Maximum':
      return 'border-[#ff3b30] text-[#ff3b30] bg-[#ff3b30]/10 shadow-[0_0_15px_rgba(255,59,48,0.2)] font-extrabold animate-pulse';
    case 'Critical':
      return 'border-red-500/40 text-red-400 bg-red-950/20';
    case 'High':
      return 'border-amber-500/40 text-amber-400 bg-amber-950/20';
    case 'Medium':
      return 'border-cyan-500/40 text-cyan-400 bg-cyan-950/20';
    default:
      return 'border-white/20 text-white bg-white/5';
  }
}
function CommandCenterShell() {
  const { 
    state, 
    activeTab, 
    setActiveTab, 
    startDemo, 
    startScenario,
    deployCountermeasures, 
    resetDemo,
    focusOnAlert
  } = useCommandCenter();

  // Webhook Simulator form state
  const [webhookSource, setWebhookSource] = React.useState('Datadog');
  const [webhookType, setWebhookType] = React.useState('Data Breach');
  const [webhookSeverity, setWebhookSeverity] = React.useState('CRITICAL');
  const [webhookTitle, setWebhookTitle] = React.useState('Unusual PostgreSQL Outflow Alert');
  const [webhookDesc, setWebhookDesc] = React.useState('Multi-vector queries observed exfiltrating sensitive PII logs at 45GB/s.');
  const [webhookSubmitting, setWebhookSubmitting] = React.useState(false);
  const [webhookSuccess, setWebhookSuccess] = React.useState(false);

  const handleTriggerWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    setWebhookSubmitting(true);
    setWebhookSuccess(false);
    try {
      const res = await fetch('http://localhost:8000/api/incident/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source: webhookSource,
          event_type: webhookType,
          severity: webhookSeverity,
          title: webhookTitle,
          description: webhookDesc,
        }),
      });
      if (res.ok) {
        setWebhookSuccess(true);
        setTimeout(() => {
          scrollToSection('dashboard');
          setWebhookSuccess(false);
        }, 800);
      } else {
        console.error('Failed to trigger webhook');
      }
    } catch (err) {
      console.error('Error triggering webhook:', err);
    } finally {
      setWebhookSubmitting(false);
    }
  };

  const [exchanges, setExchanges] = React.useState<Array<{
    id: string;
    agent: string;
    role: string;
    message: string;
    time: string;
    sentiment: 'neutral' | 'critical' | 'alert' | 'success';
  }>>([]);
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  // Parse state.debate to the same format
  const debateExchanges = React.useMemo(() => {
    return state.debate.map((msg, idx) => ({
      id: `debate-${idx}-${msg.timestamp}`,
      agent: msg.sender,
      role: msg.role,
      message: msg.content,
      time: msg.timestamp,
      sentiment: msg.sentiment
    }));
  }, [state.debate]);

  const allExchanges = React.useMemo(() => {
    return [...exchanges, ...debateExchanges];
  }, [exchanges, debateExchanges]);

  // Scroll to bottom when exchanges update
  React.useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [allExchanges.length]);

  // Capture real-time agent message changes
  React.useEffect(() => {
    if (state.scenarioState === 'INITIAL') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setExchanges(prev => prev.length > 0 ? [] : prev);
      return;
    }

    const defaultMessages = [
      'Scanning network logs and integrity hashes.',
      'Monitoring traffic for signs of lateral intrusion.',
      'All system clusters active and balancing load.',
      'Compliance scanning GDPR/CCPA regulations.',
      'Monitoring liquidity pools and billing APIs.',
      'Analyzing customer churn risk and active session drop-offs.',
      'Press hold templates ready.',
      'Enforcing data protection policies.',
      'Analyzing cost structures and revenue lines.',
      'Overseeing operational alignment and decision vectors.',
      'Shadow volume and database replication points verified.',
      'Risk vector assessment at base level.',
      'Access logs tied to physical building card swipe checks.',
      'Supply lines and logistical pipelines monitored.',
      'Reviewing ad placement pauses and campaign responses.',
      'Evaluating engineering architecture health.'
    ];

    state.agents.forEach((agent) => {
      if (agent.status === 'IDLE') return;
      if (!agent.lastMessage || defaultMessages.includes(agent.lastMessage)) return;

      setExchanges((prev) => {
        const lastForAgent = [...prev].reverse().find(e => e.agent === agent.name);
        
        if (lastForAgent && lastForAgent.message === agent.lastMessage) {
          return prev;
        }
        
        const alreadyExists = prev.some(e => e.agent === agent.name && e.message === agent.lastMessage);
        if (alreadyExists) return prev;

        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
        const sentiment: 'critical' | 'neutral' | 'alert' | 'success' = agent.status === 'ACTIVE' ? 'critical' : 'neutral';

        return [
          ...prev,
          {
            id: `${agent.id}-${Date.now()}-${Math.random()}`,
            agent: agent.name,
            role: agent.role,
            message: agent.lastMessage,
            time: timestamp,
            sentiment
          }
        ];
      });
    });
  }, [state.agents, state.scenarioState]);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      // Use scrollIntoView with offset, avoids forced layout from getBoundingClientRect chains
      const y = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  const handleLaunch = (scenarioId: string) => {
    startScenario(scenarioId);
    scrollToSection('dashboard');
  };

  // Scroll spy effect to highlight navigation based on current view
  useEffect(() => {
    const sections = ['overview', 'simulation', 'dashboard', 'war_room', 'board_room'];
    const observerOptions = {
      root: null,
      rootMargin: '-20% 0px -60% 0px',
      threshold: 0,
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setActiveTab(entry.target.id);
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => {
      sections.forEach((id) => {
        const el = document.getElementById(id);
        if (el) observer.unobserve(el);
      });
    };
  }, [setActiveTab]);

  // Force scroll to top on page load — disable browser scroll restoration entirely
  React.useEffect(() => {
    // Tell the browser not to restore scroll position
    if (window.history.scrollRestoration) {
      window.history.scrollRestoration = 'manual';
    }
    // Scroll to top immediately and again after a tick to override Next.js restoration
    window.scrollTo(0, 0);
    requestAnimationFrame(() => {
      window.scrollTo(0, 0);
    });
  }, []);

  const secAgent = state.agents.find((a) => a.id === 'sec');
  const infraAgent = state.agents.find((a) => a.id === 'infra');
  const legalAgent = state.agents.find((a) => a.id === 'legal');

  return (
    <div className="relative min-h-screen w-full flex flex-col font-body-base overflow-x-hidden">
      {/* WebGL space background shader */}
      <SpaceBackground />
      
      <div className="fixed inset-0 dot-grid pointer-events-none z-0" />

      {/* Global Command Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#131313]/70 backdrop-blur-xl border-b border-[#4c4546]/30 h-16 flex justify-between items-center px-6 shadow-[0_0_20px_rgba(198,198,198,0.1)]">
        <div className="flex items-center gap-4">
          <Radio size={28} className="text-[#c6c6c6]" />
          <div className="flex flex-col">
            <span className="font-label-caps text-sm tracking-widest text-[#c6c6c6] font-bold">CRISIS COMMAND</span>
            <span className="font-data-mono text-[9px] text-[#cfc4c5]/75 uppercase tracking-tighter">
              {state.scenarioState === 'INITIAL' ? 'IDLE SECURITY DOCKS' : `Incident ID: #${state.scenarioId} | Active: ${state.scenarioState}`}
            </span>
          </div>
        </div>

        {/* Header Tab Links */}
        <nav className="hidden md:flex gap-6 h-full items-center">
          <button 
            onClick={() => scrollToSection('overview')}
            className={`font-label-caps text-xs px-3 py-2 border-b-2 transition-all duration-300 ${activeTab === 'overview' ? 'border-[#c6c6c6] text-[#c6c6c6]' : 'border-transparent text-[#cfc4c5] hover:text-[#c6c6c6]'}`}
          >
            CONSOLE HOME
          </button>
          <button 
            onClick={() => scrollToSection('simulation')}
            className={`font-label-caps text-xs px-3 py-2 border-b-2 transition-all duration-300 ${activeTab === 'simulation' ? 'border-[#c6c6c6] text-[#c6c6c6]' : 'border-transparent text-[#cfc4c5] hover:text-[#c6c6c6]'}`}
          >
            SIMULATION DECK
          </button>
          <button 
            onClick={() => scrollToSection('dashboard')}
            className={`font-label-caps text-xs px-3 py-2 border-b-2 transition-all duration-300 ${activeTab === 'dashboard' ? 'border-[#c6c6c6] text-[#c6c6c6]' : 'border-transparent text-[#cfc4c5] hover:text-[#c6c6c6]'}`}
          >
            LIVE TELEMETRY
          </button>
          <button 
            onClick={() => scrollToSection('war_room')}
            className={`font-label-caps text-xs px-3 py-2 border-b-2 transition-all duration-300 ${activeTab === 'war_room' ? 'border-[#c6c6c6] text-[#c6c6c6]' : 'border-transparent text-[#cfc4c5] hover:text-[#c6c6c6]'}`}
          >
            SDK ORCHESTRATOR
          </button>
          <button 
            onClick={() => scrollToSection('board_room')}
            className={`font-label-caps text-xs px-3 py-2 border-b-2 transition-all duration-300 ${activeTab === 'board_room' ? 'border-[#c6c6c6] text-[#c6c6c6]' : 'border-transparent text-[#cfc4c5] hover:text-[#c6c6c6]'}`}
          >
            COMMAND DECISIONS
          </button>
        </nav>

        {/* Global Action controls */}
        <div className="flex items-center gap-4">
          {state.simulationRunning ? (
            <button 
              onClick={resetDemo}
              className="px-4 py-2 border border-red-500/40 text-red-400 text-xs font-label-caps hover:bg-red-950/30 rounded-sm transition-all"
            >
              RESET CRISIS
            </button>
          ) : (
            <button 
              onClick={startDemo}
              className="px-5 py-2 bg-[#c6c6c6] text-[#303030] text-xs font-label-caps hover:bg-white rounded-sm transition-all shadow-[0_0_15px_rgba(198,198,198,0.2)]"
            >
              SIMULATE BREACH DEMO
            </button>
          )}
          <Radar size={20} className="text-[#c6c6c6] cursor-pointer hover:scale-105 active:scale-95 duration-200" />
        </div>
      </header>

      {/* Main content body */}
      <main className="flex-1 relative z-10 pt-24 pb-24 px-6 md:px-8 max-w-[1700px] mx-auto w-full space-y-24">
        
        {/* Section 1: Overview */}
        <section id="overview" className="scroll-mt-24 w-full section-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            {/* Hero Section */}
            <div className="flex flex-col items-center text-center max-w-5xl mx-auto py-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#c6c6c6]/10 border border-[#c6c6c6]/20 mb-6">
                <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${state.scenarioState === 'INITIAL' ? 'bg-[#00ffcc]' : 'bg-red-500'}`} />
                <span className="font-label-caps text-[10px] text-[#c6c6c6]">
                  SYSTEM STATUS: {state.scenarioState === 'INITIAL' ? 'OPTIMAL' : 'ACTIVE BREACH DETECTED'}
                </span>
              </div>
              
              <h1 className="font-display-xl text-4xl md:text-7xl font-bold leading-tight mb-6 text-white tracking-tight">
                Enterprise <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c6c6c6] to-[#988e90]">Crisis Command</span> Center
              </h1>
              
              <p className="font-body-base text-[#cfc4c5] max-w-2xl mb-8 text-base md:text-lg">
                Multi-agent collaborative war room powered by Band SDK orchestration layer. Coordinating security threat analysis, infrastructure response, and corporate liability protocols.
              </p>

              <div className="flex gap-4">
                <button 
                  onClick={() => scrollToSection('war_room')}
                  className="bg-[#c6c6c6] text-[#303030] px-8 py-3.5 rounded-sm font-label-caps text-xs hover:bg-white transition-all shadow-[0_0_20px_rgba(198,198,198,0.2)]"
                >
                  LAUNCH WAR ROOM
                </button>
                <button 
                  onClick={() => scrollToSection('dashboard')}
                  className="border border-[#4c4546] text-[#e2e2e2] px-8 py-3.5 rounded-sm font-label-caps text-xs hover:border-[#c6c6c6] transition-all"
                >
                  EXECUTIVE SUMMARY
                </button>
              </div>
            </div>

            {/* Bento Grid layout of agents */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mt-12 relative">              {/* Agent 01: Security */}
              <div className={`md:col-span-4 glass-panel p-6 rounded-lg animate-float transition-all duration-300 ${
                secAgent?.status === 'ACTIVE' 
                  ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]' 
                  : secAgent?.status === 'THINKING' 
                  ? 'border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.05)]' 
                  : secAgent?.status === 'SLEEPING'
                  ? 'border-emerald-500/30'
                  : 'border-[#4c4546]/30'
              }`} style={{ animationDelay: '0s' }}>
                <div className="flex justify-between items-start mb-6">
                  <div className={`p-3 rounded-sm transition-colors ${
                    secAgent?.status === 'ACTIVE'
                      ? 'bg-red-500/10'
                      : secAgent?.status === 'THINKING'
                      ? 'bg-amber-500/10'
                      : secAgent?.status === 'SLEEPING'
                      ? 'bg-emerald-500/10'
                      : 'bg-[#c6c6c6]/10'
                  }`}>
                    <Shield size={24} className={`transition-colors ${
                      secAgent?.status === 'ACTIVE'
                        ? 'text-red-400'
                        : secAgent?.status === 'THINKING'
                        ? 'text-amber-400'
                        : secAgent?.status === 'SLEEPING'
                        ? 'text-emerald-400'
                        : 'text-[#c6c6c6]'
                    } ${['ACTIVE', 'THINKING'].includes(secAgent?.status || '') ? 'animate-pulse' : ''}`} />
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="font-label-caps text-[10px] text-[#c6c6c6] opacity-60">AGENT_SEC_01</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-data-mono font-bold tracking-wider uppercase ${
                      secAgent?.status === 'ACTIVE'
                        ? 'bg-red-950/40 text-red-400 border border-red-500/30 animate-pulse'
                        : secAgent?.status === 'THINKING'
                        ? 'bg-amber-950/40 text-amber-400 border border-amber-500/30'
                        : secAgent?.status === 'SLEEPING'
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-[#c6c6c6] border border-white/5'
                    }`}>
                      {secAgent?.status || 'IDLE'}
                    </span>
                  </div>
                </div>
                <h3 className="font-title-md text-lg mb-2">{secAgent?.name || "Cyber Threat Containment Agent"}</h3>
                <p className="font-body-sm text-sm text-[#cfc4c5] mb-6 min-h-[40px]">
                  {secAgent?.lastMessage || "Real-time threat detection and automated perimeter lockdown protocols."}
                </p>
                <div className="space-y-3">
                  <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full transition-all duration-1000 ${
                      secAgent?.status === 'ACTIVE'
                        ? 'bg-red-500 w-[90%] animate-pulse'
                        : secAgent?.status === 'THINKING'
                        ? 'bg-amber-500 w-[55%] animate-pulse'
                        : secAgent?.status === 'SLEEPING'
                        ? 'bg-emerald-500 w-full'
                        : 'bg-[#c6c6c6] w-[15%]'
                    }`} />
                  </div>
                  <div className="flex justify-between text-[10px] font-data-mono text-[#c6c6c6]/70">
                    <span className="uppercase">
                      {secAgent?.status === 'ACTIVE'
                        ? 'CONTAINMENT PROTOCOL DEPLOYED'
                        : secAgent?.status === 'THINKING'
                        ? 'TRACING DATABASE CONNECTIONS'
                        : secAgent?.status === 'SLEEPING'
                        ? 'SYSTEM SECURED & LOCKS ACTIVE'
                        : 'MONITORING ENCRYPTED TRAFFIC'}
                    </span>
                    <span>
                      {secAgent?.status === 'ACTIVE'
                        ? '90%'
                        : secAgent?.status === 'THINKING'
                        ? '55%'
                        : secAgent?.status === 'SLEEPING'
                        ? '100%'
                        : '15%'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Agent 02: Infrastructure */}
              <div className={`md:col-span-4 glass-panel p-6 rounded-lg animate-float mt-12 transition-all duration-300 ${
                infraAgent?.status === 'ACTIVE' 
                  ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]' 
                  : infraAgent?.status === 'THINKING' 
                  ? 'border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.05)]' 
                  : infraAgent?.status === 'SLEEPING'
                  ? 'border-emerald-500/30'
                  : 'border-[#4c4546]/30'
              }`} style={{ animationDelay: '1.5s' }}>
                <div className="flex justify-between items-start mb-6">
                  <div className={`p-3 rounded-sm transition-colors ${
                    infraAgent?.status === 'ACTIVE'
                      ? 'bg-red-500/10'
                      : infraAgent?.status === 'THINKING'
                      ? 'bg-amber-500/10'
                      : infraAgent?.status === 'SLEEPING'
                      ? 'bg-emerald-500/10'
                      : 'bg-[#c6c6c6]/10'
                  }`}>
                    <Cpu size={24} className={`transition-colors ${
                      infraAgent?.status === 'ACTIVE'
                        ? 'text-red-400'
                        : infraAgent?.status === 'THINKING'
                        ? 'text-amber-400'
                        : infraAgent?.status === 'SLEEPING'
                        ? 'text-emerald-400'
                        : 'text-[#c6c6c6]'
                    } ${['ACTIVE', 'THINKING'].includes(infraAgent?.status || '') ? 'animate-spin' : ''}`} style={{ animationDuration: infraAgent?.status === 'ACTIVE' ? '3s' : '8s' }} />
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="font-label-caps text-[10px] text-[#c6c6c6] opacity-60">AGENT_INFRA_02</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-data-mono font-bold tracking-wider uppercase ${
                      infraAgent?.status === 'ACTIVE'
                        ? 'bg-red-950/40 text-red-400 border border-red-500/30 animate-pulse'
                        : infraAgent?.status === 'THINKING'
                        ? 'bg-amber-950/40 text-amber-400 border border-amber-500/30'
                        : infraAgent?.status === 'SLEEPING'
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-[#c6c6c6] border border-white/5'
                    }`}>
                      {infraAgent?.status || 'IDLE'}
                    </span>
                  </div>
                </div>
                <h3 className="font-title-md text-lg mb-2">{infraAgent?.name || "Cloud Infrastructure & Failover Architect"}</h3>
                <p className="font-body-sm text-sm text-[#cfc4c5] mb-6 min-h-[40px]">
                  {infraAgent?.lastMessage || "Load balancing and cloud resource reallocation during peak incidents."}
                </p>
                <div className="flex flex-wrap gap-2">
                  {infraAgent?.tags ? (
                    infraAgent.tags.map((tag) => (
                      <span key={tag} className="px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] font-data-mono text-[#c6c6c6] uppercase tracking-tighter">
                        {tag}
                      </span>
                    ))
                  ) : (
                    <>
                      <span className="px-2 py-1 bg-[#353535] rounded text-[10px] font-data-mono text-[#c6c6c6]">AWS-US-EAST-1</span>
                      <span className="px-2 py-1 bg-[#353535] rounded text-[10px] font-data-mono text-[#c6c6c6]">ACTIVE</span>
                    </>
                  )}
                </div>
              </div>

              {/* Agent 03: Legal/Compliance */}
              <div className={`md:col-span-4 glass-panel p-6 rounded-lg animate-float transition-all duration-300 ${
                legalAgent?.status === 'ACTIVE' 
                  ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]' 
                  : legalAgent?.status === 'THINKING' 
                  ? 'border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.05)]' 
                  : legalAgent?.status === 'SLEEPING'
                  ? 'border-emerald-500/30'
                  : 'border-[#4c4546]/30'
              }`} style={{ animationDelay: '0.8s' }}>
                <div className="flex justify-between items-start mb-6">
                  <div className={`p-3 rounded-sm transition-colors ${
                    legalAgent?.status === 'ACTIVE'
                      ? 'bg-red-500/10'
                      : legalAgent?.status === 'THINKING'
                      ? 'bg-amber-500/10'
                      : legalAgent?.status === 'SLEEPING'
                      ? 'bg-emerald-500/10'
                      : 'bg-[#c6c6c6]/10'
                  }`}>
                    <Gavel size={24} className={`transition-colors ${
                      legalAgent?.status === 'ACTIVE'
                        ? 'text-red-400'
                        : legalAgent?.status === 'THINKING'
                        ? 'text-amber-400'
                        : legalAgent?.status === 'SLEEPING'
                        ? 'text-emerald-400'
                        : 'text-[#c6c6c6]'
                    } ${['ACTIVE', 'THINKING'].includes(legalAgent?.status || '') ? 'animate-pulse' : ''}`} />
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="font-label-caps text-[10px] text-[#c6c6c6] opacity-60">AGENT_LEGAL_03</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-data-mono font-bold tracking-wider uppercase ${
                      legalAgent?.status === 'ACTIVE'
                        ? 'bg-red-950/40 text-red-400 border border-red-500/30 animate-pulse'
                        : legalAgent?.status === 'THINKING'
                        ? 'bg-amber-950/40 text-amber-400 border border-amber-500/30'
                        : legalAgent?.status === 'SLEEPING'
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-[#c6c6c6] border border-white/5'
                    }`}>
                      {legalAgent?.status || 'IDLE'}
                    </span>
                  </div>
                </div>
                <h3 className="font-title-md text-lg mb-2">{legalAgent?.name || "Data Protection & Legal Compliance Shield"}</h3>
                <p className="font-body-sm text-sm text-[#cfc4c5] mb-6 min-h-[40px]">
                  {legalAgent?.lastMessage || "Ensuring regulatory adherence and automated reporting during breach events."}
                </p>
                <div className="flex items-center gap-3">
                  {['ACTIVE', 'THINKING'].includes(legalAgent?.status || '') ? (
                    <>
                      <div className="w-6 h-6 rounded-full border-2 border-[#c6c6c6] border-t-transparent animate-spin" />
                      <span className="font-data-mono text-[11px] text-[#cfc4c5] uppercase tracking-tighter">
                        {legalAgent?.status === 'ACTIVE' ? 'REPORTING MANDATES ACTIVE' : 'PARSING REGULATORY RULES'}
                      </span>
                    </>
                  ) : legalAgent?.status === 'SLEEPING' ? (
                    <>
                      <CheckCircle size={18} className="text-emerald-400" />
                      <span className="font-data-mono text-[11px] text-emerald-400 uppercase tracking-tighter font-bold">
                        COMPLIANCE SECURE
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="w-2 h-2 rounded-full bg-[#c6c6c6] animate-pulse" />
                      <span className="font-data-mono text-[11px] text-[#cfc4c5] uppercase tracking-tighter">
                        STANDING BY
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Data Visualizer Centerpiece */}
              <div className="md:col-span-12 glass-panel h-80 rounded-lg relative overflow-hidden flex items-center justify-center border-[#c6c6c6]/20">
                <div className="absolute inset-0 opacity-20 pointer-events-none">                    <img 
                    alt="Cyber Grid" 
                    loading="lazy" 
                    decoding="async" 
                    className="w-full h-full object-cover" 
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCYkywpcb7m3ioQuUXrSeoSKW099g-NT8fyRqNBKwwMjEh6qmpw_rRdyN4xl4c8HngGwfWvRGbGKWph0agpG8RD8V5oB3Bn64A9jha10hkmcXH2VXHlxD9AmfhZYvmaPciXA15bN9pfmA2jf075p4Tk-nIEtJ8nle_SpQZ0s_hRjYv6nabkf42wGmLTIRu0njJkwe_5dViYM0EG-osEBwrd4kzyDjm5Lpb1VBhGRXAR0DIZg4BzjX-n3BJ2mS4Y-yR9pZhIrfb7Vd4"
                  />
                </div>
                <div className="relative z-10 text-center">
                  <div className="pulse-ring absolute inset-0 -m-8 border border-[#c6c6c6]/30 rounded-full" />
                  <div className="pulse-ring absolute inset-0 -m-16 border border-[#c6c6c6]/10 rounded-full" style={{ animationDelay: '0.5s' }} />
                  <Radar size={60} className="text-[#c6c6c6] mb-4 mx-auto opacity-80" />
                  <h2 className="font-label-caps text-xs tracking-[0.3em] text-[#c6c6c6]">LIVE COLLABORATIVE FEED</h2>
                  <p className="font-data-mono text-[10px] text-[#cfc4c5] mt-2">AGENT BANDWIDTH: 4.8 TB/S | LATENCY: 0.4MS</p>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Section 5: Simulation Center */}
        <section id="simulation" className="scroll-mt-24 w-full pt-16 border-t border-white/10 section-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <div className="text-center max-w-3xl mx-auto mb-8">
              <h2 className="font-display-xl text-3xl md:text-5xl font-bold tracking-tight text-white mb-3">
                Cyber Simulation <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c6c6c6] to-[#988e90]">Deck</span>
              </h2>
              <p className="font-body-base text-[#cfc4c5] text-sm md:text-base">
                Select an incident scenario to trigger real-time AI agent collaboration in our Band-SDK simulated war room. Watch the C-Suite debate in real time and execute countermeasures.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              {SCENARIOS_LIST.map((sc) => (
                <div
                  key={sc.id}
                  className={`glass-panel p-6 rounded-xl relative group flex flex-col justify-between border border-[#4c4546]/30 overflow-hidden hover:border-[#c6c6c6]/50 transition-all duration-300 ${
                    sc.isFlagship 
                      ? 'md:col-span-12 lg:col-span-12 border-red-500/40 bg-gradient-to-br from-[#1c1213] to-[#131313]' 
                      : 'md:col-span-6 lg:col-span-4 bg-[#131313]/60'
                  }`}
                >
                  <div className="space-y-4">
                    {/* Card Top */}
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <span className="font-data-mono text-[10px] text-[#cfc4c5]/60 block mb-1">{sc.id}</span>
                        <h3 className="font-title-md text-lg md:text-xl font-bold text-white group-hover:text-[#00ffcc] transition-colors">{sc.title}</h3>
                      </div>
                      <span className={`px-2.5 py-0.5 border rounded-sm font-label-caps text-[9px] tracking-wider ${getSeverityStyle(sc.severity)}`}>
                        {sc.severity.toUpperCase()}
                      </span>
                    </div>

                    <p className="font-body-sm text-xs text-[#cfc4c5] leading-relaxed">
                      {sc.description}
                    </p>

                    {/* Estimated Impact */}
                    <div className="p-3 bg-white/5 rounded border border-white/5 flex items-center gap-2.5">
                      <span className="material-symbols-outlined text-[#c6c6c6] text-sm">warning</span>
                      <div>
                        <span className="font-label-caps text-[8px] text-[#cfc4c5]/60 block">ESTIMATED IMPACT</span>
                        <span className="font-data-mono text-[11px] text-white font-medium">{sc.impact}</span>
                      </div>
                    </div>

                    {/* Activated Agents */}
                    <div className="space-y-1.5">
                      <span className="font-label-caps text-[9px] text-[#cfc4c5]/60 block tracking-wider">ACTIVATED AGENTS ({sc.agents.length})</span>
                      <div className="flex flex-wrap gap-1.5">
                        {sc.agents.map((ag) => (
                          <span 
                            key={ag} 
                            className={`px-2 py-0.5 rounded-sm font-data-mono text-[9px] border ${
                              state.simulationRunning && state.scenarioId === sc.id
                                ? 'bg-[#00ffcc]/10 border-[#00ffcc]/20 text-[#00ffcc]'
                                : 'bg-white/5 border-white/10 text-[#cfc4c5]'
                            }`}
                          >
                            {ag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Card Action */}
                  <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between gap-4">
                    {state.simulationRunning && state.scenarioId === sc.id ? (
                      <div className="flex items-center gap-2 text-[#00ffcc]">
                        <span className="w-2 h-2 rounded-full bg-[#00ffcc] animate-ping" />
                        <span className="font-label-caps text-[10px] tracking-wider font-bold">ACTIVE SIMULATION</span>
                      </div>
                    ) : (
                      <span className="text-[10px] font-data-mono text-[#cfc4c5]/50">Ready for dispatch</span>
                    )}
                    
                    {sc.id !== 'INC-010' ? (
                      <button
                        onClick={() => handleLaunch(sc.id)}
                        className={`px-5 py-2.5 font-label-caps text-[10px] font-bold rounded-sm active:scale-95 transition-all duration-200 ${
                          state.simulationRunning && state.scenarioId === sc.id
                            ? 'bg-transparent border border-red-500/40 hover:bg-red-950/20 text-red-400'
                            : sc.isFlagship
                              ? 'bg-red-600 text-white hover:bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                              : 'bg-[#c6c6c6] text-[#131313] hover:bg-white'
                        }`}
                      >
                        {state.simulationRunning && state.scenarioId === sc.id ? 'MONITOR RUN' : 'LAUNCH SIMULATION'}
                      </button>
                    ) : (
                      <div className="px-5 py-2.5 border border-white/10 rounded-sm font-label-caps text-[10px] text-white/40 tracking-wider">
                        CLASSIFIED / LOCKED
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Live Webhook Integration Panel */}
            <div className="mt-16 glass-panel p-8 rounded-xl border border-[#4c4546]/30 relative overflow-hidden bg-gradient-to-br from-[#161616] to-[#0f0f0f]">
              <div className="absolute top-0 right-0 p-4 font-data-mono text-[9px] text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
                INTEGRATION LISTENER ACTIVE
              </div>
              
              <div className="mb-6">
                <h3 className="font-display-xl text-xl font-bold text-white mb-2">Enterprise Webhook Integration & Live Investigation</h3>
                <p className="font-body-sm text-xs text-[#cfc4c5] max-w-3xl">
                  Connect your external monitoring infrastructure (e.g. Datadog, PagerDuty, or custom SIEM alerts) directly to our Incident Response Command Center. Any incoming webhook instantly spawns a real-time, multi-agent AI war room.
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Integration Docs */}
                <div className="lg:col-span-6 space-y-4">
                  <div className="p-4 bg-white/5 rounded border border-white/5 space-y-3">
                    <p className="font-label-caps text-[10px] text-white tracking-wider font-bold">1. API WEBHOOK ENDPOINT</p>
                    <div className="bg-[#131313] p-2.5 rounded font-data-mono text-[11px] text-[#00ffcc] select-all border border-white/5">
                      POST http://localhost:8000/api/incident/trigger
                    </div>
                  </div>

                  <div className="p-4 bg-white/5 rounded border border-white/5 space-y-3">
                    <p className="font-label-caps text-[10px] text-white tracking-wider font-bold">2. PAYLOAD SCHEMA (JSON)</p>
                    <pre className="bg-[#131313] p-3 rounded font-data-mono text-[10px] text-[#cfc4c5] overflow-x-auto border border-white/5 select-all">
{`{
  "source": "Datadog",
  "event_type": "Data Breach",
  "severity": "CRITICAL",
  "title": "Unusual DB Outflow Alert",
  "description": "SQL injection exfiltrating PII at 45GB/s."
}`}
                    </pre>
                  </div>

                  <div className="p-4 bg-white/5 rounded border border-white/5 space-y-3">
                    <p className="font-label-caps text-[10px] text-white tracking-wider font-bold">3. EXAMPLE CURL TRIGGER</p>
                    <pre className="bg-[#131313] p-3 rounded font-data-mono text-[10px] text-[#cfc4c5] overflow-x-auto whitespace-pre-wrap break-all border border-white/5 select-all">
{`curl -X POST http://localhost:8000/api/incident/trigger \\
  -H "Content-Type: application/json" \\
  -d '{"source":"PagerDuty","event_type":"Ransomware","severity":"critical","title":"Compromised AD Controller","description":"LockBit ransom note found on AD controller."}'`}
                    </pre>
                  </div>
                </div>

                {/* Webhook Simulator Form */}
                <form onSubmit={handleTriggerWebhook} className="lg:col-span-6 space-y-4 flex flex-col justify-between p-6 bg-white/5 rounded border border-white/5">
                  <div>
                    <p className="font-label-caps text-[10px] text-white tracking-wider font-bold mb-4">LIVE WEBHOOK SIMULATOR</p>
                    
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="font-label-caps text-[9px] text-[#cfc4c5] block mb-1">Alert Source</label>
                        <select 
                          value={webhookSource} 
                          onChange={(e) => setWebhookSource(e.target.value)}
                          className="w-full bg-[#131313] border border-white/10 rounded px-2.5 py-1.5 text-xs text-white font-data-mono focus:border-[#c6c6c6] outline-none"
                        >
                          <option value="Datadog">Datadog</option>
                          <option value="PagerDuty">PagerDuty</option>
                          <option value="Sysdig">Sysdig</option>
                          <option value="CloudWatch">AWS CloudWatch</option>
                          <option value="Custom SIEM">Custom SIEM</option>
                        </select>
                      </div>

                      <div>
                        <label className="font-label-caps text-[9px] text-[#cfc4c5] block mb-1">Event Type</label>
                        <select 
                          value={webhookType} 
                          onChange={(e) => setWebhookType(e.target.value)}
                          className="w-full bg-[#131313] border border-white/10 rounded px-2.5 py-1.5 text-xs text-white font-data-mono focus:border-[#c6c6c6] outline-none"
                        >
                          <option value="Data Breach">Data Breach</option>
                          <option value="Cloud Outage">Cloud Outage</option>
                          <option value="Ransomware">Ransomware</option>
                          <option value="DDoS Attack">DDoS Attack</option>
                          <option value="Custom">Custom Incident</option>
                        </select>
                      </div>
                    </div>

                    <div className="mb-4">
                      <label className="font-label-caps text-[9px] text-[#cfc4c5] block mb-1">Severity</label>
                      <div className="flex gap-4">
                        {['CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
                          <label key={sev} className="flex items-center gap-1.5 cursor-pointer text-xs font-data-mono text-white">
                            <input 
                              type="radio" 
                              name="severity" 
                              value={sev} 
                              checked={webhookSeverity === sev}
                              onChange={() => setWebhookSeverity(sev)}
                              className="accent-red-500"
                            />
                            {sev}
                          </label>
                        ))}
                      </div>
                    </div>

                    <div className="mb-4">
                      <label className="font-label-caps text-[9px] text-[#cfc4c5] block mb-1">Incident Title</label>
                      <input 
                        type="text" 
                        value={webhookTitle} 
                        onChange={(e) => setWebhookTitle(e.target.value)}
                        placeholder="Title of alert..."
                        className="w-full bg-[#131313] border border-white/10 rounded px-3 py-1.5 text-xs text-white placeholder-white/20 focus:border-[#c6c6c6] outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="font-label-caps text-[9px] text-[#cfc4c5] block mb-1">Description</label>
                      <textarea 
                        value={webhookDesc} 
                        onChange={(e) => setWebhookDesc(e.target.value)}
                        placeholder="Detailed payload logs..."
                        rows={2}
                        className="w-full bg-[#131313] border border-white/10 rounded px-3 py-1.5 text-xs text-white placeholder-white/20 focus:border-[#c6c6c6] outline-none resize-none"
                        required
                      />
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    disabled={webhookSubmitting}
                    className={`w-full py-2.5 rounded font-label-caps text-[10px] font-bold tracking-wider transition-all duration-200 active:scale-95 ${
                      webhookSuccess 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-red-600 text-white hover:bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.25)]'
                    }`}
                  >
                    {webhookSubmitting ? 'INGESTING ALERT...' : webhookSuccess ? 'WEBHOOK INGESTED! LAUNCHING WAR ROOM...' : 'SEND WEBHOOK ALERT'}
                  </button>
                </form>
              </div>

              {/* Received Webhook Logs */}
              <div className="mt-8 border-t border-white/5 pt-6">
                <p className="font-label-caps text-[10px] text-white tracking-wider font-bold mb-4 flex items-center gap-2">
                  <Radio size={14} className="text-[#c6c6c6]" />
                  LIVE ALERT LISTENER LOGS
                </p>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-white/5 font-label-caps text-[9px] text-[#cfc4c5]/60 pb-2">
                        <th className="py-2 font-semibold">TIMESTAMP</th>
                        <th className="py-2 font-semibold">INCIDENT ID</th>
                        <th className="py-2 font-semibold">SOURCE</th>
                        <th className="py-2 font-semibold">TITLE</th>
                        <th className="py-2 font-semibold text-center">SEVERITY</th>
                        <th className="py-2 font-semibold">STATUS</th>
                        <th className="py-2 font-semibold text-right">ACTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-data-mono text-xs text-white">
                      {!state.receivedAlerts || state.receivedAlerts.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-xs text-[#cfc4c5] italic">
                            <div className="flex flex-col items-center justify-center gap-2">
                              <span className="w-6 h-6 border-2 border-[#cfc4c5]/20 border-t-emerald-400 rounded-full animate-spin" />
                              Listening for incoming PagerDuty, Datadog, or Simulator webhooks...
                            </div>
                          </td>
                        </tr>
                      ) : (
                        state.receivedAlerts.map((alert) => (
                          <tr key={alert.id} className="hover:bg-white/5 transition-colors">
                            <td className="py-3 text-[11px] text-[#cfc4c5]">
                              {new Date(alert.timestamp).toLocaleTimeString()}
                            </td>
                            <td className="py-3 text-[11px] text-[#00ffcc] font-medium">
                              {alert.id}
                            </td>
                            <td className="py-3 text-[11px] font-bold text-white">
                              {alert.source}
                            </td>
                            <td className="py-3 max-w-[250px] truncate text-xs text-[#cfc4c5]">
                              {alert.title}
                            </td>
                            <td className="py-3 text-center">
                              <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${
                                alert.severity.toUpperCase() === 'CRITICAL' 
                                  ? 'bg-red-500/10 border border-red-500/30 text-red-400' 
                                  : alert.severity.toUpperCase() === 'HIGH' 
                                  ? 'bg-amber-500/10 border border-amber-500/30 text-amber-400' 
                                  : 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400'
                              }`}>
                                {alert.severity.toUpperCase()}
                              </span>
                            </td>
                            <td className="py-3 text-[11px] text-emerald-400 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                              {alert.status}
                            </td>
                            <td className="py-3 text-right">
                              <button 
                                onClick={() => {
                                  focusOnAlert(alert);
                                  scrollToSection('dashboard');
                                }}
                                className="px-3 py-1 border border-white/10 hover:border-white rounded-sm font-label-caps text-[9px] text-[#cfc4c5] hover:text-white transition-all active:scale-95"
                              >
                                FOCUS WAR ROOM
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Section 2: Dashboard */}
        <section id="dashboard" className="scroll-mt-24 w-full pt-16 border-t border-white/10 section-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            {/* Crisis Status Banner */}
            <div className={`relative overflow-hidden glass-panel rounded-xl p-8 border-l-4 ${state.scenarioState === 'INITIAL' ? 'border-[#c6c6c6]/40' : 'border-red-500 glow-error'}`}>
              <div className="scan-line" />
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    {state.scenarioState === 'INITIAL' ? (
                      <CheckCircle size={18} className="text-[#c6c6c6]" />
                    ) : (
                      <AlertCircle size={18} className="text-red-400 animate-bounce" />
                    )}
                    <h2 className={`font-label-caps text-xs tracking-[0.2em] ${state.scenarioState === 'INITIAL' ? 'text-[#c6c6c6]' : 'text-red-400'}`}>
                      {state.scenarioState === 'INITIAL' ? 'SYSTEM STATUS: OPTIMAL' : 'SEVERITY LEVEL: ALPHA-1'}
                    </h2>
                  </div>
                  <h1 className="font-headline-lg text-2xl md:text-3xl font-bold text-white mb-1">
                    {state.scenarioState === 'INITIAL' ? 'Systems Operating Normally' : state.scenarioTitle}
                  </h1>
                  <p className="font-data-mono text-xs text-[#cfc4c5] uppercase">
                    {state.scenarioState === 'INITIAL' ? 'Awaiting scenario activation' : `Incident ID: #${state.scenarioId} | Active: ${state.scenarioState}`}
                  </p>
                </div>
                <div className="flex items-center gap-12">
                  <div className="text-center">
                    <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-1">ACTIVE INCIDENTS</p>
                    <p className="font-display-xl text-3xl font-bold text-white">
                      {state.scenarioState === 'INITIAL' ? '0' : '14'}
                    </p>
                  </div>
                  <div className="h-14 w-[1px] bg-white/10" />
                  <div className="text-center">
                    <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-1">NODES COMPROMISED</p>
                    <p className={`font-display-xl text-3xl font-bold ${state.nodesCompromised > 0 ? 'text-red-400' : 'text-white'}`}>
                      {state.scenarioState === 'INITIAL' ? '00' : String(state.nodesCompromised).padStart(2, '0')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Main metrics + 3D Orb center */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-3 flex flex-col gap-6">
                <div className="glass-panel p-6 rounded-xl relative group overflow-hidden border-t border-[#c6c6c6]/20">
                  <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-4">REVENUE AT RISK</p>
                  <p className="text-3xl font-bold text-white">{state.revenueAtRisk}</p>
                  <div className="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-red-400 transition-all duration-1000" 
                      style={{ width: `${state.scenarioState === 'INITIAL' ? 0 : 78}%` }} 
                    />
                  </div>
                  <p className="font-data-mono text-[10px] text-red-400 mt-2">
                    {state.scenarioState === 'INITIAL' ? 'Stable metrics' : '▲ 12% in last 10m'}
                  </p>
                </div>

                <div className="glass-panel p-6 rounded-xl relative group overflow-hidden border-t border-[#c6c6c6]/20">
                  <div className="absolute inset-0 bg-gradient-to-br from-[#c6c6c6]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-4">AFFECTED USERS</p>
                  <p className="text-3xl font-bold text-white">{state.affectedUsers.toLocaleString()}</p>
                  <div className="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#c6c6c6] transition-all duration-1000" 
                      style={{ width: `${state.scenarioState === 'INITIAL' ? 0 : 45}%` }} 
                    />
                  </div>
                  <p className="font-data-mono text-[10px] text-[#c6c6c6] mt-2">
                    {state.scenarioState === 'INITIAL' ? '0 users affected' : 'STABILIZING'}
                  </p>
                </div>
              </div>

              {/* 3D Orb representation */}
              <div className="lg:col-span-6 glass-panel rounded-xl flex flex-col items-center justify-center relative min-h-[380px]">
                <div className="absolute top-6 left-6">
                  <p className="font-label-caps text-[10px] text-[#c6c6c6] tracking-wider">GLOBAL RISK INDEX</p>
                </div>
                
                {/* Embedded Threejs Severity Orb */}
                <SeverityOrb 
                  severity={state.severity === 'OPTIMAL' ? 'OPTIMAL' : 'OMEGA'} 
                  riskScore={state.riskScore} 
                />

                <div className="absolute bottom-6 right-6 text-right">
                  <p className="font-data-mono text-[9px] text-[#cfc4c5]">AI NEURAL CONFIDENCE</p>
                  <p className="font-label-caps text-xs text-[#c6c6c6] font-bold">
                    {state.scenarioState === 'INITIAL' ? '100% SECURE' : '99.84%'}
                  </p>
                </div>
              </div>

              {/* Regional status */}
              <div className="lg:col-span-3 flex flex-col gap-6">
                <div className="glass-panel p-6 rounded-xl">
                  <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-6">REGIONAL STATUS</p>
                  <div className="space-y-4">
                    {state.regionalStatus.map((region) => (
                      <div key={region.name} className="flex justify-between items-center">
                        <span className="font-data-mono text-xs">{region.name}</span>
                        <span className={`w-3 h-3 rounded-full ${
                          region.status === 'OPTIMAL' ? 'bg-[#c6c6c6] shadow-[0_0_8px_rgba(198,198,198,0.4)]' : 
                          region.status === 'DEGRADED' ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.4)]' : 
                          'bg-red-500 shadow-[0_0_8px_rgba(255,180,171,0.6)]'
                        }`} />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-panel p-6 rounded-xl flex-1 flex flex-col justify-end">
                  <div className="mb-4 opacity-40 grayscale">
                    <img 
                      alt="World Map Visualization" 
                      loading="lazy" 
                      decoding="async" 
                      className="w-full h-32 object-cover rounded" 
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuCZubbDnpr9V1os_VQt8QFxGPoDXNM45xBMrOt_34_LIzzRxrbIs2a9B6Mbw5-0Jg9AIfpV53rGT4kW3Oen6SUKsLKIjgeHyfOgdteMwqjeIbB_73Tj6v1H_3xfkT4_l_DcKnJZctMgoH396M-xinXT8hoOtuLo-Fbblwp_AiQXPn0ozADswfBgkKN0AgcvXl3747mOzzBjiHBr7TpAaS37ADqATZEctXFN4iMBwS8SZ0rhWLhBxS1Y-dwwQyqQ4Q8tzxdl9ubt6ls"
                    />
                  </div>
                  <button 
                    onClick={() => scrollToSection('board_room')}
                    className="w-full py-3 bg-[#c6c6c6] text-[#303030] font-label-caps text-xs font-bold rounded-sm hover:scale-[1.02] active:scale-95 transition-all glow-cyan"
                  >
                    DEPLOY COUNTERMEASURES
                  </button>
                </div>
              </div>
            </div>

            {/* Predictive Outage chart (lazy-loaded) */}
            {state.scenarioState !== 'INITIAL' && (
              <div className="glass-panel p-6 rounded-xl">
                <h3 className="font-label-caps text-xs tracking-wider text-white mb-6">PREDICTIVE IMPACT ANALYSIS (OUTAGE DURATION VS LOSS)</h3>
                <div className="h-64 w-full">
                  <PredictiveChart />
                </div>
              </div>
            )}

            {/* Live operational agents list */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-label-caps text-xs text-white">LIVE AGENT TELEMETRY</h3>
                <span className="font-data-mono text-[9px] text-[#cfc4c5]">COUNT: {state.agents.length} OPERATIONAL</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                {state.agents.map((agent) => {
                  const isWorking = ['THINKING', 'ACTIVE', 'DELEGATING', 'SLEEPING'].includes(agent.status);
                  const statusClass = agent.status.toLowerCase();
                  
                  // Dynamically map icons to agents based on key tags/id
                  const getAgentIcon = (agentId: string) => {
                    const idLower = agentId.toLowerCase();
                    let IconComponent = Shield; // Fallback
                    let animationClass = "";

                    if (idLower.includes('detection')) {
                      IconComponent = Radio;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('sec') || idLower.includes('ciso')) {
                      IconComponent = idLower.includes('ciso') ? ShieldCheck : Shield;
                      if (isWorking) animationClass = "animate-bounce";
                    } else if (idLower.includes('infra') || idLower.includes('cto')) {
                      IconComponent = idLower.includes('cto') ? Database : Cpu;
                      if (isWorking) animationClass = "animate-spin";
                    } else if (idLower.includes('legal')) {
                      IconComponent = Gavel;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('finance') || idLower.includes('cfo')) {
                      IconComponent = idLower.includes('cfo') ? TrendingUp : Coins;
                      if (isWorking) animationClass = "animate-bounce";
                    } else if (idLower.includes('cx')) {
                      IconComponent = Users;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('pr') || idLower.includes('marketing')) {
                      IconComponent = idLower.includes('pr') ? Megaphone : Binary;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('recovery')) {
                      IconComponent = RefreshCw;
                      if (isWorking) animationClass = "animate-spin";
                    } else if (idLower.includes('risk')) {
                      IconComponent = AlertTriangle;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('hr')) {
                      IconComponent = ScanFace;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('ops')) {
                      IconComponent = Activity;
                      if (isWorking) animationClass = "animate-pulse";
                    } else if (idLower.includes('ceo')) {
                      IconComponent = Award;
                      if (isWorking) animationClass = "animate-pulse";
                    }

                    // Slow down spinning icons for aesthetics
                    let style = {};
                    if (animationClass === "animate-spin") {
                      style = { animationDuration: '6s' };
                    }

                    return <IconComponent size={20} className={animationClass} style={style} />;
                  };

                  return (
                    <div 
                      key={agent.id} 
                      className={`glass-panel p-6 rounded-xl border-white/5 hover:border-[#c6c6c6]/20 transition-all ${
                        isWorking ? `agent-card-working state-${statusClass}` : ''
                      }`}
                    >
                      {isWorking && <div className={`agent-scanner-line state-${statusClass}`} />}
                      <div className="relative z-10 flex justify-between items-start mb-6">
                        <div className={`p-3 rounded-lg ${
                          agent.status === 'THINKING' ? 'bg-[#e9a13b]/10 text-[#e9a13b]' :
                          agent.status === 'ACTIVE' || agent.status === 'SLEEPING' ? 'bg-[#00ffcc]/10 text-[#00ffcc]' :
                          agent.status === 'DELEGATING' ? 'bg-[#b55fe6]/10 text-[#b55fe6]' :
                          'bg-white/5 text-[#c6c6c6]'
                        }`}>
                          {getAgentIcon(agent.id)}
                        </div>
                        <div className={`flex items-center gap-1.5 px-2 py-0.5 border rounded-sm ${
                          agent.status === 'THINKING' ? 'border-[#e9a13b]/30 bg-[#e9a13b]/10 text-[#e9a13b]' :
                          agent.status === 'ACTIVE' || agent.status === 'SLEEPING' ? 'border-[#00ffcc]/30 bg-[#00ffcc]/10 text-[#00ffcc]' :
                          agent.status === 'DELEGATING' ? 'border-[#b55fe6]/30 bg-[#b55fe6]/10 text-[#b55fe6]' :
                          'border-white/10 text-[#cfc4c5]'
                        }`}>
                          <span className={`status-pulse-dot ${statusClass}`} />
                          <span className="font-label-caps text-[9px] tracking-wider">{agent.status}</span>
                        </div>
                      </div>
                      <h4 className="relative z-10 font-title-md font-semibold text-white mb-2">{agent.name}</h4>
                      <p className="relative z-10 font-body-sm text-xs text-[#cfc4c5] mb-4">{agent.lastMessage}</p>
                      <div className="relative z-10 flex flex-wrap gap-2">
                        {agent.tags.map((tag) => (
                          <span key={tag} className="px-2 py-0.5 bg-white/5 rounded-sm font-data-mono text-[9px] text-[#cfc4c5]">{tag}</span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </section>

        {/* Section 3: War Room */}
        <section id="war_room" className="scroll-mt-24 w-full pt-16 border-t border-white/10 section-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-6"
          >
            {/* Left sidebar info */}
            <div className="lg:col-span-3 flex flex-col gap-6">
              <div className="glass-panel p-6 rounded-xl">
                <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-4">INCIDENT SHELL PROFILE</p>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full overflow-hidden border border-[#c6c6c6]/30">
                    <img 
                      alt="Commander Profile" 
                      loading="lazy" 
                      decoding="async" 
                      className="w-full h-full object-cover" 
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuCJxl8b7KReGsBi8ki4Ykz3VApkTNzFGMiusNkkDYs4FVexrfvU2nIzus7YUdY016XY-d2IpV44D5e_E6F7JD3jiGrE38wzVD8EA8_AUQkSK4KBZBhYDUaaT6dTveoj9dFuqKLkYCe_r7lOFfjiR5j1h2sQoBYIWRFwWZJQoQuGhLSgRHwiVk-Ldaq19aiLqKu_ueBoKfWQWw4qSxyK34hNM1EtqkFECGkZgKYQ7uK22hnC5cDx6BZV-tdCSspPDHXJA6tpusyPZsM"
                    />
                  </div>
                  <div>
                    <p className="font-data-mono text-sm text-white">OPERATOR_01</p>
                    <p className="font-data-mono text-[9px] text-[#cfc4c5]">LEVEL: ALPHA_CLEARANCE</p>
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded border border-white/5 text-xs text-[#cfc4c5] leading-relaxed">
                  <span className="font-bold text-white block mb-1">SYSTEM NOTE</span>
                  This console displays the real-time interaction logs orchestrated via Band SDK channels.
                </div>
              </div>

              <div className="glass-panel p-6 rounded-xl flex-grow overflow-hidden flex flex-col min-h-[300px] justify-between">
                <div className="flex flex-col flex-grow overflow-hidden">
                  <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-4">BAND BLOCKCHAIN AUDIT LOG</p>
                  <div className="flex-grow overflow-y-auto space-y-4">
                    {state.auditLogs.length === 0 ? (
                      <p className="text-xs text-[#cfc4c5] italic">No logs recorded yet. Start simulation.</p>
                    ) : (
                      state.auditLogs.map((log) => (
                        <div key={log.id} className="text-xs border-b border-white/5 pb-2">
                          <div className="flex justify-between font-data-mono text-[9px] text-[#cfc4c5] mb-1">
                            <span>{log.agent}</span>
                            <span>{log.timestamp}</span>
                          </div>
                          <p className="text-white font-medium mb-0.5">{log.action}</p>
                          <p className="text-[#cfc4c5] text-[10px]">{log.details}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                {state.scenarioState !== 'INITIAL' && (
                  <div className="mt-4 p-4 rounded bg-red-950/20 border border-red-500/20">
                    <p className="font-label-caps text-[10px] text-red-400 mb-2">SYSTEM ALERT</p>
                    <p className="font-body-sm text-[11px] text-[#cfc4c5] leading-tight">Breach in Sector 7G requires immediate attention.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Middle Section: Node network graph */}
            <div className="lg:col-span-6 flex flex-col gap-6">
              {state.scenarioState !== 'INITIAL' && (
                <div className="glass-panel glow-error p-6 flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />
                    <h1 className="font-headline-lg text-lg md:text-xl font-bold text-red-400 tracking-tight">CRITICAL: RANSOMWARE BREACH DETECTED</h1>
                  </div>
                  <div className="flex gap-2">
                    <div className="px-3 py-1 rounded bg-red-500/20 border border-red-500/40 text-red-400 font-data-mono text-xs">PRIORITY: OMEGA</div>
                    <div className="px-3 py-1 rounded bg-[#353535] border border-white/10 text-white font-data-mono text-xs">ELAPSED: 00:04:21</div>
                  </div>
                </div>
              )}
              <NeuralGraph />

              {/* Bottom Panel: Live Timeline */}
              <div className="glass-panel rounded-xl overflow-hidden flex flex-col min-h-[250px]">
                <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/3">
                  <span className="font-label-caps text-xs tracking-widest text-[#c6c6c6]">REAL-TIME INCIDENT TIMELINE</span>
                  <span className="font-data-mono text-[9px] text-[#cfc4c5]">EVENTS LOGGED: {state.timeline.length}</span>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  {state.timeline.length === 0 ? (
                    <p className="text-sm text-[#cfc4c5] italic text-center py-6">Timeline is currently inactive. Run breach simulation.</p>
                  ) : (
                    <div className="space-y-6 relative before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-[2px] before:bg-white/10">
                      {state.timeline.map((event, idx) => (
                        <div key={idx} className="relative pl-8">
                          <div className={`absolute left-0 top-1.5 w-4.5 h-4.5 rounded-full ${event.severity === 'critical' ? 'bg-red-500 ring-4 ring-red-500/20' : 'bg-[#c6c6c6] ring-4 ring-white/10'}`} />
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                            <div>
                              <span className={`font-data-mono text-xs font-bold ${event.severity === 'critical' ? 'text-red-400' : 'text-[#c6c6c6]'}`}>
                                {event.time} - {event.title}
                              </span>
                              <p className="font-body-sm text-xs text-[#cfc4c5] mt-0.5">{event.description}</p>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-white/5 text-[9px] font-data-mono text-[#c6c6c6] border border-white/10 h-fit">
                              {event.module}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right panel: Holographic chats */}
            <div className="lg:col-span-3 glass-panel p-6 rounded-xl flex flex-col h-[780px]">
              <p className="font-label-caps text-[10px] text-[#cfc4c5] mb-6">BAND CHANNEL EXCHANGES</p>
              <div className="flex-1 overflow-y-auto space-y-4">
                {state.scenarioState === 'INITIAL' ? (
                  <div className="h-full flex items-center justify-center text-center p-4">
                    <p className="text-xs text-[#cfc4c5] italic">Start the simulation to launch operational agent communication channels.</p>
                  </div>
                ) : allExchanges.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-center p-4">
                    <p className="text-xs text-[#cfc4c5] italic">Monitoring SDK channels. Waiting for agent check-ins...</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {allExchanges.map((exchange) => (
                      <div
                        key={exchange.id}
                        className={`glass-panel p-4 rounded-xl border-l-4 transition-all duration-300 ${
                          exchange.sentiment === 'critical' ? 'border-red-500/50' :
                          exchange.sentiment === 'alert' ? 'border-yellow-500/50' :
                          exchange.sentiment === 'success' ? 'border-emerald-500/50' :
                          'border-[#c6c6c6]'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className={`font-data-mono text-[10px] ${
                            exchange.sentiment === 'critical' ? 'text-red-400' :
                            exchange.sentiment === 'alert' ? 'text-yellow-400' :
                            exchange.sentiment === 'success' ? 'text-emerald-400' :
                            'text-[#c6c6c6]'
                          }`}>
                            {exchange.agent}
                          </span>
                          <span className="font-data-mono text-[9px] text-[#cfc4c5]">{exchange.time}</span>
                        </div>
                        <p className={`text-xs text-[#e2e2e2] leading-relaxed ${exchange.sentiment === 'critical' ? 'italic' : ''}`}>
                          {exchange.message}
                        </p>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </section>

        {/* Section 4: Board Room */}
        <section id="board_room" className="scroll-mt-24 w-full pt-16 border-t border-white/10 section-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            {/* Decision Workflow Pipeline */}
            <div className="flex flex-col lg:flex-row items-center justify-between gap-4 w-full relative">
              {/* CISO */}
              <div className="flex-1 w-full glass-panel p-6 flex flex-col items-center text-center group cursor-pointer hover:border-red-500/40 transition-all">
                <div className="relative mb-4">
                  {state.scenarioState === 'DEBATE_ACTIVE' && (
                    <div className="absolute inset-0 rounded-full border-2 border-red-500/20 animate-pulse-ring" />
                  )}
                  <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-dashed border-red-500/40 bg-red-950/10 relative group-hover:border-red-500 transition-all glow-error">
                    {/* Spinning outline ring */}
                    <div className="absolute inset-1 rounded-full border border-dotted border-red-500/20 animate-spin" style={{ animationDuration: '8s' }} />
                    {/* Pulsing center background */}
                    <div className="absolute inset-3 rounded-full bg-red-500/5 animate-pulse" />
                    {/* Icon */}
                    <ShieldCheck size={36} className="text-red-400 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  {/* Status dot */}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-red-500 rounded-full border-4 border-black shadow-lg flex items-center justify-center">
                    <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                </div>
                <h3 className="font-title-md font-bold text-white mb-1 text-center text-xs">Chief Information Security Officer Agent</h3>
                <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-3">CONVICTION: 94%</p>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 w-[94%]" />
                </div>
              </div>

              {/* Connector */}
              <div className="flex lg:flex-col items-center justify-center text-white/20 py-1 lg:py-0">
                <span className="lg:hidden"><ChevronDown size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
                <span className="hidden lg:block"><ChevronRight size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
              </div>

              {/* CTO */}
              <div className="flex-1 w-full glass-panel p-6 flex flex-col items-center text-center group cursor-pointer hover:border-amber-500/40 transition-all">
                <div className="relative mb-4">
                  {state.scenarioState === 'DEBATE_ACTIVE' && (
                    <div className="absolute inset-0 rounded-full border-2 border-amber-500/20 animate-pulse-ring" />
                  )}
                  <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-dashed border-amber-500/40 bg-amber-950/10 relative group-hover:border-amber-500 transition-all">
                    {/* Spinning outline ring */}
                    <div className="absolute inset-1 rounded-full border border-dotted border-amber-500/20 animate-spin" style={{ animationDuration: '10s' }} />
                    {/* Pulsing center background */}
                    <div className="absolute inset-3 rounded-full bg-amber-500/5 animate-pulse" />
                    {/* Icon */}
                    <Database size={36} className="text-amber-400 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  {/* Status dot */}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-amber-500 rounded-full border-4 border-black shadow-lg flex items-center justify-center">
                    <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                </div>
                <h3 className="font-title-md font-bold text-white mb-1 text-center text-xs">Chief Technology Architect Agent</h3>
                <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-3">CONVICTION: 75%</p>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 w-[75%]" />
                </div>
              </div>

              {/* Connector */}
              <div className="flex lg:flex-col items-center justify-center text-white/20 py-1 lg:py-0">
                <span className="lg:hidden"><ChevronDown size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
                <span className="hidden lg:block"><ChevronRight size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
              </div>

              {/* CFO */}
              <div className="flex-1 w-full glass-panel p-6 flex flex-col items-center text-center group cursor-pointer hover:border-cyan-500/40 transition-all">
                <div className="relative mb-4">
                  {state.scenarioState === 'DEBATE_ACTIVE' && (
                    <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 animate-pulse-ring" />
                  )}
                  <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-dashed border-cyan-500/40 bg-cyan-950/10 relative group-hover:border-cyan-500 transition-all">
                    {/* Spinning outline ring */}
                    <div className="absolute inset-1 rounded-full border border-dotted border-cyan-500/20 animate-spin" style={{ animationDuration: '12s' }} />
                    {/* Pulsing center background */}
                    <div className="absolute inset-3 rounded-full bg-cyan-500/5 animate-pulse" />
                    {/* Icon */}
                    <TrendingUp size={36} className="text-cyan-400 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  {/* Status dot */}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-cyan-500 rounded-full border-4 border-black shadow-lg flex items-center justify-center">
                    <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                </div>
                <h3 className="font-title-md font-bold text-white mb-1 text-center text-xs">Chief Financial Risk Strategist</h3>
                <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-3">CONVICTION: 42%</p>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-400 w-[42%]" />
                </div>
              </div>

              {/* Connector */}
              <div className="flex lg:flex-col items-center justify-center text-white/20 py-1 lg:py-0">
                <span className="lg:hidden"><ChevronDown size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
                <span className="hidden lg:block"><ChevronRight size={20} className="animate-pulse text-[#c6c6c6]/50" /></span>
              </div>

              {/* CEO */}
              <div className="flex-1 w-full glass-panel p-6 flex flex-col items-center text-center group cursor-pointer hover:border-emerald-500/40 transition-all">
                <div className="relative mb-4">
                  {state.scenarioState === 'DEBATE_ACTIVE' && (
                    <div className="absolute inset-0 rounded-full border-2 border-emerald-500/20 animate-pulse-ring" />
                  )}
                  <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-dashed border-emerald-500/40 bg-emerald-950/10 relative group-hover:border-emerald-500 transition-all glow-cyan">
                    {/* Spinning outline ring */}
                    <div className="absolute inset-1 rounded-full border border-dotted border-emerald-500/20 animate-spin" style={{ animationDuration: '6s' }} />
                    {/* Pulsing center background */}
                    <div className="absolute inset-3 rounded-full bg-emerald-500/5 animate-pulse" />
                    {/* Icon */}
                    <Award size={36} className="text-emerald-400 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  {/* Status dot */}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-4 border-black shadow-lg flex items-center justify-center">
                    <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                </div>
                <h3 className="font-title-md font-bold text-white mb-1 text-center text-xs">Chief Executive Decision Agent</h3>
                <p className="font-label-caps text-[9px] text-[#cfc4c5] mb-3">CONVICTION: 88%</p>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-400 w-[88%]" />
                </div>
              </div>
            </div>

            {/* Debate and Table Matrix */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Real-time debate chat */}
              <div className="lg:col-span-1 glass-panel flex flex-col h-[480px]">
                <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/3">
                  <span className="font-label-caps text-[10px] text-[#c6c6c6] tracking-wider">REAL-TIME C-SUITE DEBATE</span>
                  <span className="flex items-center gap-1 text-[9px] text-[#cfc4c5]"><span className="w-2 h-2 rounded-full bg-[#c6c6c6] animate-pulse" /> SYNCING</span>
                </div>
                <div className="flex-grow overflow-y-auto p-4 space-y-4">
                  {state.debate.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-center p-4">
                      <p className="text-xs text-[#cfc4c5] italic">Debate feed inactive. Kicking off the demo breach will trigger board arguments.</p>
                    </div>
                  ) : (
                    state.debate.map((msg, idx) => (
                      <div key={idx} className={`flex flex-col gap-1.5 ${msg.role === 'CFO' ? 'items-end' : ''}`}>
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-data-mono ${msg.sentiment === 'critical' ? 'text-red-400' : 'text-[#c6c6c6]'}`}>
                            {msg.sender}
                          </span>
                          <span className="text-[9px] text-[#cfc4c5]/50">{msg.timestamp}</span>
                        </div>
                        <div className={`p-3 text-xs leading-relaxed max-w-[85%] ${
                          msg.sentiment === 'critical' ? 'bg-red-500/5 border-l-2 border-red-500 text-white' : 
                          msg.sentiment === 'alert' ? 'bg-yellow-500/5 border-l-2 border-yellow-500 text-white' :
                          'bg-white/5 border border-white/10 rounded-sm text-[#e2e2e2]'
                        }`}>
                          {msg.content}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Decision Matrix Table */}
              <div className="lg:col-span-2 glass-panel flex flex-col overflow-hidden min-h-[400px]">
                <div className="p-4 border-b border-white/5 bg-white/3">
                  <span className="font-label-caps text-[10px] text-[#c6c6c6] tracking-wider">STRATEGIC DECISION MATRIX</span>
                </div>
                <div className="overflow-x-auto flex-grow">
                  <table className="w-full text-left font-data-mono text-xs">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/5">
                        <th className="p-4 text-[#cfc4c5] font-label-caps text-[9px]">DECISION VECTOR</th>
                        <th className="p-4 text-[#cfc4c5] font-label-caps text-[9px]">SHUTDOWN SERVICE OPTION</th>
                        <th className="p-4 text-[#cfc4c5] font-label-caps text-[9px]">ISOLATE NETWORK OPTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      <tr>
                        <td className="p-4 text-white font-bold">Security Risk Containment</td>
                        <td className="p-4"><span className="bg-emerald-950/30 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded text-[9px]">MINIMAL RESIDUAL RISK</span></td>
                        <td className="p-4"><span className="bg-red-950/30 text-red-400 border border-red-500/20 px-2.5 py-1 rounded text-[9px]">CRITICAL SECONDARY VECTORS</span></td>
                      </tr>
                      <tr>
                        <td className="p-4 text-white font-bold">Projected Revenue Loss</td>
                        <td className="p-4"><span className="bg-red-950/30 text-red-400 border border-red-500/20 px-2.5 py-1 rounded text-[9px]">MAXIMUM (EST: $4.2M)</span></td>
                        <td className="p-4"><span className="bg-emerald-950/30 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded text-[9px]">MINIMAL (EST: $500K)</span></td>
                      </tr>
                      <tr>
                        <td className="p-4 text-white font-bold">Recovery Window</td>
                        <td className="p-4 text-[#cfc4c5]">48 - 72 Hours (System boot cycle)</td>
                        <td className="p-4 text-[#cfc4c5]">2 - 6 Hours (Patch rollout)</td>
                      </tr>
                      <tr>
                        <td className="p-4 text-white font-bold">GDPR Liability Exposure</td>
                        <td className="p-4 text-emerald-400">Compliance fully secured</td>
                        <td className="p-4 text-red-400">Ongoing breach window</td>
                      </tr>
                      <tr>
                        <td className="p-4 text-white font-bold">AI Recommendation weighting</td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-white/5 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-[#c6c6c6] h-full w-[72%]" />
                            </div>
                            <span className="text-[9px]">72% Preference</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-white/5 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-red-500 h-full w-[28%]" />
                            </div>
                            <span className="text-[9px]">28% Preference</span>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Operational triggers */}
                <div className="p-4 border-t border-white/5 bg-black/40 flex gap-4">
                  <button 
                    disabled={state.scenarioState !== 'DEBATE_ACTIVE'}
                    onClick={() => deployCountermeasures('SHUTDOWN')}
                    className="flex-1 py-3.5 bg-[#c6c6c6] text-[#303030] font-label-caps text-xs font-bold rounded-sm glow-cyan active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none uppercase"
                  >
                    {state.shutdownLabel || 'EXECUTE SHUTDOWN'}
                  </button>
                  <button 
                    disabled={state.scenarioState !== 'DEBATE_ACTIVE'}
                    onClick={() => deployCountermeasures('ISOLATION')}
                    className="flex-1 py-3.5 border border-[#4c4546] text-[#e2e2e2] font-label-caps text-xs font-bold rounded-sm hover:bg-white/5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none uppercase"
                  >
                    {state.isolationLabel || 'ATTEMPT ISOLATION'}
                  </button>
                </div>
              </div>
            </div>

            {/* Global Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-panel p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                  <Shield size={20} className="text-[#c6c6c6]" />
                </div>
                <div>
                  <p className="text-[10px] font-label-caps text-[#cfc4c5]">THREAT LEVEL</p>
                  <p className="font-data-mono text-xs text-red-400 font-bold">LEVEL 5: BREACH</p>
                </div>
              </div>

              <div className="glass-panel p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                  <Cpu size={20} className="text-[#c6c6c6]" />
                </div>
                <div>
                  <p className="text-[10px] font-label-caps text-[#cfc4c5]">AI NEURAL LOAD</p>
                  <p className="font-data-mono text-xs text-[#c6c6c6] font-bold">82% CAPACITY</p>
                </div>
              </div>

              <div className="glass-panel p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                  <Radar size={20} className="text-[#c6c6c6]" />
                </div>
                <div>
                  <p className="text-[10px] font-label-caps text-[#cfc4c5]">RESPONSE ASSETS</p>
                  <p className="font-data-mono text-xs text-[#c6c6c6] font-bold">READY_STANDBY</p>
                </div>
              </div>
            </div>

            {/* Resolved Post-Mortem Report */}
            {state.postMortem && (
              <div className="glass-panel p-6 rounded-xl border-[#00ffcc]/30 space-y-6">
                <div className="flex justify-between items-center border-b border-white/5 pb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={20} className="text-[#00ffcc]" />
                    <h3 className="font-label-caps text-xs tracking-wider text-white">INCIDENT RESOLVED: POST-MORTEM REPORT</h3>
                  </div>
                  <span className="text-[9px] font-data-mono text-[#00ffcc] bg-[#00ffcc]/10 px-2 py-0.5 rounded border border-[#00ffcc]/20">COMPLIANCE SIGNED</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed text-[#cfc4c5]">
                  <div>
                    <h4 className="font-bold text-white mb-1 uppercase">Root Cause Analysis (RCA)</h4>
                    <p className="mb-4">{state.postMortem.rootCause}</p>
                    <h4 className="font-bold text-white mb-1 uppercase">Timeline Analysis</h4>
                    <p className="mb-4">{state.postMortem.timelineAnalysis}</p>
                    <h4 className="font-bold text-white mb-1 uppercase">Lessons Learned</h4>
                    <p>{state.postMortem.lessonsLearned}</p>
                  </div>
                  <div>
                    <h4 className="font-bold text-white mb-1 uppercase">Business Impact</h4>
                    <p className="mb-4">{state.postMortem.businessImpact}</p>
                    <h4 className="font-bold text-white mb-1 uppercase">Compliance Report</h4>
                    <p className="mb-4">{state.postMortem.complianceReport}</p>
                    <h4 className="font-bold text-white mb-1 uppercase">Future Prevention Plan</h4>
                    <p>{state.postMortem.preventionPlan}</p>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </section>

        {/* Section 5: Simulation Center deleted and moved up */}

      </main>
    </div>
  );
}

export default function page() {
  return (
    <CommandCenterShell />
  );
}
