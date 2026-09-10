# GongChangJin Hands-on

새로운 AI 기술을 직접 구현하고, 프로젝트에 적용할 수 있는지 공통 기준으로 검증하는 공간입니다.

각 핸즈온은 하나의 명확한 질문에서 시작하며 사용법 재현보다 실행 결과, 실패 사례, 제약과 적용 판단을 남기는 것을 목표로 합니다. 전체 전후관계는 [프로젝트 맵](PROJECT_MAP.md)을 참고합니다.

## 상태

```text
planned → active → validated
              └──→ stopped
```

| 상태 | 의미 |
| --- | --- |
| `planned` | 프로젝트 정의와 검증 범위를 확정함 |
| `active` | 구현과 평가를 진행 중임 |
| `validated` | 결과와 프로젝트 적용 판단을 기록함 |
| `stopped` | 중단 이유와 현재까지의 결과를 기록함 |

## 디렉터리 구조

```text
hands-on/
├── README.md
├── PROJECT_MAP.md
├── common/                         # 프로젝트 공통 계약·어댑터·평가 기반
├── experiments/                    # 주제별 핸즈온 프로젝트
│   ├── README.template.md
│   ├── IMPLEMENTATION.template.md
│   └── <순번>-<topic>/
│       ├── README.md               # 과제명세·공통 결과·최종 판단
│       ├── shared/                 # 해당 프로젝트의 공통 데이터·평가 자산
│       └── implementations/        # 구현 방식이 다를 때만 개인별 분리
└── integration/                    # 검증된 프로젝트의 통합
```

## 프로젝트 추가 방법

1. `experiments/README.template.md`를 `experiments/<순번>-<topic>/README.md`로 복사합니다.
2. 프로젝트의 정의, 입력, 산출물, 선행·후행 프로젝트와 완료 조건을 작성합니다.
3. 공통 데이터와 평가 자산은 해당 프로젝트의 `shared/`에 둡니다.
4. 구현 방식이 다를 때만 `implementations/<github-id>/`를 만들고 개인 구현 템플릿을 복사합니다.
5. 프로젝트가 독립 실행·배포·제출 단위로 커지면 별도 프로젝트 저장소로 승격합니다.
6. 핸즈온 내부에 중첩 Git 저장소를 만들지 않습니다.

## 공통 영역과 프로젝트 영역

- 두 프로젝트 이상에서 사용하는 계약·어댑터·평가 코드는 `common/`에서 관리합니다.
- 한 프로젝트에서만 사용하는 문서·이미지·fixture·평가 데이터는 해당 프로젝트의 `shared/`에서 관리합니다.
- 검증된 구현을 연결하는 코드는 `integration/`에서 관리합니다.
- 공통 계약을 변경하면 영향받는 프로젝트를 함께 확인합니다.

## 함께 구현하는 방법

프로젝트는 참여자보다 주제와 검증 질문을 기준으로 관리합니다.

```text
experiments/03-agentic-rag/
├── README.md
├── shared/
│   └── README.md
└── implementations/
    ├── README.md
    ├── github-id-a/
    └── github-id-b/
```

- 하나의 구현을 공동 개발한다면 주제 디렉터리에 `src/`와 `tests/`를 둡니다.
- 서로 다른 접근을 비교한다면 `implementations/<github-id>/`로 분리합니다.
- 공통 질문, 평가 기준, 구현 비교와 결론은 주제 `README.md`에 기록합니다.
- 개인 구현의 실행법과 결과는 개인 `README.md`에 기록합니다.
- 공용 README는 정리 담당자 한 명이 갱신하여 충돌을 줄입니다.

## 프로젝트 목록

| 순서 | 프로젝트 | 상태 | 직접 후행 프로젝트 | 결론 |
| ---: | --- | --- | --- | --- |
| 01 | [Agent Evaluation](experiments/01-agent-evaluation/) | `planned` | 전체 프로젝트 | 진행 전 |
| 02 | [Local/Open-weight LLM](experiments/02-local-llm/) | `planned` | LLM Router | 진행 전 |
| 03 | [Agentic RAG](experiments/03-agentic-rag/) | `planned` | LLM Router, Integration | 진행 전 |
| 04 | [Multimodal Agent](experiments/04-multimodal-agent/) | `planned` | Computer-use, LLM Router | 진행 전 |
| 05 | [AI Research Agent](experiments/05-research-agent/) | `planned` | LLM Router, Integration | 진행 전 |
| 06 | [LLM Router](experiments/06-llm-router/) | `planned` | Computer-use, Coding, Integration | 진행 전 |
| 07 | [Computer-use Agent](experiments/07-computer-use-agent/) | `planned` | Integration | 진행 전 |
| 08 | [Coding Agent](experiments/08-coding-agent/) | `planned` | Cybersecurity Agent | 진행 전 |
| 09 | [Cybersecurity Agent](experiments/09-cybersecurity-agent/) | `planned` | Integration | 진행 전 |

## 완료와 적용 판단

프로젝트는 실행 가능한 구현, 공통 평가 결과, 대표 실패 사례와 적용 범위가 모두 기록되었을 때 `validated`로 변경합니다.

| 판단 | 의미 |
| --- | --- |
| `adopt` | 실제 프로젝트의 기본 기술로 사용 |
| `trial` | 제한된 범위에서 시범 적용 |
| `hold` | 조건이나 기술 성숙도를 추가 확인 |
| `reject` | 현재 요구와 품질·비용·안전 기준에 부적합 |

독립 프로젝트 생성 방법은 [프로젝트 생성 가이드](https://github.com/GongChangJin/projects/blob/main/docs/creating-a-project.md)를 참고합니다.
