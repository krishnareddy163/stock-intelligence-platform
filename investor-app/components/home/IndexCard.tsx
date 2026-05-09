import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { LineChart } from '@/components/charts/LineChart';
import { Colors, Typography, Spacing, Radius, Shadow } from '@/theme';

interface Props {
  name: string;
  value: string;
  change: string;
  pct: string;
  up: boolean;
  sparkData: number[];
}

export function IndexCard({ name, value, change, pct, up, sparkData }: Props) {
  const color = up ? Colors.primary : Colors.danger;
  return (
    <TouchableOpacity activeOpacity={0.85} style={styles.card}>
      <View style={styles.top}>
        <Text style={styles.name}>{name}</Text>
        <View style={[styles.badge, { backgroundColor: up ? Colors.primaryLight : Colors.dangerLight }]}>
          <Text style={[styles.pct, { color }]}>{pct}</Text>
        </View>
      </View>
      <Text style={styles.value}>{value}</Text>
      <Text style={[styles.change, { color }]}>{change}</Text>
      <View style={styles.chart}>
        <LineChart data={sparkData} width={140} height={40} color={color} showGradient />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.card,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    width: 160,
    marginRight: Spacing.md,
    ...Shadow.sm,
  },
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  name: { fontSize: Typography.xs, color: Colors.textSecondary, fontWeight: '600', flex: 1 },
  badge: { borderRadius: Radius.full, paddingHorizontal: 6, paddingVertical: 2 },
  pct: { fontSize: 10, fontWeight: '700' },
  value: { fontSize: Typography.xl, fontWeight: '800', color: Colors.text },
  change: { fontSize: Typography.xs, fontWeight: '500', marginTop: 2 },
  chart: { marginTop: 8 },
});
