import React, { useMemo } from 'react';
import { View } from 'react-native';
import Svg, { Path, Defs, LinearGradient, Stop, Rect } from 'react-native-svg';
import { Colors } from '@/theme';

interface LineChartProps {
  data: number[];
  width: number;
  height: number;
  color?: string;
  showGradient?: boolean;
}

export function LineChart({
  data,
  width,
  height,
  color = Colors.chartLine,
  showGradient = true,
}: LineChartProps) {
  const { linePath, areaPath } = useMemo(() => {
    if (data.length < 2) return { linePath: '', areaPath: '' };

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const padV = height * 0.08;
    const usableH = height - padV * 2;

    const pts = data.map((v, i) => ({
      x: (i / (data.length - 1)) * width,
      y: padV + usableH - ((v - min) / range) * usableH,
    }));

    const smooth = (points: { x: number; y: number }[]) => {
      let d = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const cpx = (prev.x + curr.x) / 2;
        d += ` C ${cpx.toFixed(1)} ${prev.y.toFixed(1)}, ${cpx.toFixed(1)} ${curr.y.toFixed(1)}, ${curr.x.toFixed(1)} ${curr.y.toFixed(1)}`;
      }
      return d;
    };

    const line = smooth(pts);
    const last = pts[pts.length - 1];
    const area = `${line} L ${last.x.toFixed(1)} ${height} L 0 ${height} Z`;

    return { linePath: line, areaPath: area };
  }, [data, width, height]);

  if (!linePath) return <View style={{ width, height }} />;

  return (
    <Svg width={width} height={height}>
      <Defs>
        <LinearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <Stop offset="100%" stopColor={color} stopOpacity="0" />
        </LinearGradient>
      </Defs>
      {showGradient && (
        <Path d={areaPath} fill="url(#grad)" />
      )}
      <Path d={linePath} stroke={color} strokeWidth={2.2} fill="none" strokeLinecap="round" />
    </Svg>
  );
}
