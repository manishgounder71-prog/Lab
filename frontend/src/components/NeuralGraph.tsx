'use client';

import React, { useState, useCallback, useMemo, memo } from 'react';
import { useCommandCenter } from '../context/CommandCenterContext';
import { motion } from 'framer-motion';
import { 
  Shield, Cpu, Gavel, Coins, Users, Megaphone, Award, TrendingUp, 
  ShieldCheck, Activity, Radio, Database, RefreshCw, AlertTriangle, 
  ScanFace, Binary, ZoomIn, ZoomOut, Maximize2, GitFork, Play, Grid
} from 'lucide-react';
import type { AgentInfo } from '../context/CommandCenterContext';

// ─── Static lookup tables (never re-created) ────────────────────────────────
const AGENT_ICONS: Record<string, React.ComponentType<{ className?: string; size?: number }>> = {
  detection: Radio, sec: Shield, infra: Cpu, legal: Gavel, finance: Coins,
  cx: Users, pr: Megaphone, recovery: RefreshCw, risk: AlertTriangle,
  hr: ScanFace, ops: Activity, marketing: Binary, cto: Database,
  ceo: Award, cfo: TrendingUp, ciso: ShieldCheck,
};

interface NodePosition {
  x: number;
  y: number;
  theme: 'red' | 'amber' | 'cyan' | 'emerald' | 'blue';
}

const AGENT_POSITIONS: Record<string, NodePosition> = {
  detection: { x: 120, y: 280, theme: 'blue' },
  sec:       { x: 340, y: 180, theme: 'red' },
  infra:     { x: 340, y: 380, theme: 'amber' },
  legal:     { x: 560, y: 130, theme: 'blue' },
  cx:        { x: 560, y: 280, theme: 'blue' },
  finance:   { x: 560, y: 430, theme: 'cyan' },
  ciso:      { x: 780, y: 130, theme: 'red' },
  cfo:       { x: 780, y: 280, theme: 'cyan' },
  pr:        { x: 780, y: 430, theme: 'blue' },
  ceo:       { x: 1000, y: 280, theme: 'emerald' },
};

const CONNECTIONS = [
  { from: 'detection', to: 'sec' },
  { from: 'detection', to: 'infra' },
  { from: 'sec', to: 'legal' },
  { from: 'sec', to: 'finance' },
  { from: 'infra', to: 'cx' },
  { from: 'legal', to: 'ciso' },
  { from: 'legal', to: 'pr' },
  { from: 'finance', to: 'cfo' },
  { from: 'cx', to: 'pr' },
  { from: 'ciso', to: 'ceo' },
  { from: 'cfo', to: 'ceo' },
  { from: 'pr', to: 'ceo' },
] as const;

const STAGE_HEADERS = [
  { x: 120, name: '01 | INGESTION' },
  { x: 340, name: '02 | TRIAGE' },
  { x: 560, name: '03 | ANALYSIS' },
  { x: 780, name: '04 | ADVISORY' },
  { x: 1000, name: '05 | BOARD ROOM' },
] as const;

const THEME_COLORS = {
  blue:    { border: 'group-hover:border-blue-500/50',    bar: 'bg-blue-500',    glow: 'shadow-[0_0_10px_rgba(59,130,246,0.1)]' },
  red:     { border: 'group-hover:border-red-500/50',     bar: 'bg-red-500',     glow: 'shadow-[0_0_10px_rgba(239,68,68,0.1)]' },
  amber:   { border: 'group-hover:border-amber-500/50',   bar: 'bg-amber-500',   glow: 'shadow-[0_0_10px_rgba(245,158,11,0.1)]' },
  cyan:    { border: 'group-hover:border-cyan-500/50',    bar: 'bg-cyan-500',    glow: 'shadow-[0_0_10px_rgba(6,182,212,0.1)]' },
  emerald: { border: 'group-hover:border-emerald-500/50', bar: 'bg-emerald-500', glow: 'shadow-[0_0_10px_rgba(16,185,129,0.1)]' },
} as const;

const WORKING_STATES = new Set(['THINKING', 'ACTIVE', 'DELEGATING', 'SLEEPING']);
const NODE_WIDTH = 200;
const NODE_HEIGHT = 98;
const SPRING_TRANSITION = { type: 'spring', stiffness: 400, damping: 20 } as const;

// ─── Pure utility ────────────────────────────────────────────────────────────
function getBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const controlOffset = Math.abs(x2 - x1) / 2;
  return `M ${x1} ${y1} C ${x1 + controlOffset} ${y1}, ${x2 - controlOffset} ${y2}, ${x2} ${y2}`;
}

function getStatusBorder(status: string): string {
  switch (status) {
    case 'THINKING':   return 'border-[#e9a13b]/40 glow-thinking';
    case 'ACTIVE':     return 'border-[#00ffcc]/40 glow-active';
    case 'DELEGATING': return 'border-[#b55fe6]/40 glow-delegating';
    case 'SLEEPING':   return 'border-[#00ffcc]/35 glow-active';
    default:           return 'border-white/10';
  }
}

function getPortColor(status: string): string {
  switch (status) {
    case 'THINKING':   return 'bg-[#e9a13b] shadow-[0_0_8px_#e9a13b] port-pulse';
    case 'ACTIVE':
    case 'SLEEPING':   return 'bg-[#00ffcc] shadow-[0_0_8px_#00ffcc] port-pulse';
    case 'DELEGATING': return 'bg-[#b55fe6] shadow-[0_0_8px_#b55fe6] port-pulse';
    default:           return 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)] port-pulse';
  }
}

function getIconContainerClass(status: string): string {
  switch (status) {
    case 'THINKING':   return 'bg-[#e9a13b]/10 text-[#e9a13b]';
    case 'ACTIVE':
    case 'SLEEPING':   return 'bg-[#00ffcc]/10 text-[#00ffcc]';
    case 'DELEGATING': return 'bg-[#b55fe6]/10 text-[#b55fe6]';
    default:           return 'bg-white/5 text-[#c6c6c6]';
  }
}

// ─── Memoized sub-components ─────────────────────────────────────────────────

/** Offline / non-participating node placeholder */
const OfflineNode = memo(function OfflineNode({ agentId, pos }: { agentId: string; pos: NodePosition }) {
  return (
    <div
      onPointerDown={(e) => e.stopPropagation()}
      className="absolute rounded border border-white/5 bg-[#171717]/40 opacity-20 filter grayscale select-none"
      style={{ left: pos.x - NODE_WIDTH / 2, top: pos.y - NODE_HEIGHT / 2, width: NODE_WIDTH, height: NODE_HEIGHT }}
    >
      <div className="h-1 bg-neutral-700 w-full" />
      <div className="p-3 flex gap-2.5 items-center">
        <div className="p-1.5 bg-white/5 rounded text-neutral-500"><Cpu size={14} /></div>
        <div className="flex flex-col min-w-0">
          <span className="text-[10px] font-bold text-neutral-500 tracking-tight capitalize truncate">{agentId} Agent</span>
          <span className="text-[8px] text-neutral-600 uppercase mt-0.5 tracking-wider">OFFLINE</span>
        </div>
      </div>
    </div>
  );
});

/** Active agent node card */
const AgentNode = memo(function AgentNode({
  agent,
  pos,
  isHovered,
  onHover,
  onLeave,
}: {
  agent: AgentInfo;
  pos: NodePosition;
  isHovered: boolean;
  onHover: () => void;
  onLeave: () => void;
}) {
  const isWorking = WORKING_STATES.has(agent.status);
  const statusClass = agent.status.toLowerCase();
  const themeColors = THEME_COLORS[pos.theme];
  const IconComponent = AGENT_ICONS[agent.id] || Shield;
  const statusBorder = getStatusBorder(agent.status);
  const isPortActive = isWorking || isHovered;
  const portClass = isPortActive ? getPortColor(agent.status) : '';

  return (
    <motion.div
      onPointerDown={(e) => e.stopPropagation()}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      onFocus={onHover}
      onBlur={onLeave}
      tabIndex={0}
      role="button"
      aria-label={`Agent: ${agent.name}, Role: ${agent.role}, Status: ${agent.status}`}
      className={`absolute rounded bg-[#131313]/95 border ${statusBorder} flex flex-col justify-between overflow-hidden shadow-2xl transition-all duration-300 z-10 group cursor-pointer`}
      style={{ left: pos.x - NODE_WIDTH / 2, top: pos.y - NODE_HEIGHT / 2, width: NODE_WIDTH, height: NODE_HEIGHT }}
      whileHover={{ scale: 1.05 }}
      transition={SPRING_TRANSITION}
    >
      {/* Horizontal scanner bar overlay when working */}
      {isWorking && <div className={`agent-scanner-line state-${statusClass}`} />}

      {/* Node Top Header Stage Color Bar */}
      <div className={`h-[3px] w-full ${themeColors.bar}`} />

      {/* Node Card Core Content */}
      <div className="p-2.5 flex-1 flex flex-col justify-between relative">
        {/* Connection Handles */}
        <div className={`w-2 h-2 rounded-full absolute -left-[4.5px] top-1/2 -translate-y-1/2 border border-black/85 shadow-md transition-all duration-300 z-30 ${isPortActive ? portClass : 'bg-neutral-600'}`} />
        <div className={`w-2 h-2 rounded-full absolute -right-[4.5px] top-1/2 -translate-y-1/2 border border-black/85 shadow-md transition-all duration-300 z-30 ${isPortActive ? portClass : 'bg-emerald-500'}`} />

        <div className="flex gap-2 min-w-0">
          <div className={`p-1.5 rounded h-fit ${getIconContainerClass(agent.status)}`}>
            <IconComponent size={14} className={isWorking ? 'animate-pulse' : ''} />
          </div>
          <div className="flex flex-col min-w-0 leading-tight">
            <span className="text-[10px] font-bold text-white tracking-tight truncate">{agent.name}</span>
            <span className="text-[8px] text-[#cfc4c5]/60 uppercase tracking-tighter truncate mt-0.5">{agent.role}</span>
          </div>
        </div>

        {/* Agent latest trace log */}
        <div className="mt-1 text-[8px] text-[#cfc4c5] font-data-mono truncate bg-black/30 px-1 py-0.5 rounded-sm">
          {agent.lastMessage}
        </div>

        {/* Processing progress bar when working */}
        {isWorking && (
          <div className="w-full h-[2px] bg-white/5 rounded-full mt-1.5 overflow-hidden relative">
            <div className={`h-full rounded-full progress-bar-fill state-${statusClass}`} />
          </div>
        )}
      </div>

      {/* Node Card Bottom Status Bar */}
      <div className="px-2.5 py-1 border-t border-white/5 flex justify-between items-center bg-[#0d0d0d] relative z-10">
        <div className="flex items-center gap-1">
          <span className={`status-pulse-dot ${statusClass}`} />
          <span className="text-[7px] font-label-caps tracking-wide text-neutral-400">{agent.status}</span>
        </div>
        <span className="text-[7px] font-data-mono text-neutral-600">ID: {agent.id.slice(0, 5)}</span>
      </div>
    </motion.div>
  );
});

// ─── Main Component ──────────────────────────────────────────────────────────
export default function NeuralGraph() {
  const { state, startDemo } = useCommandCenter();
  const [zoom, setZoom] = useState(0.85);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [showGrid, setShowGrid] = useState(true);

  // Build a quick lookup map instead of .find() per connection
  const agentsById = useMemo(() => {
    const map = new Map<string, AgentInfo>();
    for (const a of state.agents) map.set(a.id, a);
    return map;
  }, [state.agents]);

  const handleZoomIn  = useCallback(() => setZoom(prev => Math.min(prev + 0.05, 1.3)), []);
  const handleZoomOut = useCallback(() => setZoom(prev => Math.max(prev - 0.05, 0.6)), []);
  const handleResetZoom = useCallback(() => setZoom(0.85), []);
  const handleResetView = useCallback(() => { setZoom(0.85); setPanOffset({ x: 0, y: 0 }); }, []);
  const handleToggleGrid = useCallback(() => setShowGrid(prev => !prev), []);

  const handlePointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
    e.currentTarget.setPointerCapture(e.pointerId);
  }, [panOffset]);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    setPanOffset({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  }, [isDragging, dragStart]);

  const handlePointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    setIsDragging(false);
    e.currentTarget.releasePointerCapture(e.pointerId);
  }, []);

  return (
    <div className="relative w-full h-[620px] glass-panel rounded-xl border-[#4c4546]/30 overflow-hidden flex flex-col justify-between bg-black/40 shadow-[0_0_20px_rgba(0,0,0,0.4)]">
      {/* n8n top status and control bar */}
      <div className="p-4 border-b border-white/5 flex justify-between items-center bg-[#131313]/90 z-20 select-none">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded border border-emerald-500/30 text-emerald-400">
            <GitFork size={16} />
          </div>
          <div className="flex flex-col">
            <span className="font-label-caps text-xs tracking-widest text-[#c6c6c6] font-bold">MULTI-AGENT WORKFLOW ORCHESTRATOR</span>
            <span className="font-data-mono text-[9px] text-[#cfc4c5]/75">MODEL: BAND_SDK_V4 | ACTIVE LINKS: {CONNECTIONS.length}</span>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2">
          <div className="flex bg-white/5 border border-white/10 rounded-sm overflow-hidden mr-2" role="toolbar" aria-label="Neural graph controls">
            <button onClick={handleToggleGrid} className={`p-2 hover:bg-white/10 transition-colors border-r border-white/10 ${showGrid ? 'text-emerald-400' : 'text-neutral-500'}`} title="Toggle Grid" aria-label="Toggle background grid" aria-pressed={showGrid}>
              <Grid size={14} />
            </button>
            <button onClick={handleResetView} className="p-2 hover:bg-white/10 text-[#c6c6c6] transition-colors border-r border-white/10" title="Reset View & Pan" aria-label="Reset view and pan position">
              <Maximize2 size={14} />
            </button>
            <button onClick={handleZoomIn} className="p-2 hover:bg-white/10 text-[#c6c6c6] transition-colors border-r border-white/10" title="Zoom In" aria-label="Zoom in on graph">
              <ZoomIn size={14} />
            </button>
            <button onClick={handleZoomOut} className="p-2 hover:bg-white/10 text-[#c6c6c6] transition-colors border-r border-white/10" title="Zoom Out" aria-label="Zoom out on graph">
              <ZoomOut size={14} />
            </button>
            <button onClick={handleResetZoom} className="p-2 hover:bg-white/10 text-[#c6c6c6] transition-colors text-xs font-data-mono" title="Reset Zoom" aria-label={`Reset zoom to ${Math.round(zoom * 100)}%`}>
              {Math.round(zoom * 100)}%
            </button>
          </div>

          {!state.simulationRunning && (
            <button
              onClick={startDemo}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-black rounded-sm font-label-caps text-[10px] font-bold transition-all shadow-[0_0_10px_rgba(16,185,129,0.2)]"
              aria-label="Trigger agent workflow flow"
            >
              <Play size={10} fill="black" /> TRIGGER FLOW
            </button>
          )}
        </div>
      </div>

      {/* Infinite Canvas Window */}
      <div 
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        className={`flex-1 w-full relative overflow-hidden bg-[#0c0c0c] select-none cursor-grab active:cursor-grabbing ${showGrid ? 'dot-grid' : ''}`}
        style={{ backgroundPosition: `${panOffset.x}px ${panOffset.y}px` }}
      >
        {/* Dynamic Zoom & Pan Wrapper */}
        <div 
          className={`absolute inset-0 ${isDragging ? '' : 'transition-transform duration-200'}`}
          style={{ 
            transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoom})`, 
            transformOrigin: 'center center',
            width: '1120px', height: '560px',
            left: 'calc(50% - 560px)', top: 'calc(50% - 280px)',
          }}
        >
          {/* SVG Connection Cables */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
            <defs>
              <linearGradient id="flow-grad-active" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00ffcc" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#ffb4ab" stopOpacity="0.4" />
              </linearGradient>
            </defs>

            {/* Stage Headers & Divider Lines */}
            {STAGE_HEADERS.map((stage, idx) => (
              <g key={idx} role="img" aria-label={`Stage ${idx + 1}: ${stage.name}`}>
                <text x={stage.x} y={40} textAnchor="middle" className="font-data-mono text-[9px] font-bold fill-[#cfc4c5]/30 tracking-widest uppercase">
                  {stage.name}
                </text>
                {idx < 4 && (
                  <line x1={stage.x + 110} y1={20} x2={stage.x + 110} y2={540} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" strokeDasharray="4, 6" />
                )}
              </g>
            ))}

            {CONNECTIONS.map((conn) => {
              const startPos = AGENT_POSITIONS[conn.from];
              const endPos = AGENT_POSITIONS[conn.to];
              if (!startPos || !endPos) return null;

              const x1 = startPos.x + NODE_WIDTH / 2;
              const y1 = startPos.y;
              const x2 = endPos.x - NODE_WIDTH / 2;
              const y2 = endPos.y;

              const fromAgent = agentsById.get(conn.from);
              const toAgent   = agentsById.get(conn.to);
              const isSourceWorking = !!fromAgent && WORKING_STATES.has(fromAgent.status);
              const isCableConnected = !!fromAgent && !!toAgent;

              const pathId = `cable-${conn.from}-${conn.to}`;
              const bezierPath = getBezierPath(x1, y1, x2, y2);
              const isHovered = hoveredNodeId === conn.from || hoveredNodeId === conn.to;
              const isHighlight = isSourceWorking || isHovered;

              return (
                <g key={pathId}>
                  {/* Cable outer glow */}
                  <path
                    d={bezierPath}
                    fill="none"
                    stroke={isHighlight ? (isHovered ? 'rgba(0, 255, 204, 0.25)' : 'rgba(0, 255, 204, 0.12)') : 'rgba(255, 255, 255, 0.02)'}
                    strokeWidth={isHighlight ? 5 : 2}
                    className="transition-all duration-300"
                  />
                  {/* Cable wire */}
                  <path
                    id={pathId}
                    d={bezierPath}
                    fill="none"
                    stroke={isHighlight ? 'url(#flow-grad-active)' : isCableConnected ? 'rgba(198, 198, 198, 0.15)' : 'rgba(255, 255, 255, 0.05)'}
                    strokeWidth={isHighlight ? (isHovered ? 2.5 : 2) : 1.5}
                    strokeDasharray="4, 6"
                    className={`transition-all duration-300 ${isSourceWorking ? 'cable-flow-active' : ''} ${isHovered ? 'cable-highlight' : ''}`}
                  />
                  {/* Flowing Staggered Data Particles - reduced for performance */}
                  {isHighlight && (
                    <>
                      {/* Single particle pair instead of two pairs */}
                      <circle r="4" fill="#00ffcc" opacity="0.35">
                        <animateMotion dur={isHovered ? '1.6s' : '3s'} repeatCount="indefinite">
                          <mpath href={`#${pathId}`} />
                        </animateMotion>
                      </circle>
                      <circle r="2" fill="#ffb4ab" opacity="0.5">
                        <animateMotion dur={isHovered ? '1.6s' : '3s'} begin="0.8s" repeatCount="indefinite">
                          <mpath href={`#${pathId}`} />
                        </animateMotion>
                      </circle>
                    </>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Render Agent Nodes */}
          {Object.entries(AGENT_POSITIONS).map(([agentId, pos]) => {
            const agent = agentsById.get(agentId);
            if (!agent) return <OfflineNode key={agentId} agentId={agentId} pos={pos} />;

            return (
              <AgentNode
                key={agent.id}
                agent={agent}
                pos={pos}
                isHovered={hoveredNodeId === agent.id}
                onHover={() => setHoveredNodeId(agent.id)}
                onLeave={() => setHoveredNodeId(null)}
              />
            );
          })}
        </div>

        {/* Cinematic Vignette Overlay */}
        <div className="absolute inset-0 canvas-vignette pointer-events-none z-20" />
      </div>

      {/* Workspace Footer trace bar */}
      <div className="p-3 border-t border-white/5 bg-[#131313]/90 text-center font-data-mono text-[9px] text-[#cfc4c5] z-20">
        DRAG CANVAS TO PAN | SCROLL OR USE CONTROLS TO ZOOM | HOVER NODE TO HIGHLIGHT FLOW &amp; SPEED UP PACKETS
      </div>
    </div>
  );
}
