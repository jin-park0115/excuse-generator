// 홈 화면. M1에서는 빈 화면만 보여주고, M2에서 상황·레벨·말투 선택 UI를 채운다.
import { StyleSheet, Text, View } from 'react-native';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text>핑계 생성기</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
