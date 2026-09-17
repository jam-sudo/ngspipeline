# Nextflow 용어집 (T-05) — 자기 말로 한 문단씩

작성 2026-09-16. 예시는 모두 이 저장소(`workflows/ngspipeline.nf`, `modules/local/*`)와 nf-core/scrnaseq에서 가져왔다.

**process.** 한 종류의 일을 정의하는 단위다. 입력 선언(`input:`), 출력 선언(`output:`), 실제 실행할 셸 스크립트(`script:`), 그리고 컨테이너·자원 라벨(`label 'process_low'`, `container`)로 이루어진다. 프로세스는 "정의"이고, 입력 채널에서 항목이 하나 들어올 때마다 "태스크"가 하나 실행된다. `GUIDE_ASSIGN`은 프로세스 하나지만 샘플이 12개면 태스크 12개가 각자 작업 디렉터리에서 돈다. 프로세스는 서로의 존재를 모르고 오직 채널로만 연결된다.

**channel.** 프로세스 사이를 흐르는 비동기 큐다. 항목은 보통 `[meta, 파일들]` 튜플이고, `meta.id`가 어느 샘플의 것인지 붙여 다닌다. `map`, `join`, `mix`, `collect`, `toSortedList` 같은 연산자로 모양을 바꾼다. 우리 파이프라인의 `GEX_QUANT.out.count_dir.join(GUIDE_ASSIGN.out.assignment)`는 같은 `meta`를 가진 두 채널의 항목을 짝지어 `[meta, count_dir, assignment.tsv]`로 만든다. 값 채널(value channel)은 항목이 하나뿐이고 몇 번이든 재사용되는 특수한 경우로, `--guides` 같은 파라미터 파일이 그렇다. 큐 채널의 항목 순서는 보장되지 않으므로 순서가 중요하면 `toSortedList`처럼 명시해야 한다(011의 풀링에서 그렇게 했다).

**workflow.** 프로세스와 서브워크플로를 채널로 엮는 코드 블록이다. `take:`로 입력 채널을 받고 `main:`에서 호출을 나열하고 `emit:`로 결과를 내놓는다. `main.nf`의 이름 없는 워크플로가 진입점이고, 우리 `NGSPIPELINE` 워크플로는 파라미터 값까지 `take:`로 받아 안에서 `params`를 직접 읽지 않게 했다. Nextflow는 워크플로 코드를 위에서 아래로 "실행"하는 것이 아니라 데이터플로 그래프를 만든 뒤 항목이 도착하는 대로 태스크를 띄운다. 그래서 코드 순서와 실행 순서가 다를 수 있다.

**profile.** `nextflow.config`의 `profiles { }` 안에 이름을 붙여 둔 설정 묶음이다. `-profile test,docker`처럼 쉼표로 여러 개를 겹치면 뒤의 것이 앞의 것을 덮어쓴다. `test`는 작은 입력과 자원 상한, `docker`/`singularity`는 컨테이너 엔진, `slurm`은 실행기(executor)와 큐를 정한다. 프로파일은 "무엇을 계산하는가"를 바꾸지 않고 "어디서 어떻게 돌리는가"를 바꾼다는 것이 핵심이고, 그래서 docs/03의 해시 비교가 의미를 가진다. 파라미터는 프로파일이 아니라 `-params-file`이나 CLI로 넘기는 것이 nf-core 규칙이다.

**work dir / -resume.** 태스크마다 입력 파일·스크립트·컨테이너·파라미터를 해시한 값으로 `work/ab/cdef...` 디렉터리를 만들고 그 안에서 실행한다. 출력은 그 디렉터리에 남고 `publishDir`가 결과 폴더로 복사·링크한다. `-resume`를 주면 같은 해시의 태스크는 다시 돌리지 않고 이전 디렉터리의 결과를 그대로 쓴다. 우리 docs/02에서 kb count와 guide count를 SIGTERM으로 죽인 뒤 `-resume`하자 상류 4개는 CACHED, 중단된 것과 그 하류 5개만 다시 돌았다. 입력 파일의 내용이 같아도 경로나 타임스탬프가 바뀌면 해시가 달라질 수 있어(`stageInMode`, 파일 속성), 재현성 논의에서 자주 나오는 함정이다. work dir은 지우기 전까지 디스크를 크게 차지한다(Discovery 전체 실행 16 GB).

**module vs subworkflow.** module은 프로세스 하나를 담은 `main.nf`(+ `environment.yml`, `meta.yml`, 테스트)로, 도구 하나를 감싼 재사용 단위다. nf-core/modules에서 `nf-core modules install kallistobustools/count`로 설치하면 `modules/nf-core/`에 들어오고 손으로 고치지 않는다. subworkflow는 여러 모듈을 채널로 엮어 한 단계를 만든 것으로, 우리 `subworkflows/local/gex_quant`는 KALLISTOBUSTOOLS_REF와 COUNT를 묶고 세포 수를 로그로 남긴다. 규칙 4에서 손으로 쓴 module을 네 개로 제한한 이유는, 도구 래퍼는 커뮤니티 것을 쓰고 우리가 책임질 코드는 조합(subworkflow)과 꼭 필요한 변환(guide 인덱스·카운트·할당·h5ad)으로 좁히기 위해서다.
