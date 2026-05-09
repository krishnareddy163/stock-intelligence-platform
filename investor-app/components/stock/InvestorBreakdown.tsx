import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { DonutChart } from '@/components/charts/DonutChart';
import { LineChart } from '@/components/charts/LineChart';
import { Card } from '@/components/ui/Card';
import { Colors, Typography, Spacing, Radius } from '@/theme';
import type { ShareholdingQuarter } from '@/data/stocks';

interface Props {
  shareholding: ShareholdingQuarter[];
}

const CATEGORIES = [
  { key: 'promoters', label: 'Promoters',  color: Colors.promoters },
  { key: 'fii',       label: 'FII / FPI',  color: Colors.fii },
  { key: 'dii',       label: 'DII',        color: Colors.dii },
  { key: 'retail',    label: 'Retail',     color: Colors.retail },
];

export function InvestorBreakdown({ shareholding }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const latest = shareholding[shareholding.length - 1];

  const donutData = CATEGORIES.map(c => ({
    label: c.label,
    value: latest[c.key as keyof ShareholdingQuarter] as number,
    color: c.color,
  }));

  const trendData = selected
    ? shareholding.map(q => q[selected as keyof ShareholdingQuarter] as number)
    : null;

  const trendCategory = CATEGORIES.find(c => c.key === selected);

  return (
    <Card style={styles.card}>
      <Text style={styles.title}>Shareholding Pattern</Text>
      <Text style={styles.sub}>As of {latest.quarter}</Text>

      <View style={styles.chartRow}>
        <DonutChart
          data={donutData}
          size={164}
          strokeWidth={28}
          centerLabel={`${latest.promoters}%`}
          centerSub="Promoters"
        />

        <View style={styles.legend}>
          {CATEGORIES.map(c => {
            const val = latest[c.key as keyof ShareholdingQuarter] as number;
            const prev = shareholding[shareholding.length - 2]?.[c.key as keyof ShareholdingQuarter] as number;
            const delta = val - prev;
            const isActive = selected === c.key;
            return (
              <TouchableOpacity
                key={c.key}
                style={[styles.legendItem, isActive && { backgroundColor: '#f8f9fa', borderRadius: 8 }]}
                onPress={() => setSelected(isActive ? null : c.key)}
                activeOpacity={0.7}
              >
                <View style={[styles.dot, { backgroundColor: c.color }]} />
                <View style={styles.legendText}>
                  <Text style={styles.legendLabel}>{c.label}</Text>
                  <Text style={[styles.legendVal, { color: c.color }]}>{val.toFixed(2)}%</Text>
                </View>
                <Text style={[styles.delta, { color: delta >= 0 ? Colors.primary : Colors.danger }]}>
                  {delta >= 0 ? '▲' : '▼'}{Math.abs(delta).toFixed(2)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {selected && trendData && trendCategory && (
        <View style={styles.trendBox}>
          <Text style={[styles.trendTitle, { color: trendCategory.color }]}>
            {trendCategory.label} — 12-Quarter Trend
          </Text>
          <LineChart
            data={trendData}
            width={320}
            height={72}
            color={trendCategory.color}
            showGradient
          />
          <View style={styles.trendLabels}>
            {shareholding.filter((_, i) => i % 3 === 0).map(q => (
              <Text key={q.quarter} style={styles.trendLabel}>{q.quarter.split(' ')[0]}</Text>
            ))}
          </View>
        </View>
      )}

      <View style={styles.historyHeader}>
        <Text style={styles.histTitle}>Quarterly History</Text>
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View>
          <View style={styles.tableHead}>
            {['Quarter', ...CATEGORIES.map(c => c.label)].map(h => (
              <Text key={h} style={[styles.th, h === 'Quarter' ? styles.thWide : null]}>{h}</Text>
            ))}
          </View>
          {[...shareholding].reverse().slice(0, 8).map((q, i) => (
            <View key={q.quarter} style={[styles.tableRow, i % 2 === 0 && styles.tableRowAlt]}>
              <Text style={[styles.td, styles.thWide, { color: Colors.textSecondary }]}>{q.quarter}</Text>
              {CATEGORIES.map(c => (
                <Text key={c.key} style={[styles.td, { color: c.color, fontWeight: '600' }]}>
                  {(q[c.key as keyof ShareholdingQuarter] as number).toFixed(2)}%
                </Text>
              ))}
            </View>
          ))}
        </View>
      </ScrollView>
    </Card>
  );
}

const COL = 88;

const styles = StyleSheet.create({
  card: { marginBottom: Spacing.md },
  title: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text },
  sub: { fontSize: Typography.xs, color: Colors.textMuted, marginTop: 2, marginBottom: Spacing.md },
  chartRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.base },
  legend: { flex: 1, gap: 4 },
  legendItem: { flexDirection: 'row', alignItems: 'center', padding: 6 },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  legendText: { flex: 1 },
  legendLabel: { fontSize: Typography.xs, color: Colors.textSecondary },
  legendVal: { fontSize: Typography.md, fontWeight: '700' },
  delta: { fontSize: 10, fontWeight: '600' },

  trendBox: { marginTop: Spacing.md, backgroundColor: '#f8f9fa', borderRadius: Radius.md, padding: Spacing.md },
  trendTitle: { fontSize: Typography.sm, fontWeight: '600', marginBottom: 8 },
  trendLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  trendLabel: { fontSize: 9, color: Colors.textMuted },

  historyHeader: { marginTop: Spacing.md, marginBottom: Spacing.sm },
  histTitle: { fontSize: Typography.sm, fontWeight: '600', color: Colors.textSecondary },
  tableHead: { flexDirection: 'row', paddingBottom: 6, borderBottomWidth: 1, borderBottomColor: Colors.divider },
  th: { width: COL, fontSize: 10, color: Colors.textMuted, fontWeight: '600', textAlign: 'right' },
  thWide: { width: 90, textAlign: 'left' },
  tableRow: { flexDirection: 'row', paddingVertical: 5 },
  tableRowAlt: { backgroundColor: '#f8fafc' },
  td: { width: COL, fontSize: Typography.xs, textAlign: 'right' },
});
