# Hello Nextflow 훈련 — 모듈별 대응표 (T-05)

Nextflow 공식 훈련 "Hello Nextflow"의 모듈을 이 저장소의 실제 코드에 대응시킨 표. 훈련 자체의 수행(브라우저 실습)은 사람의 몫이며, 이 표는 각 모듈에서 배우는 것이 이 파이프라인 어디에 쓰였는지 찾아가는 안내다. 작성 2026-09-16 (에이전트, 위임).

| 훈련 모듈        | 배우는 것                                                     | 이 저장소에서 보는 곳                                                               |
| ---------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Hello World      | process, script, output, `nextflow run`                       | `modules/local/guide_index/main.nf` (가장 단순한 프로세스)                          |
| Hello Channels   | `Channel.of/fromPath`, `map`, `view`, 큐 vs 값 채널           | `subworkflows/local/utils_nfcore_ngspipeline_pipeline/main.nf` (samplesheet → 채널) |
| Hello Workflow   | 여러 프로세스 연결, `emit`, `join`                            | `workflows/ngspipeline.nf` 84–101행 (assign → h5ad, 풀링)                           |
| Hello Modules    | `include { } from`, 모듈 분리                                 | `workflows/ngspipeline.nf` 상단 include, `modules/nf-core/`                         |
| Hello Containers | `container`, `-profile docker/singularity`                    | `modules/local/*/main.nf`의 container 삼항식, docs/03 엔진 간 해시                  |
| Hello Config     | `nextflow.config`, profiles, `-params-file`, `resourceLimits` | `conf/test.config`, `conf/slurm.config`, README의 `--min_ratio` 주의                |
| (nf-test)        | 프로세스·파이프라인 테스트, 스냅샷                            | `modules/local/*/tests/main.nf.test`, `tests/default.nf.test`                       |
