import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { ModulePsychometrics } from '../types';

interface Props {
  data: ModulePsychometrics;
}

const PsychometricChart: React.FC<Props> = ({ data }) => {
  const [isReady, setIsReady] = React.useState(false);

  // V4.0 FIX: Wait for component mount before rendering chart (prevents width(-1) error)
  React.useEffect(() => {
    // Delay chart render until container has dimensions
    const timer = setTimeout(() => setIsReady(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Guard: Prevent rendering if data is missing
  if (!data || !data.bigFive) {
    return (
      <div className="w-full h-48 flex items-center justify-center text-zinc-500 text-sm" style={{ minHeight: '192px' }}>
        Loading chart data...
      </div>
    );
  }

  // Guard: Wait for container to be ready (prevents Recharts width(-1) error)
  if (!isReady) {
    return (
      <div className="w-full h-48 flex items-center justify-center text-zinc-500 text-sm" style={{ minHeight: '192px' }}>
        <div className="w-4 h-4 border-2 border-zinc-700 border-t-tesla-red rounded-full animate-spin"></div>
      </div>
    );
  }

  const chartData = [
    { subject: 'Opn', A: data.bigFive.openness, fullMark: 100 },
    { subject: 'Con', A: data.bigFive.conscientiousness, fullMark: 100 },
    { subject: 'Ext', A: data.bigFive.extraversion, fullMark: 100 },
    { subject: 'Agr', A: data.bigFive.agreeableness, fullMark: 100 },
    { subject: 'Neu', A: data.bigFive.neuroticism, fullMark: 100 },
  ];

  return (
    // V4.0 FIX: Explicit dimensions + position relative to force layout calculation
    <div className="w-full h-[200px] relative" style={{ minHeight: '200px', minWidth: '200px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
          <PolarGrid stroke="#3f3f46" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
          <Radar
            name="Big 5"
            dataKey="A"
            stroke="#E31937"
            strokeWidth={2}
            fill="#E31937"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PsychometricChart;