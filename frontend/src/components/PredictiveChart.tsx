'use client';

// Standalone chart component so Recharts is only loaded when needed
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

const predictiveData = [
  { name: '1h Outage', revenue: 1.2, fines: 0.1 },
  { name: '4h Outage', revenue: 4.8, fines: 0.5 },
  { name: '8h Outage', revenue: 9.6, fines: 1.5 },
  { name: '24h Outage', revenue: 28.8, fines: 4.0 },
];

export default function PredictiveChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={predictiveData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <XAxis dataKey="name" stroke="#cfc4c5" fontSize={11} tickLine={false} />
        <YAxis stroke="#cfc4c5" fontSize={11} tickLine={false} />
        <Tooltip contentStyle={{ backgroundColor: '#131313', border: '1px solid rgba(255,255,255,0.1)' }} />
        <Area type="monotone" dataKey="revenue" stackId="1" stroke="#ffb4ab" fill="rgba(255, 180, 171, 0.2)" name="Loss ($M)" />
        <Area type="monotone" dataKey="fines" stackId="2" stroke="#c6c6c6" fill="rgba(198, 198, 198, 0.2)" name="Fines ($M)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
