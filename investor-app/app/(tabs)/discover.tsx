import React, { useState, useMemo } from 'react';
import {
  View, Text, StyleSheet, TextInput, ScrollView,
  TouchableOpacity, SafeAreaView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { StockListItem } from '@/components/stock/StockListItem';
import { Colors, Typography, Spacing, Radius } from '@/theme';
import { STOCKS } from '@/data/stocks';

const SECTORS = ['All', 'IT', 'Banking', 'Auto', 'Pharma', 'NBFC', 'Consumer', 'Oil & Gas'];
const SORT_OPTIONS = ['Price ↑', 'Price ↓', 'Gain ↑', 'Loss ↑', 'Market Cap'];

export default function DiscoverScreen() {
  const [query, setQuery] = useState('');
  const [sector, setSector] = useState('All');
  const [sort, setSort] = useState('Market Cap');

  const filtered = useMemo(() => {
    let result = STOCKS.filter(s => {
      const q = query.toLowerCase();
      const matchQ = !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q);
      const matchS = sector === 'All' || s.sector === sector;
      return matchQ && matchS;
    });
    if (sort === 'Price ↑') result = [...result].sort((a, b) => a.currentPrice - b.currentPrice);
    if (sort === 'Price ↓') result = [...result].sort((a, b) => b.currentPrice - a.currentPrice);
    if (sort === 'Gain ↑')  result = [...result].sort((a, b) => (b.currentPrice - b.previousClose) - (a.currentPrice - a.previousClose));
    if (sort === 'Loss ↑')  result = [...result].sort((a, b) => (a.currentPrice - a.previousClose) - (b.currentPrice - b.previousClose));
    if (sort === 'Market Cap') result = [...result].sort((a, b) => b.marketCap - a.marketCap);
    return result;
  }, [query, sector, sort]);

  return (
    <SafeAreaView style={styles.safe}>
      {/* Search bar */}
      <View style={styles.searchBar}>
        <Ionicons name="search" size={18} color={Colors.textMuted} style={styles.searchIcon} />
        <TextInput
          style={styles.input}
          placeholder="Search stocks, e.g. TCS, Reliance…"
          placeholderTextColor={Colors.textMuted}
          value={query}
          onChangeText={setQuery}
          autoCorrect={false}
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => setQuery('')}>
            <Ionicons name="close-circle" size={18} color={Colors.textMuted} />
          </TouchableOpacity>
        )}
      </View>

      {/* Sector chips */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll} contentContainerStyle={styles.chipContent}>
        {SECTORS.map(s => (
          <TouchableOpacity
            key={s}
            style={[styles.chip, s === sector && styles.chipActive]}
            onPress={() => setSector(s)}
          >
            <Text style={[styles.chipText, s === sector && styles.chipTextActive]}>{s}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Sort bar */}
      <View style={styles.sortRow}>
        <Text style={styles.resultCount}>{filtered.length} stocks</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {SORT_OPTIONS.map(o => (
            <TouchableOpacity
              key={o}
              style={[styles.sortChip, o === sort && styles.sortActive]}
              onPress={() => setSort(o)}
            >
              <Text style={[styles.sortText, o === sort && styles.sortTextActive]}>{o}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Stock list */}
      <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
        <View style={styles.listCard}>
          {filtered.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>🔍</Text>
              <Text style={styles.emptyText}>No stocks found</Text>
              <Text style={styles.emptySub}>Try a different search or filter</Text>
            </View>
          ) : (
            filtered.map((s, i) => (
              <StockListItem key={s.symbol} stock={s} rank={i + 1} />
            ))
          )}
        </View>
        <View style={{ height: 24 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.card,
    margin: Spacing.base,
    borderRadius: Radius.lg,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'web' ? 10 : 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  searchIcon: { marginRight: 8 },
  input: {
    flex: 1,
    fontSize: Typography.md,
    color: Colors.text,
    outlineStyle: 'none',
  } as any,
  chipScroll: { maxHeight: 44 },
  chipContent: { paddingHorizontal: Spacing.base, gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: Radius.full,
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  chipText: { fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: Colors.card },

  sortRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    gap: 8,
  },
  resultCount: { fontSize: Typography.sm, color: Colors.textMuted, marginRight: 4 },
  sortChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: Radius.sm,
    backgroundColor: Colors.card,
    marginRight: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sortActive: { backgroundColor: Colors.primaryLight, borderColor: Colors.primary },
  sortText: { fontSize: Typography.xs, color: Colors.textSecondary, fontWeight: '600' },
  sortTextActive: { color: Colors.primaryDark },

  list: { flex: 1 },
  listCard: {
    backgroundColor: Colors.card,
    marginHorizontal: Spacing.base,
    borderRadius: Radius.lg,
    overflow: 'hidden',
  },
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  emptyText: { fontSize: Typography.lg, fontWeight: '700', color: Colors.text },
  emptySub: { fontSize: Typography.sm, color: Colors.textMuted, marginTop: 4 },
});
