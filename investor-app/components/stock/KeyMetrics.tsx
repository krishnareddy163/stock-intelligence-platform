import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@/components/ui/Card';
import { Colors, Typography, Spacing } from '@/theme';
import type { Stock } from '@/data/stocks';

function fmt(n: number, prefix = '', suffix = '') {
  if (n >= 1e5) return `${prefix}${(n / 1e5).toFixed(2)}L${suffix}`;
  return `${prefix}${n.toLocaleString('en-IN')}${suffix}`;
}

function fmtCr(n: number) {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)}L Cr`;
  return `₹${(n / 1e5).toFixed(2)}K Cr`;
}

interface MetricItemProps {
  label: string;
  value: string;
  color?: string;
}

function MetricItem({ label, value, color }: MetricItemProps) {
  return (
    <View style={styles.item}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, color ? { color } : null]}>{value}</Text>
    </View>
  );
}

interface Props {
  stock: Stock;
}

export function KeyMetrics({ stock }: Props) {
  const change = stock.currentPrice - stock.previousClose;
  const pct = (change / stock.previousClose) * 100;

  return (
    <Card style={styles.card}>
      <Text style={styles.title}>Key Metrics</Text>
      <View style={styles.grid}>
        <MetricItem label="Market Cap"     value={fmtCr(stock.marketCap)} />
        <MetricItem label="P/E Ratio"      value={stock.peRatio.toFixed(1)} />
        <MetricItem label="P/B Ratio"      value={stock.pbRatio.toFixed(1)} />
        <MetricItem label="EPS (TTM)"      value={`₹${stock.eps.toFixed(2)}`} />
        <MetricItem label="ROE"            value={`${stock.roe.toFixed(1)}%`} color={stock.roe > 15 ? Colors.primary : Colors.warning} />
        <MetricItem label="Div. Yield"     value={`${stock.dividendYield.toFixed(2)}%`} color={Colors.fii} />
        <MetricItem label="Debt/Equity"    value={stock.debtToEquity.toFixed(2)} color={stock.debtToEquity > 1 ? Colors.danger : Colors.primary} />
        <MetricItem label="Beta"           value={stock.beta.toFixed(2)} />
        <MetricItem label="52W High"       value={`₹${stock.high52w.toLocaleString('en-IN')}`} color={Colors.primary} />
        <MetricItem label="52W Low"        value={`₹${stock.low52w.toLocaleString('en-IN')}`} color={Colors.danger} />
        <MetricItem label="Open"           value={`₹${stock.open.toLocaleString('en-IN')}`} />
        <MetricItem label="Prev. Close"    value={`₹${stock.previousClose.toLocaleString('en-IN')}`} />
      </View>

      <View style={styles.rangeRow}>
        <Text style={styles.rangeLabel}>52W Range</Text>
        <View style={styles.rangeBar}>
          <View
            style={[
              styles.rangeFill,
              {
                left: `${((stock.low52w / stock.high52w) * 100).toFixed(1)}%` as any,
                width: `${(((stock.currentPrice - stock.low52w) / (stock.high52w - stock.low52w)) * 100).toFixed(1)}%` as any,
              },
            ]}
          />
          <View
            style={[
              styles.rangeThumb,
              {
                left: `${(((stock.currentPrice - stock.low52w) / (stock.high52w - stock.low52w)) * 100).toFixed(1)}%` as any,
              },
            ]}
          />
        </View>
        <View style={styles.rangeEnds}>
          <Text style={[styles.rangeEnd, { color: Colors.danger }]}>₹{stock.low52w.toLocaleString('en-IN')}</Text>
          <Text style={[styles.rangeEnd, { color: Colors.primary }]}>₹{stock.high52w.toLocaleString('en-IN')}</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: Spacing.md },
  title: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text, marginBottom: Spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 0 },
  item: {
    width: '50%',
    paddingVertical: 10,
    paddingRight: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
  },
  label: { fontSize: Typography.xs, color: Colors.textMuted },
  value: { fontSize: Typography.md, fontWeight: '600', color: Colors.text, marginTop: 2 },
  rangeRow: { marginTop: Spacing.md },
  rangeLabel: { fontSize: Typography.xs, color: Colors.textMuted, marginBottom: 8 },
  rangeBar: {
    height: 6,
    backgroundColor: '#e2e8f0',
    borderRadius: 3,
    position: 'relative',
    overflow: 'visible',
  },
  rangeFill: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    backgroundColor: Colors.primary,
    borderRadius: 3,
    opacity: 0.5,
  },
  rangeThumb: {
    position: 'absolute',
    top: -4,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: Colors.primary,
    borderWidth: 2,
    borderColor: Colors.card,
    marginLeft: -7,
  },
  rangeEnds: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  rangeEnd: { fontSize: Typography.xs, fontWeight: '600' },
});
