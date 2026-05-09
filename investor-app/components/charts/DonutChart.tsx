import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { G, Path, Circle } from 'react-native-svg';

export interface DonutSlice {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DonutSlice[];
  size?: number;
  strokeWidth?: number;
  centerLabel?: string;
  centerSub?: string;
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, start: number, end: number): string {
  const s = polarToCartesian(cx, cy, r, start);
  const e = polarToCartesian(cx, cy, r, end);
  const large = end - start > 180 ? 1 : 0;
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`;
}

export function DonutChart({
  data,
  size = 160,
  strokeWidth = 26,
  centerLabel,
  centerSub,
}: DonutChartProps) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - strokeWidth) / 2;

  const slices = useMemo(() => {
    let cursor = 0;
    return data.map(d => {
      const sweep = (d.value / total) * 358; // 358 leaves a tiny gap
      const start = cursor;
      cursor += sweep;
      return { ...d, start, end: cursor };
    });
  }, [data, total]);

  return (
    <View style={styles.wrapper}>
      <Svg width={size} height={size}>
        <Circle cx={cx} cy={cy} r={r} stroke="#f1f5f9" strokeWidth={strokeWidth} fill="none" />
        <G>
          {slices.map((s, i) => (
            <Path
              key={i}
              d={arcPath(cx, cy, r, s.start, s.end)}
              stroke={s.color}
              strokeWidth={strokeWidth}
              fill="none"
              strokeLinecap="round"
            />
          ))}
        </G>
      </Svg>
      {(centerLabel || centerSub) && (
        <View style={[styles.center, { width: size, height: size }]}>
          {centerLabel && <Text style={styles.centerLabel}>{centerLabel}</Text>}
          {centerSub && <Text style={styles.centerSub}>{centerSub}</Text>}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a2e',
  },
  centerSub: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 2,
  },
});
