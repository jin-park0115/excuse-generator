// 신뢰도 게이지(0~100%)와 한 줄 코멘트 (F7). 결과 화면과 기록 화면에서 쓴다.
import { StyleSheet, Text, View } from 'react-native';

import { useTheme, type Theme } from '@/constants/theme';

function gaugeColor(credibility: number, c: Theme): string {
  if (credibility >= 70) return c.good;
  if (credibility >= 30) return c.warn;
  return c.bad;
}

export default function CredibilityGauge({ credibility, comment }: { credibility: number; comment: string }) {
  const c = useTheme();
  return (
    <View style={styles.container} accessible accessibilityLabel={`신뢰도 ${credibility}퍼센트. ${comment}`}>
      <View style={styles.labelRow}>
        <Text style={[styles.label, { color: c.subtext }]}>신뢰도</Text>
        <Text style={[styles.value, { color: c.text }]}>{credibility}%</Text>
      </View>
      <View style={[styles.track, { backgroundColor: c.track }]}>
        <View style={[styles.fill, { width: `${credibility}%`, backgroundColor: gaugeColor(credibility, c) }]} />
      </View>
      <Text style={[styles.comment, { color: c.subtext }]}>{comment}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8 },
  labelRow: { flexDirection: 'row', justifyContent: 'space-between' },
  label: { fontSize: 13, fontWeight: '500' },
  value: { fontSize: 13, fontWeight: '700' },
  track: { height: 8, borderRadius: 4, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 4 },
  comment: { fontSize: 14, lineHeight: 20 },
});
