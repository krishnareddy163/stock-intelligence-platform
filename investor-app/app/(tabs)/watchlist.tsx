import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, ScrollView,
  TouchableOpacity, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { StockListItem } from '@/components/stock/StockListItem';
import { Colors, Typography, Spacing, Radius, Shadow } from '@/theme';
import { STOCKS } from '@/data/stocks';

const DEFAULT_WATCHLIST = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'TATAMOTORS'];

export default function WatchlistScreen() {
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_WATCHLIST);

  const watchStocks = STOCKS.filter(s => symbols.includes(s.symbol));
  const totalInvested = watchStocks.reduce((s, stk) => s + stk.currentPrice, 0);
  const totalChange = watchStocks.reduce((s, stk) => s + (stk.currentPrice - stk.previousClose), 0);
  const pct = (totalChange / (totalInvested - totalChange)) * 100;
  const isUp = totalChange >= 0;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView showsVerticalScrollIndicator={false}>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>My Watchlist</Text>
          <TouchableOpacity style={styles.editBtn}>
            <Ionicons name="add" size={20} color={Colors.primary} />
            <Text style={styles.editText}>Add</Text>
          </TouchableOpacity>
        </View>

        {/* Summary card */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <View>
              <Text style={styles.summaryLabel}>Watching {symbols.length} stocks</Text>
              <Text style={styles.summaryValue}>
                ₹{totalInvested.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
              <Text style={styles.summaryLabel}>Combined price</Text>
            </View>
            <View style={[styles.changePill, { backgroundColor: isUp ? Colors.primaryLight : Colors.dangerLight }]}>
              <Text style={[styles.changePillText, { color: isUp ? Colors.primary : Colors.danger }]}>
                {isUp ? '▲' : '▼'} {Math.abs(pct).toFixed(2)}% today
              </Text>
            </View>
          </View>

          {/* Mini sparklines row */}
          <View style={styles.sparkRow}>
            {watchStocks.slice(0, 5).map(s => {
              const c = s.currentPrice - s.previousClose;
              const col = c >= 0 ? Colors.primary : Colors.danger;
              return (
                <View key={s.symbol} style={styles.sparkItem}>
                  <Text style={[styles.sparkSymbol, { color: col }]}>{s.symbol.slice(0, 4)}</Text>
                  <Text style={[styles.sparkPct, { color: col }]}>
                    {c >= 0 ? '+' : ''}{((c / s.previousClose) * 100).toFixed(1)}%
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Stock list */}
        <View style={styles.listCard}>
          {watchStocks.map(s => (
            <StockListItem key={s.symbol} stock={s} />
          ))}
        </View>

        {/* Suggestion strip */}
        <Text style={styles.suggestTitle}>You might also like</Text>
        <View style={styles.listCard}>
          {STOCKS.filter(s => !symbols.includes(s.symbol)).slice(0, 4).map(s => (
            <StockListItem key={s.symbol} stock={s} />
          ))}
        </View>

        <View style={{ height: 24 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingTop: Platform.OS === 'web' ? Spacing.base : Spacing.sm,
    paddingBottom: Spacing.sm,
  },
  title: { fontSize: Typography['2xl'], fontWeight: '800', color: Colors.text },
  editBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.primaryLight, paddingHorizontal: 12, paddingVertical: 6, borderRadius: Radius.full },
  editText: { fontSize: Typography.sm, color: Colors.primary, fontWeight: '600' },

  summaryCard: {
    backgroundColor: Colors.primary,
    marginHorizontal: Spacing.base,
    borderRadius: Radius.xl,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    ...Shadow.md,
  },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  summaryLabel: { fontSize: Typography.xs, color: 'rgba(255,255,255,0.75)', marginTop: 2 },
  summaryValue: { fontSize: Typography['3xl'], fontWeight: '800', color: Colors.textInverse },
  changePill: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: Radius.full },
  changePillText: { fontSize: Typography.sm, fontWeight: '700' },

  sparkRow: {
    flexDirection: 'row',
    marginTop: Spacing.md,
    gap: 0,
  },
  sparkItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    backgroundColor: 'rgba(255,255,255,0.15)',
    marginRight: 6,
    borderRadius: Radius.sm,
  },
  sparkSymbol: { fontSize: 10, fontWeight: '700', color: Colors.textInverse },
  sparkPct: { fontSize: 10, fontWeight: '600', color: Colors.textInverse, marginTop: 2 },

  listCard: {
    backgroundColor: Colors.card,
    marginHorizontal: Spacing.base,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  suggestTitle: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.text,
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.sm,
  },
});
