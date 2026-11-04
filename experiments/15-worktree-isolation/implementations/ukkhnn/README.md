# Worktree Isolation — ukkhnn

Node 22와 로컬 Git이 필요하다. npm 설치, 네트워크, API 키는 필요 없다. 검증 환경은 Node v22.19.0, Git 2.51.0이다.

```sh
cd hands-on/experiments/15-worktree-isolation/implementations/ukkhnn
node --test
node src/evaluate.mjs
```

실제 Git init/worktree/commit/remove 명령은 OS 임시 디렉터리 아래 이 실험이 만든 저장소에서만 실행된다. Git 전역 설정, signing, hooks를 사용하지 않으며 인증 정보를 전달하지 않는다. 결과 파일에는 임시 절대 경로를 저장하지 않는다.

## 공개 API

`src/worktrees.mjs`의 `TemporaryWorktreeLab`:

```js
const lab = TemporaryWorktreeLab.create();
lab.create('writer');
lab.create('reviewer');
lab.write('writer', 'fixture.txt', 'isolated change\n');
lab.read('reviewer', 'fixture.txt'); // baseline\n
lab.commit('writer', 'Update synthetic fixture');
const source = lab.exportSource('writer', ['fixture.txt']);
lab.cleanup();
```

- `create(name)` → `{ name, branch, path }`. path는 임시 실행용이며 전달 산출물에 저장하지 않는다.
- `write/read(name, relativePath, text?)`: 상대 경로만 허용. `.git`, traversal, symlink·hardlink를 차단한다.
- `status(name)` → `{ dirty, entries }`. untracked·ignored 파일도 포함한다.
- `commit(name, message)` → HEAD revision. 실험의 합성 변경만 대상이다.
- `exportSource(name, allowedPaths)` → `{ revision, branch, files: [{ path, content, sha256 }] }`. dirty면 거절하고 Git의 clean HEAD에서 허용 파일을 읽는다.
- `remove(name)` / `cleanup()` → `{ removed, reason? }`. dirty 자료가 있으면 보존한다. 전체 cleanup은 main과 모든 worktree를 먼저 확인한다.

임시 자원을 외부의 기존 저장소로 바꾸는 생성자는 제공하지 않는다. `root/source` getter는 관찰용이다. 실패 후 dirty 상태가 남으면 자동 강제 삭제하지 않으며, 보존 여부를 결과에서 확인해야 한다.

## 검증과 제한

12개 테스트, 실제 평가 6/6을 통과했다. 대표 차단은 `dirty_worktree`, `unsafe_relative_path`, `symlink_path`, `hardlink_path`다. [summary.json](results/summary.json)에 실제 실행 시각과 정리 결과가 있다.

테스트가 생성한 dirty fixture는 명시적으로 commit하거나 테스트가 만든 링크만 제거한 뒤 clean 상태에서 정리한다. 사용자 작업이나 기존 저장소를 수정하는 복구 로직은 없다. 경로 검사는 이 API의 신뢰하는 호출에만 적용되며 같은 OS 사용자로 실행되는 임의 프로그램을 가두지 않는다.
