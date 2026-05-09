import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  SafeAreaView, Platform, TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { IndexCard } from '@/components/home/IndexCard';
import { SectorCard } from '@/components/home/SectorCard';
import { StockListItem } from '@/components/stock/StockListItem';
import { Colors, Typography, Spacing, Radius } from '@/theme';
import { INDICES, SECTORS, STOCKS, TOP_GAINERS, TOP_LOSERS } from '@/data/stocks';

const TABS = ['Top Gainers', 'Top Losers', 'Most Active'];

export default function MarketsScreen() {
  const [activeTab, setActiveTab] = useState(0);

  const tabStocks = activeTab === 0
    ? TOP_GAINERS
    : activeTab === 1
    ? TOP_LOSERS
    : STOCKS.slice(0, 5);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Good morning 👋</Text>
            <Text style={styles.tagline}>Indian Stock Markets</Text>
          </View>
          <TouchableOpacity style={styles.bellBtn}>
            <Ionicons name="notifications-outline" size={22} color={Colors.text} />
            <View style={styles.notifDot} />
          </TouchableOpacity>
        </View>

        {/* ── Market Status Banner ── */}
        <View style={styles.statusBanner}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>NSE & BSE Markets Open · Live Data</Text>
          <Text style={styles.statusTime}>09:15 – 15:30 IST</Text>
        </View>

        {/* ── Index Strip ── */}
        <Text style={styles.sectionTitle}>Indices</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.hScroll} contentContainerStyle={styles.hContent}>
          {INDICES.map((idx, i) => (
            <IndexCard
              key={i}
              name={idx.name}
              value={idx.value}
              change={idx.change}
              pct={idx.pct}
              up={idx.up}
              sparkData={Array.from({ length: 20 }, (_, j) =>
                24000 + Math.sin(j * 0.4 + i) * 600 + Math.random() * 200
              )}
            />
          ))}
        </ScrollView>

        {/* ── Sectors ── */}
        <View style={styles.sectionRow}>
          <Text style={styles.sectionTitle}>Sectors</Text>
          <TouchableOpacity><Text style={styles.seeAll}>See all</Text></TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.hScroll} contentContainerStyle={styles.hContent}>
          {SECTORS.map((s, i) => (
            <SectorCard key={i} name={s.name} change={s.change} up={s.up} count={s.count} />
          ))}
        </ScrollView>

        {/* ── Movers ── */}
        <View style={styles.moversCard}>
          <View style={styles.tabRow}>
            {TABS.map((t, i) => (
              <TouchableOpacity
                key={t}
                style={[styles.tab, activeTab === i && styles.tabActive]}
                onPress={() => setActiveTab(i)}
              >
                <Text style={[styles.tabText, activeTab === i && styles.tabTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>
          {tabStocks.map((s) => (
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
  scroll: { flex: 1 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingTop: Platform.OS === 'web' ? Spacing.base : Spacing.sm,
    paddingBottom: Spacing.sm,
  },
  greeting: { fontSize: Typography.sm, color: Colors.textSecondary },
  tagline: { fontSize: Typography['2xl'], fontWeight: '800', color: Colors.text },
  bellBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.card, alignItems: 'center', justifyContent: 'center' },
  notifDot: { position: 'absolute', top: 8, right: 8, width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.danger, borderWidth: 1.5, borderColor: Colors.card },

  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primaryLight,
    marginHorizontal: Spacing.base,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: 8,
    marginBottom: Spacing.md,
    gap: 6,
  },
  statusDot: { width: 7, height: 7, borderRadius: 3.5, backgroundColor: Colors.primary },
  statusText: { fontSize: Typography.xs, color: Colors.primaryDark, fontWeight: '600', flex: 1 },
  statusTime: { fontSize: Typography.xs, color: Colors.primary },

  sectionTitle: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text, paddingHorizontal: Spacing.base, marginBottom: Spacing.sm },
  sectionRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingRight: Spacing.base },
  seeAll: { fontSize: Typography.sm, color: Colors.primary, fontWeight: '600' },
  hScroll: { paddingBottom: Spacing.md },
  hContent: { paddingHorizontal: Spacing.base, paddingRight: Spacing.base },

  moversCard: {
    backgroundColor: Colors.card,
    marginHorizontal: Spacing.base,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    marginTop: Spacing.sm,
  },
  tabRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
    paddingHorizontal: Spacing.base,
  },
  tab: { paddingVertical: 12, paddingHorizontal: 4, marginRight: Spacing.md, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabActive: { borderBottomColor: Colors.primary },
  tabText: { fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: '600' },
  tabTextActive: { color: Colors.primary },
});
