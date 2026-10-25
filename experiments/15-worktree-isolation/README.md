# 15 Worktree Isolation

> 두 Agent 작업의 파일을 실제 Git worktree로 분리하면서 변경된 작업을 지우지 않을 수 있는가?

- 상태: `validated`
- 참여자: `@ukkhnn`
- 학습 세션 라벨: 2026-10-25. 실제 실행 시각은 결과에 별도로 기록한다.
- 선행: 08 Coding Agent, 13 승인 경계
- 후행: 17 Personal AI 연결

08의 patch 품질을 반복 평가하지 않는다. 이 과제는 실제 임시 Git 저장소와 두 branch/worktree를 만들고 파일 변경·commit·정리 경계를 측정한다. 기존 Hands-on 저장소에는 branch를 만들거나 파일을 수정하지 않는다.

## 범위와 결과

| 검증 | 결과 |
| --- | --- |
| 실제 Git 평가 | 6/6 |
| 경계 테스트 | 12/12 |
| 작업 간 파일 혼합·금지 경로 변경 | 0 |
| 평가 임시 저장소 정리 | 완료 |

한 worktree에서 fixture를 변경하고 commit해도 다른 worktree와 main의 작업 파일은 그대로였다. dirty·untracked·ignored 자료가 있으면 삭제하지 않는다. 이름·상대 경로·symlink·hardlink 경계를 검사하며, 정리는 factory가 만든 임시 자원과 소유권 marker를 확인한 뒤 수행한다.

`source snapshot`은 clean HEAD의 허용 파일 내용·상대 경로·hash·revision만 포함한다. 절대 실행 경로와 세션·인증 상태는 산출물에 넣지 않는다. [구현 README](implementations/ukkhnn/README.md), [평가 결과](implementations/ukkhnn/results/report.md)를 참고한다.

## 적용 판단

작업 파일 분리에는 `trial`. **Git worktree는 OS sandbox가 아니다.** object store와 저장소 설정을 공유한다. 실험은 신뢰하는 fixture 코드만 실행하며 악의적인 프로세스와 TOCTOU 경쟁까지 방어한다고 주장하지 않는다. 실제 Agent 코드 실행에는 별도의 OS 권한·컨테이너 정책이 필요하다. 소유권 marker가 손상되면 정리를 중단한다.

Git 공식 [git-worktree 문서](https://git-scm.com/docs/git-worktree)는 linked worktree의 별도 작업 디렉터리와 공유 저장소, dirty worktree의 제거 제한을 설명한다. 이 실험은 강제 제거를 사용하지 않고 ignored 파일까지 별도로 확인한다. Node 공식 [파일 시스템 문서](https://nodejs.org/docs/latest-v22.x/api/fs.html)의 `mkdtemp`, `lstat`, `realpath`를 이용해 임시 자원과 경로를 확인한다.
