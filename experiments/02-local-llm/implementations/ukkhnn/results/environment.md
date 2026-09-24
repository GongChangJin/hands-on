# 실행 환경

- 실행 시각: 2026-09-24 (Asia/Seoul)
- 기기: Mac mini, Apple M4 Pro, 14-core CPU, 64 GB unified memory
- 운영체제: macOS 26.6.2, arm64
- Python: 3.11.15
- Ollama: 0.22.0
- context: 4,096 tokens
- 생성 설정: temperature 0, seed 42, JSON Schema structured output

| model | parameters | quantization | local storage | loaded memory | processor | CPU offload |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| `qwen2.5:3b` | 3.1B | Q4_K_M | 1.9 GB | 2.3 GB | 100% GPU | 0% reported |
| `qwen2.5:latest` | 7.6B | Q4_K_M | 4.7 GB | 4.8 GB | 100% GPU | 0% reported |

저장공간은 `ollama list`, processor와 적재 메모리는 평가 직후 `ollama ps`로 확인했다. Apple Silicon의 GPU 메모리는 unified memory를 사용하므로 표의 loaded memory를 별도 물리 VRAM으로 해석하지 않는다.
