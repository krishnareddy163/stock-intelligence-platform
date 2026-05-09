import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  SafeAreaView, Platform, useWindowDimensions,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { LineChart } from '@/components/charts/LineChart';
import { InvestorBreakdown } from '@/components/stock/InvestorBreakdown';
import { KeyMetrics } from '@/components/stock/KeyMetrics';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Colors, Typography, Spacing, Radius } from '@/theme';
import { STOCKS, type PeriodKey } from '@/data/stocks';

const PERIODS: PeriodKey[] = ['1D', '1W', '1M', '3M', '1Y', '5Y'];

export default function StockDetailScreen() {
  const { symbol } = useLocalSearchParams<{ symbol: string }>();
  const router = useRouter();
  const { width } = useWindowDimensions();
  const [period, setPeriod] = useState<PeriodKey>('1Y');
  const [watchlisted, setWatchlisted] = useState(false);

  const stock = STOCKS.find(s => s.symbol === symbol);
  if (!stock) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.notFound}>
          <Text style={styles.notFoundText}>Stock not found</Text>
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={{ color: Colors.primary }}>Go back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const change = stock.currentPrice - stock.previousClose;
  const pct = (change / stock.previousClose) * 100;
  const isUp = change >= 0;
  const color = isUp ? Colors.primary : Colors.danger;
  const chartData = stock.priceHistory[period];
  const chartWidth = Math.min(width - 32, 560);

  const periodHigh = Math.max(...chartData);
  const periodLow = Math.min(...chartData);

  return (
    <SafeAreaView style={styles.safe}>
      {/* ── Header ── */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.topCenter}>
          <Text style={styles.topSymbol}>{stock.symbol}</Text>
          <Text style={styles.topExchange}>{stock.exchange}</Text>
        </View>
        <TouchableOpacity
          style={styles.wlBtn}
          onPress={() => setWatchlisted(w => !w)}
        >
          <Ionicons
            name={watchlisted ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={watchlisted ? Colors.primary : Colors.text}
          />
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>

        {/* ── Price Hero ── */}
        <LinearGradient
          colors={isUp ? ['#e6f7f3', '#f0f2f5'] : ['#fef2f2', '#f0f2f5']}
          style={styles.hero}
        >
          <View style={styles.heroContent}>
            <View style={styles.heroLeft}>
              <View style={styles.stockAvatar}>
                <Text style={styles.avatarText}>{stock.symbol.slice(0, 2)}</Text>
              </View>
              <View>
                <Text style={styles.heroName}>{stock.name}</Text>
                <View style={styles.badgeRow}>
                  <Badge label={stock.sector} variant="neutral" />
                  <Badge label={stock.exchange} variant="primary" style={{ marginLeft: 6 }} />
                </View>
              </View>
            </View>
          </View>

          <View style={styles.priceRow}>
            <Text style={styles.price}>
              ₹{stock.currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
            <View style={[styles.changePill, { backgroundColor: isUp ? Colors.primaryLight : Colors.dangerLight }]}>
              <Text style={[styles.changePillText, { color }]}>
                {isUp ? '▲' : '▼'} ₹{Math.abs(change).toFixed(2)} ({Math.abs(pct).toFixed(2)}%)
              </Text>
            </View>
          </View>

          <View style={styles.ohlcRow}>
            {[
              ['Open',  `₹${stock.open.toLocaleString('en-IN')}`],
              ['High',  `₹${periodHigh.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`],
              ['Low',   `₹${periodLow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`],
              ['Prev.', `₹${stock.previousClose.toLocaleString('en-IN')}`],
            ].map(([l, v]) => (
              <View key={l} style={styles.ohlcItem}>
                <Text style={styles.ohlcLabel}>{l}</Text>
                <Text style={styles.ohlcVal}>{v}</Text>
              </View>
            ))}
          </View>
        </LinearGradient>

        <View style={styles.body}>

          {/* ── Period Selector + Chart ── */}
          <Card style={styles.chartCard} padded={false}>
            <View style={styles.periodRow}>
              {PERIODS.map(p => (
                <TouchableOpacity
                  key={p}
                  style={[styles.periodBtn, period === p && styles.periodBtnActive]}
                  onPress={() => setPeriod(p)}
                >
                  <Text style={[styles.periodText, period === p && styles.periodTextActive]}>{p}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.chartWrap}>
              <LineChart
                data={chartData}
                width={chartWidth}
                height={200}
                color={color}
                showGradient
              />
            </View>

            <View style={styles.chartStats}>
              <View style={styles.chartStat}>
                <Text style={styles.chartStatLabel}>Period High</Text>
                <Text style={[styles.chartStatVal, { color: Colors.primary }]}>
                  ₹{periodHigh.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </Text>
              </View>
              <View style={styles.chartStat}>
                <Text style={styles.chartStatLabel}>Period Low</Text>
                <Text style={[styles.chartStatVal, { color: Colors.danger }]}>
                  ₹{periodLow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </Text>
              </View>
              <View style={styles.chartStat}>
                <Text style={styles.chartStatLabel}>Change</Text>
                <Text style={[styles.chartStatVal, { color: chartData[chartData.length - 1] >= chartData[0] ? Colors.primary : Colors.danger }]}>
                  {(((chartData[chartData.length - 1] - chartData[0]) / chartData[0]) * 100).toFixed(1)}%
                </Text>
              </View>
            </View>
          </Card>

          {/* ── Investor Breakdown ── */}
          <InvestorBreakdown shareholding={stock.shareholding} />

          {/* ── Key Metrics ── */}
          <KeyMetrics stock={stock} />

          {/* ── About ── */}
          <Card style={styles.aboutCard}>
            <Text style={styles.aboutTitle}>About {stock.name}</Text>
            <Text style={styles.aboutText}>{stock.about}</Text>
            <View style={styles.aboutTags}>
              <View style={styles.tag}><Text style={styles.tagText}>{stock.sector}</Text></View>
              <View style={styles.tag}><Text style={styles.tagText}>{stock.exchange}</Text></View>
              <View style={styles.tag}><Text style={styles.tagText}>Large Cap</Text></View>
            </View>
          </Card>

        </View>

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* ── CTA Bar ── */}
      <View style={styles.ctaBar}>
        <TouchableOpacity style={styles.sellBtn}>
          <Text style={styles.sellText}>Sell</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.buyBtn}>
          <Text style={styles.buyText}>Buy</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  notFound: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  notFoundText: { fontSize: Typography.xl, color: Colors.text },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.card,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.bg, alignItems: 'center', justifyContent: 'center' },
  topCenter: { flex: 1, alignItems: 'center' },
  topSymbol: { fontSize: Typography.lg, fontWeight: '800', color: Colors.text },
  topExchange: { fontSize: Typography.xs, color: Colors.textMuted },
  wlBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.bg, alignItems: 'center', justifyContent: 'center' },

  hero: { padding: Spacing.base, paddingBottom: Spacing.lg },
  heroContent: { flexDirection: 'row', alignItems: 'center', marginBottom: Spacing.sm },
  heroLeft: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  stockAvatar: {
    width: 48, height: 48, borderRadius: 14,
    backgroundColor: '#eef2ff',
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { fontSize: Typography.md, fontWeight: '800', color: '#6366f1' },
  heroName: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text },
  badgeRow: { flexDirection: 'row', marginTop: 4 },

  priceRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: Spacing.md },
  price: { fontSize: Typography['4xl'], fontWeight: '800', color: Colors.text },
  changePill: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: Radius.full },
  changePillText: { fontSize: Typography.sm, fontWeight: '700' },

  ohlcRow: { flexDirection: 'row', gap: 0 },
  ohlcItem: { flex: 1 },
  ohlcLabel: { fontSize: Typography.xs, color: Colors.textMuted },
  ohlcVal: { fontSize: Typography.sm, fontWeight: '600', color: Colors.text, marginTop: 2 },

  body: { padding: Spacing.base, gap: Spacing.md },

  chartCard: { marginBottom: 0, overflow: 'hidden' },
  periodRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
  },
  periodBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: Radius.full },
  periodBtnActive: { backgroundColor: Colors.primary },
  periodText: { fontSize: Typography.sm, fontWeight: '600', color: Colors.textSecondary },
  periodTextActive: { color: Colors.textInverse },
  chartWrap: { paddingHorizontal: Spacing.base, paddingVertical: Spacing.md },
  chartStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.divider,
    backgroundColor: '#f8f9fa',
  },
  chartStat: { alignItems: 'center' },
  chartStatLabel: { fontSize: Typography.xs, color: Colors.textMuted },
  chartStatVal: { fontSize: Typography.md, fontWeight: '700', marginTop: 2 },

  aboutCard: { marginBottom: 0 },
  aboutTitle: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text, marginBottom: Spacing.sm },
  aboutText: { fontSize: Typography.base, color: Colors.textSecondary, lineHeight: 22 },
  aboutTags: { flexDirection: 'row', gap: 8, marginTop: Spacing.md },
  tag: { paddingHorizontal: 10, paddingVertical: 4, backgroundColor: Colors.primaryLight, borderRadius: Radius.full },
  tagText: { fontSize: Typography.xs, color: Colors.primaryDark, fontWeight: '600' },

  ctaBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    gap: Spacing.md,
    padding: Spacing.base,
    paddingBottom: Platform.OS === 'ios' ? 32 : Spacing.base,
    backgroundColor: Colors.card,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sellBtn: {
    flex: 1,
    backgroundColor: Colors.dangerLight,
    paddingVertical: 14,
    borderRadius: Radius.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.danger,
  },
  sellText: { fontSize: Typography.lg, fontWeight: '700', color: Colors.danger },
  buyBtn: {
    flex: 1,
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: Radius.lg,
    alignItems: 'center',
  },
  buyText: { fontSize: Typography.lg, fontWeight: '700', color: Colors.textInverse },
});
