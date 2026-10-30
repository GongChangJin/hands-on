# Worktree 격리 결과

실행 시각: 2026-11-04T14:25:26.098Z

- 실제 임시 Git 저장소 평가: 6/6
- 경계 위반: 0
- 임시 자원 정리: true
- 한 worktree의 변경과 commit은 다른 worktree의 파일에 영향을 주지 않았다.
- dirty 파일과 ignored 파일은 삭제하지 않으며, 출처 snapshot에는 상대 경로와 revision만 내보낸다.
- 적용 판단: 작업 디렉터리 분리에는 trial. Git 설정·object store는 공유하며 OS 보안 격리로 사용하지 않는다.
