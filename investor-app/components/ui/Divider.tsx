import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Colors } from '@/theme';

export function Divider() {
  return <View style={styles.divider} />;
}

const styles = StyleSheet.create({
  divider: {
    height: 1,
    backgroundColor: Colors.divider,
    marginVertical: 12,
  },
});
