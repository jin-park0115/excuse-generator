// 신뢰도 게이지(0~100%)와 한 줄 코멘트 (F7). 결과 화면과 기록 화면에서 쓴다.
import { StyleSheet, Text, View } from 'react-native';

function gaugeColor(credibility: number): string {
  if (credibility >= 70) return '#27AE60';
  if (credibility >= 30) return '#F39C12';
  return '#E74C3C';
}

export default function CredibilityGauge({ credibility, comment }: { credibility: number; comment: string }) {
  return (
    <View style={styles.container} accessible accessibilityLabel={`신뢰도 ${credibility}퍼센트. ${comment}`}>
      <Text style={styles.label}>신뢰도 {credibility}%</Text>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${credibility}%`, backgroundColor: gaugeColor(credibility) }]} />
      </View>
      <Text style={styles.comment}>{comment}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 6 },
  label: { fontSize: 14, fontWeight: '600' },
  track: { height: 12, borderRadius: 6, backgroundColor: '#E5E5E5', overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 6 },
  comment: { fontSize: 15, color: '#555' },
});
