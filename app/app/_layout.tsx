// 앱 전체 내비게이션 레이아웃. expo-router가 app/ 폴더의 파일을 화면으로 등록한다.
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: '핑계 생성기' }} />
      <Stack.Screen name="result" options={{ title: '결과' }} />
      <Stack.Screen name="history" options={{ title: '기록' }} />
    </Stack>
  );
}
