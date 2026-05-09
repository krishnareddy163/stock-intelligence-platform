import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors, Typography, Radius, Shadow } from '@/theme';

const SECTOR_ICONS: Record<string, string> = {
  IT: '💻', Banking: '🏦', Auto: '🚗', Pharma: '💊',
  FMCG: '🛒', Metals: '⚙️', Energy: '⚡', Realty: '🏗️',
};

interface Props {
  name: string;
  change: string;
  up: boolean;
  count: number;
}

export function SectorCard({ name, change, up, count }: Props) {
  const color = up ? Colors.primary : Colors.danger;
  return (
    <TouchableOpacity activeOpacity={0.8} style={styles.card}>
      <Text style={styles.icon}>{SECTOR_ICONS[name] ?? '📊'}</Text>
      <Text style={styles.name}>{name}</Text>
      <Text style={[styles.change, { color }]}>{change}</Text>
      <Text style={styles.count}>{count} stocks</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 88,
    backgroundColor: Colors.card,
    borderRadius: Radius.lg,
    padding: 12,
    marginRight: 10,
    alignItems: 'center',
    ...Shadow.sm,
  },
  icon: { fontSize: 22, marginBottom: 4 },
  name: { fontSize: Typography.xs, fontWeight: '700', color: Colors.text, textAlign: 'center' },
  change: { fontSize: Typography.xs, fontWeight: '600', marginTop: 2 },
  count: { fontSize: 9, color: Colors.textMuted, marginTop: 1 },
});
