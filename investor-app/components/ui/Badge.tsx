import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { Colors, Radius, Typography } from '@/theme';

type Variant = 'gain' | 'loss' | 'neutral' | 'primary' | 'warning';

interface BadgeProps {
  label: string;
  variant?: Variant;
  style?: ViewStyle;
}

const CONFIG: Record<Variant, { bg: string; color: string }> = {
  gain:    { bg: Colors.primaryLight, color: Colors.primary },
  loss:    { bg: Colors.dangerLight,  color: Colors.danger },
  neutral: { bg: '#f1f5f9',           color: Colors.textSecondary },
  primary: { bg: Colors.primaryLight, color: Colors.primaryDark },
  warning: { bg: Colors.warningLight, color: Colors.warning },
};

export function Badge({ label, variant = 'neutral', style }: BadgeProps) {
  const cfg = CONFIG[variant];
  return (
    <View style={[styles.badge, { backgroundColor: cfg.bg }, style]}>
      <Text style={[styles.label, { color: cfg.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: Radius.full,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: 'flex-start',
  },
  label: {
    fontSize: Typography.xs,
    fontWeight: '600',
  },
});
