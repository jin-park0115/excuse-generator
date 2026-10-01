// 선택 가능한 둥근 칩 버튼. 홈의 상황·말투 선택과 기록 화면 탭에서 쓴다.
import { Pressable, StyleSheet, Text } from 'react-native';

import { useTheme } from '@/constants/theme';

type Props = { label: string; selected: boolean; onPress: () => void; accessibilityLabel?: string };

export default function Chip({ label, selected, onPress, accessibilityLabel }: Props) {
  const c = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, { borderColor: c.border, backgroundColor: c.card }, selected && { backgroundColor: c.primary, borderColor: c.primary }]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ selected }}
    >
      <Text style={[styles.text, { color: selected ? c.onPrimary : c.text }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: { minHeight: 44, paddingHorizontal: 16, justifyContent: 'center', borderRadius: 22, borderWidth: 1 },
  text: { fontSize: 15, fontWeight: '500' },
});
