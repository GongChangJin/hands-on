# 공통 자료

`@ukkhnn`과 `@us788`이 독립 구현 전에 함께 고정해 사용하는 합성 평가 자료다. 실제 사용자·회사 화면, 개인정보, 인증 정보와 비밀값은 포함하지 않는다.

## 고정 데이터

- `fixtures/`: 1280×720 RGB PNG 합성 UI 24장(결함 20장, 정상 4장)
- `labels/`: taxonomy 1.0.0과 이미지별 정답 라벨, SHA-256, 화면 근거, 허용 가능한 불확실성
- `context/`: 사용자 설명, 축약 DOM, 축약 accessibility snapshot
- `evals/tasks.jsonl`: 각 이미지의 `image-only`와 `image-with-context` 조건을 짝지은 TaskRequest 48개
- `manifest.json`: 생성기 버전, 개수와 이미지 무결성 목록

오류 taxonomy는 `layout_break`, `element_clipping`, `invalid_state`, `error_message`, `accessibility_issue`이고 정상 화면은 빈 오류 목록과 `none` 심각도로 표현한다. 근거는 화면 영역을 설명하며 보이지 않는 pixel-level 좌표는 정답에도 두지 않는다.

## 재현

저장소에 포함된 생성기는 고정된 명세만으로 자료를 다시 만든다.

```bash
python experiments/04-multimodal-agent/shared/generate_fixtures.py
```

생성 후 구현별 `validate-fixtures`가 PNG signature/MIME, 크기, metadata, 개인정보·비밀 패턴, SHA-256, label과 task 연결을 검증해야 한다. 이미지 hash가 라벨과 다르면 모델로 전송하면 안 된다.

## 독립 협업 경계

두 구현자는 이 디렉터리의 이미지, label, context, task와 저장소 공통 schema만 공유한다. 구현 코드, prompt, 전처리 방식과 중간 Phoenix trace는 공유하지 않는다. 독립 구현이 끝난 뒤 조건별 성공률·분류 정확도, schema 준수율, 근거 정확도, p50/p95, token·비용, 개인정보·안전 위반, 대표 실패와 적용 결론만 공유한다.
