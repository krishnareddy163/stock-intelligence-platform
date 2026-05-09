import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { LineChart } from '@/components/charts/LineChart';
import { Colors, Typography, Spacing } from '@/theme';
import type { Stock } from '@/data/stocks';

interface Props {
  stock: Stock;
  rank?: number;
}

export function StockListItem({ stock, rank }: Props) {
  const router = useRouter();
  const change = stock.currentPrice - stock.previousClose;
  const pct = (change / stock.previousClose) * 100;
  const isUp = change >= 0;
  const color = isUp ? Colors.primary : Colors.danger;
  const miniData = stock.priceHistory['1M'];

  return (
    <TouchableOpacity
      style={styles.row}
      activeOpacity={0.7}
      onPress={() => router.push(`/stock/${stock.symbol}`)}
    >
      {rank !== undefined && (
        <Text style={styles.rank}>{rank}</Text>
      )}

      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{stock.symbol.slice(0, 2)}</Text>
      </View>

      <View style={styles.info}>
        <Text style={styles.symbol}>{stock.symbol}</Text>
        <Text style={styles.name} numberOfLines={1}>{stock.name}</Text>
        <View style={styles.sectorRow}>
          <View style={[styles.dot, { backgroundColor: getSectorColor(stock.sector) }]} />
          <Text style={styles.sector}>{stock.sector}</Text>
        </View>
      </View>

      <View style={styles.chart}>
        <LineChart data={miniData.slice(-30)} width={64} height={32} color={color} showGradient={false} />
      </View>

      <View style={styles.priceBlock}>
        <Text style={styles.price}>₹{stock.currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
        <View style={[styles.changePill, { backgroundColor: isUp ? Colors.primaryLight : Colors.dangerLight }]}>
          <Text style={[styles.changeText, { color }]}>
            {isUp ? '▲' : '▼'} {Math.abs(pct).toFixed(2)}%
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

function getSectorColor(sector: string): string {
  const map: Record<string, string> = {
    IT: '#3b82f6', Banking: '#8b5cf6', 'Oil & Gas': '#f59e0b',
    NBFC: '#0ea5e9', Auto: '#f97316', Pharma: '#10b981',
    Consumer: '#ec4899', Metals: '#6366f1',
  };
  return map[sector] ?? Colors.textMuted;
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.card,
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
  },
  rank: {
    width: 22,
    fontSize: Typography.sm,
    color: Colors.textMuted,
    fontWeight: '600',
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#eef2ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  avatarText: {
    fontSize: Typography.sm,
    fontWeight: '700',
    color: '#6366f1',
  },
  info: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  symbol: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.text,
  },
  name: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  sectorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 3,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    marginRight: 4,
  },
  sector: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  chart: {
    marginRight: Spacing.md,
  },
  priceBlock: {
    alignItems: 'flex-end',
    minWidth: 90,
  },
  price: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.text,
  },
  changePill: {
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginTop: 4,
  },
  changeText: {
    fontSize: Typography.xs,
    fontWeight: '600',
  },
});
