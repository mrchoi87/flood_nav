# 침수 회피 내비게이션 — 스타터 프로젝트

Flask + Leaflet + OSMnx로 **침수 구역을 피해서 경로를 안내**하는 최소 기능(MVP)을 바로 실행할 수 있는 템플릿입니다.

## 0) 사전 준비
- Python 3.10+ 권장 (Windows, macOS, Linux)
- 터미널/명령 프롬프트

## 1) 설치
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> **처음 실행은 느릴 수 있어요.** OSM 도로 데이터를 캐시로 받아옵니다. 다음 실행부터는 빨라집니다.

## 2) 실행
```bash
python app.py
```
브라우저에서 http://127.0.0.1:5000 열기

## 3) 사용 방법
1. **출발지 지정** 버튼 → 지도 클릭
2. **도착지 지정** 버튼 → 지도 클릭
3. 다각형 도구로 **침수 구역**을 그리기 (복수 개 가능)
4. 버퍼(m)를 원하면 입력 (기본 8m; *대략적인 값*)
5. **경로 계산** 클릭 → 우회 경로가 파란 선으로 표시

> 경로가 없다면 침수 구역을 줄이거나 버퍼를 낮춰보세요.

## 4) 지역 변경 (그래프 범위)
`app.py` 상단의 다음 값을 바꾸면 됩니다.
```py
CENTER_LAT, CENTER_LNG = 37.5665, 126.9780  # 중심(서울시청)
DIST_METERS = 5000                           # 반경(m)
```
더 넓게 하려면 `DIST_METERS`를 키우세요(너무 크면 느릴 수 있음).

## 5) 정확한 버퍼 처리(선택)
현재는 간단히 **미터→위도경도**로 근사 변환합니다. 더 정확히 하려면:
- 그래프를 지역 좌표계(미터)로 **투영**하고,
- 폴리곤도 동일 좌표계로 변환 후 `buffer()`를 사용하세요.

예시(개발 고급 단계):
```python
Gp = ox.project_graph(G)  # G를 지역 투영(미터)로
# 폴리곤을 같은 CRS로 투영한 뒤 buffer(5~10) 적용
```

## 6) Firebase로 다중 사용자 공유(선택)
- `templates/index.html` `<head>`에 Firebase SDK 2줄을 추가하고,
- `static/main.js` 맨 아래의 Firebase 블록을 활성화해
- `firebaseConfig`를 본인 프로젝트 값으로 채우세요.
- Realtime Database 규칙은 개발 단계에서 읽기/쓰기를 허용해 실험하고, 배포 시 제한하세요.

```jsonc
// 개발용 샘플 규칙(비권장; 실서비스 전 반드시 강화)
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

## 7) 흔한 문제
- **도시 범위 밖에서 찍은 출발/도착** → 그래프 범위를 넓히세요.
- **경로 없음** → 침수 다각형이 도로를 완전히 막았을 수 있습니다. 지역 또는 버퍼를 조정.
- **첫 실행 매우 느림** → 캐시 구축 중; 이후 빨라집니다.

## 8) 라이선스
오픈스트리트맵(OpenStreetMap) 데이터는 해당 라이선스(OSM Contributors)를 따릅니다.
```

