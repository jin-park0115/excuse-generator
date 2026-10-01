// 선택 가능한 둥근 칩 버튼. 홈의 상황·말투 선택과 기록 화면 탭에서 쓴다.
import { Pressable, StyleSheet, Text } from 'react-native';

type Props = { label: string; selected: boolean; onPress: () => void; accessibilityLabel?: string };

export default function Chip({ label, selected, onPress, accessibilityLabel }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected && styles.chipOn]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ selected }}
    >
      <Text style={selected && styles.textOn}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: { minHeight: 44, paddingHorizontal: 16, justifyContent: 'center', borderRadius: 22, borderWidth: 1, borderColor: '#ccc' },
  chipOn: { backgroundColor: '#208AEF', borderColor: '#208AEF' },
  textOn: { color: '#fff', fontWeight: '600' },
});
