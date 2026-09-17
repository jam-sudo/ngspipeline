# PLAN.md — NGSpipeline

**버전** v3.1 · **작성** 2026-09-15 · **작업 디렉토리** `~/NGSpipeline` (MacBook) · **원격** `github.com/jam-sudo/<repo>` (public; 이름은 T-00에서 결정)

**문서 역할 구분** — 이 문서는 정적 명세다. 진행 상태는 `docs/progress.md`, 에이전트 행동 규칙은 `CLAUDE.md`, 개별 결정은 `docs/decisions/`에만 쓴다. 이 문서는 태스크 정의가 바뀔 때만 수정한다.

**목적**: ALIVE의 입력(count matrix + guide 메타데이터)을 FASTQ부터 직접 생산하는 프로덕션급 Nextflow 파이프라인. 2027년 봄 co-op 지원 전에 이력서 문구(§8)를 사실로 만든다.

**개발 방식**: Claude Code 주도 구현. 사람은 결정·검증·설명 책임. 모든 태스크에 **Definition of Done(DoD)** 이 있고, DoD 명령을 사람이 직접 실행해 결과를 `docs/progress.md`에 기록해야 완료다. DoD가 없는 작업은 존재하지 않는 작업이다.

---

## 0. 운영 원칙

### 0.1 역할

| 사람                                               | 에이전트                                        |
| -------------------------------------------------- | ----------------------------------------------- |
| 결정(데이터셋, 정량기, 할당 알고리즘, 개발 호스트) | 구현, 테스트, 리팩터, 문서 초안, 결정 기록 초안 |
| DoD 명령 실행·판정, `docs/progress.md` 기록        | DoD 명령 실행 결과 보고(판정 안 함)             |
| 외부 사실 확인(접근번호, 크기, 버전, 화학)         | `NEEDS_HUMAN:`로 질문 후 정지                   |
| 설명 체크 답변, 학습 부채 해소                     | 설명 체크 문항 생성                             |
| Phase 4 유료 실행                                  | Phase 4 구성만                                  |

### 0.2 태스크 규칙

- 태스크 ID `T-##`. 한 태스크 = 한 세션 = 한 브랜치 = 한 PR.
- 각 태스크는 **목표 / 선행 / 산출물 / DoD / 설명 체크** 다섯 항목을 갖는다.
- DoD는 실행 가능한 명령과 기대 결과로만 쓴다. "잘 동작한다"류 문장은 DoD가 아니다.
- 에이전트 한 세션에 안 끝나면 태스크 분할이 잘못된 것. 쪼개서 ID에 접미어(T-12a, T-12b).
- 선행 태스크가 `docs/progress.md`에 done으로 없으면 착수 금지.

### 0.3 설명 체크 (면접 대비)

태스크 종료 시 에이전트가 PR 본문에 질문 3개를 쓴다. 사람이 코드를 보지 않고 답한다. 하나라도 못 답하면 `docs/learning_debt.md`에 기록. **학습 부채가 남아 있으면 다음 Phase 착수 금지.** 이력서에 올라간 파이프라인을 면접에서 설명 못 하는 상황을 막는 유일한 장치다.

### 0.4 세션 프로토콜

시작: (1) 사람이 `CLAUDE.md > Current state` 갱신 (2) 프롬프트 `T-## 진행. PLAN.md §해당 태스크 참조. DoD 명령 실행 후 출력과 설명 체크 3문항을 PR 본문에.`
종료: (1) 사람이 DoD 직접 실행 (2) 설명 체크 답변 (3) `NEEDS_HUMAN:` 처리 (4) 머지, `Current state`·`docs/progress.md` 갱신.

---

## 1. 최종 완성 조건 (프로젝트 DoD)

아래 전부가 `docs/progress.md`에 증빙(명령 출력 또는 링크)과 함께 기록되면 프로젝트 완료.

| #   | 조건                                                                                                                   | 증빙                               |
| --- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| F1  | `nf-core pipelines lint` 오류 0                                                                                        | 출력 첨부                          |
| F2  | `nextflow run . -profile test,docker` 5분 내 성공                                                                      | `pipeline_info/execution_timeline` |
| F3  | `nextflow run . -profile test,singularity` 성공                                                                        | 동일                               |
| F4  | `nf-test test tests/` 전체 통과                                                                                        | 출력                               |
| F5  | GitHub Actions 최근 10커밋 CI 녹색                                                                                     | Actions 링크                       |
| F6  | `-resume` 검증 문서 `docs/02_resume_check.md` 존재, 재실행 프로세스가 중단 지점 이후만                                 | 문서                               |
| F7  | 선정 데이터 1샘플 전체 실행이 local·slurm(가능 시)·awsbatch(010으로 면제) 프로파일에서 완주, 최종 h5ad의 `sha256` 동일 | `docs/03_cross_profile_hashes.md`  |
| F8  | guide 할당 검증 문서 `docs/01_guide_assignment_validation.md`: 원논문 할당 대비 일치율, 불일치 분류                    | 문서                               |
| F9  | 최종 h5ad를 ALIVE 로더가 수정 없이 읽고 baseline 1회 실행                                                              | ALIVE 저장소 커밋 링크             |
| F10 | MultiQC 리포트에 guide 할당 통계 섹션 포함                                                                             | HTML                               |
| F11 | README: Mermaid 다이어그램, 실행법, 출력 스키마, 실행 통계(시간·비용), 결정 기록 링크                                  | README                             |
| F12 | `docs/learning_debt.md` 비어 있음                                                                                      | 파일                               |
| F13 | `docs/decisions/` 001~00N 모두 `Status: accepted`                                                                      | 디렉토리                           |

F3, F7의 slurm은 Discovery 계정 미확보 시 면제(면제 사유를 progress에 기록). F7의 awsbatch는 2026-09-16 사람의 결정으로 면제(docs/decisions/010-aws-waiver.md). 나머지는 면제 없음.

---

## 2. 입출력 규격

### 입력

- `samplesheet.csv`: `sample_id,gex_r1,gex_r2,guide_r1,guide_r2,expected_cells`
- `guide_library.csv`: `guide_id,target_gene,protospacer`
- `--reference_index` (사전 빌드) 또는 `--fasta` + `--gtf` (파이프라인 내 빌드)
- `--chemistry` (10x 버전, whitelist 결정) — **사람이 데이터셋 확인 후 지정**

### 출력 (`--outdir`)

```
counts/<sample>/                정량기 네이티브 출력(mtx/h5 등, 세포×유전자 raw UMI) — 변환 없음
guides/<sample>/guide_counts.h5ad   세포×guide
guides/<sample>/assignment.tsv  cell_barcode, guide_id, target_gene, method, top1_umi, top2_umi, ratio, posterior, status{single,multi,unassigned}
alive/<sample>.h5ad             counts + assignment 병합. obs: cell_barcode, guide_id, target_gene, assignment_confidence, assignment_method
multiqc/multiqc_report.html
pipeline_info/{execution_report,execution_timeline,execution_trace,pipeline_dag}
```

h5ad 생성은 `to_alive_h5ad`(T-14) 한 곳에서만 한다. 정량기 출력을 별도로 변환하는 프로세스는 두지 않는다(CLAUDE.md 규칙 4).

---

## 3. Phase 0 — 결정 (사람 주도, 1주차)

### T-00 저장소 초기화

- **목표**: nf-core 템플릿 기반 저장소를 `~/NGSpipeline`에 세우고 CI 스켈레톤을 올린다. 저장소/파이프라인 이름(`NGSpipeline` vs `alive-upstream` 등)은 사람이 결정 → `docs/decisions/004-naming.md`. 이후 문서에서 이름을 통일한다.
- **선행**: 없음
- **산출물**: 템플릿 구조, `CLAUDE.md`, `PLAN.md`, `docs/{progress.md,learning_debt.md,decisions/000-template.md}`, `.github/workflows/ci.yml`(lint만), GitHub 원격
- **DoD**:
  - `nf-core pipelines lint` 실행되고 오류 목록이 출력됨(0일 필요 없음, 실행 자체)
  - `git remote -v`에 결정된 원격 이름
  - GitHub Actions에 lint 잡 1회 실행 기록
- **설명 체크**: nf-core 템플릿의 `main.nf`와 `workflows/*.nf`의 역할 분리 이유

### T-01 데이터셋 결정 ⚠ 미검증 항목

- **목표**: 파이프라인을 완주할 실제 Perturb-seq raw 데이터 1샘플 선정.
- **선행**: T-00
- **후보** (에이전트가 표로 정리, 사람이 확인):
  1. Replogle 2022 raw — Figshare+ SRA/GEO 매니페스트에서 단일 샘플(레인) 크기, GEX/guide FASTQ 분리 여부
  2. Adamson 2016 / Dixit 2016 (GEO) — 소규모, guide 캡처 방식 확인 필요
  3. 10x Genomics 공개 CRISPR feature-barcode 데모 — 최소 규모, 표준 형식
- **선정 기준(전부 충족)**: 총 FASTQ ≤ 50 GB · 10x 3' 또는 5' 표준 화학 · guide 라이브러리 별도 FASTQ · 원논문/제공처에 세포별 guide 할당 결과 존재 · 라이선스상 재배포 가능한 subsample
- **산출물**: `docs/decisions/001-dataset.md` (접근번호, 파일 목록·크기, 화학, whitelist, 기각 사유)
- **DoD**:
  - 001 문서 `Status: accepted`
  - 선정 FASTQ 전량 로컬 다운로드, `md5sum -c` 통과(제공처 체크섬 있을 때) 또는 파일 크기가 매니페스트와 일치
  - 원논문 guide 할당 파일 다운로드, 행 수 기록
- **설명 체크**: 왜 이 데이터인가, guide 캡처 라이브러리가 GEX와 분리된 이유

### T-02 개발 호스트·정량기 결정 ⚠ 미검증 항목

- **목표**: 어디서 돌리고 무엇으로 정량할지 실측으로 정한다.
- **선행**: T-00
- **확인 항목** (에이전트 실행, 사람 판정):
  - MacBook: 칩(Apple Silicon 여부), RAM, 디스크 여유. Docker Desktop 설치 여부. Apple Silicon이면 nf-core 컨테이너 중 amd64 전용 이미지의 에뮬레이션 실행 가능 여부·속도.
  - WSL2(48 GB): Tailscale SSH 경유 접속 가능 여부. STAR 인간 유전체 인덱스 빌드(약 32 GB RAM 필요, 경계선) 실측.
  - kallisto|bustools 인덱스 빌드 메모리 실측(양쪽).
- **결정 규칙**: STAR 인덱스가 어느 호스트에서도 안 되면 kallisto|bustools 기본. Apple Silicon에서 amd64 에뮬레이션이 test 프로파일 5분 제한을 못 지키면 개발 호스트는 WSL2, MacBook은 편집·커밋만.
- **산출물**: `docs/decisions/002-quantifier.md`, `docs/decisions/003-dev-host.md`
- **DoD**:
  - 두 문서 `Status: accepted`
  - 선택 호스트에서 `nextflow -version`, `docker run hello-world`(또는 singularity), `nf-core --version`, `nf-test version` 출력 첨부
  - 선택 정량기 인덱스 빌드 완료, 인덱스 경로·크기·빌드 시간 기록
- **설명 체크**: pseudoalignment(kallisto)와 alignment(STAR)의 차이, 이 데이터에서 선택 근거

### T-03 계정

- **목표**: Phase 4 실행 준비.
- **선행**: 없음 (병렬)
- **DoD**:
  - NEU Discovery 클러스터 계정 신청 제출(승인 여부는 별도 기록; 미승인 시 F3/F7 slurm 면제)
  - ~~AWS 계정 생성, Billing 예산 알람 $50 / $100 설정 스크린샷 `docs/aws_budget.png`~~ (010으로 면제)
  - ~~IAM 사용자(관리자 아님) 생성, 액세스 키는 로컬 `~/.aws/credentials`만, repo에 없음~~ (010으로 면제; `git grep -i aws_secret` 결과 0은 유지)

---

## 4. Phase 1 — 학습 (사람, 1~2주차, Phase 0과 병행)

에이전트가 코드를 쓰더라도 건너뛸 수 없다. 설명 체크를 통과할 기반.

### T-05 Nextflow 기초

- **DoD**:
  - Nextflow 공식 training "Hello Nextflow" 전 모듈 완료
  - `nf-core/scrnaseq`를 `-profile test,docker`로 1회 완주, `pipeline_info/pipeline_dag.html` 확인
  - `workflows/scrnaseq.nf`를 읽고 **손으로** 채널 흐름도 작성 → `docs/learning/scrnaseq_dag.md` (사진 또는 Mermaid)
  - 아래 6개 용어를 자기 말로 한 문단씩 `docs/learning/glossary.md`에: process, channel, workflow, profile, work dir/-resume, module vs subworkflow
- **선행**: 없음
- **면제**: 없음

---

## 5. Phase 2 — 핵심 파이프라인 (에이전트, 3~6주차)

### T-10 테스트 데이터 제작

- **목표**: `-profile test`용 소형 데이터.
- **선행**: T-01, T-02
- **방법**: 선정 FASTQ에서 세포 바코드 기준 subsample(바코드 N개 선택 후 해당 리드만 추출) — 리드 무작위 추출이 아님. 참조는 단일 염색체(또는 유전자 수백 개 서브셋) FASTA/GTF.
- **산출물**: `assets/test_data/{gex_R1,gex_R2,guide_R1,guide_R2}.fastq.gz`, `assets/test_data/ref/{chr.fa,chr.gtf}`, `assets/guide_library_test.csv`, `assets/samplesheet_test.csv`, `conf/test.config`, `assets/test_data/README.md`(출처·추출 방법·명령)
- **DoD**:
  - `du -sh assets/test_data` ≤ 20 MB
  - 추출 스크립트 `bin/make_test_data.sh`가 원본 FASTQ 경로를 인자로 받아 동일 파일 재생성(`sha256sum` 일치)
  - 라이선스 확인 문구가 README에 있음
- **설명 체크**: 바코드 기준으로 자르는 이유, 리드 무작위 subsample 시 생기는 문제

### T-11 GEX 정량 서브워크플로

- **목표**: FastQC → 정량기 → 세포×유전자 행렬(정량기 네이티브 형식).
- **선행**: T-10
- **구성**: `modules/nf-core/fastqc`, `modules/nf-core/kallistobustools/{ref,count}`(또는 `star/genomegenerate`, `star/align` STARsolo 모드 — 002 결정에 따름), 빈 방울 필터(정량기 내장 또는 nf-core 모듈). 출력은 정량기 네이티브 형식 그대로 `counts/<sample>/`에 publish. h5ad 변환은 T-14에서만.
- **산출물**: `subworkflows/local/gex_quant/main.nf`, `workflows/alive_upstream.nf`에 연결
- **DoD**:
  - `nextflow run . -profile test,docker` 성공, `results/counts/` 아래 정량기 출력 존재
  - 로그에 세포 수·유전자 수 출력, 세포 수 ≥ test 데이터 바코드 수의 80%
  - `nf-core modules list local`에 사용 모듈 표시(손 편집 없음: `nf-core modules lint` 통과)
- **설명 체크**: 정량기가 whitelist를 쓰는 방식, UMI 중복 제거 시점, 빈 방울 필터 기준

### T-12 guide_index + guide_count (local 모듈)

- **목표**: `guide_library.csv` → feature index → 세포×guide 행렬.
- **선행**: T-10 (T-11과 병렬 가능)
- **방법**: kallisto|bustools kite 워크플로(protospacer → mismatch 허용 k-mer index). 단순 서열 매칭(Python, 해밍 거리)이 더 간단하고 충분하면 그쪽 — 비교 결과를 `docs/decisions/005-guide-count-method.md`에.
- **산출물**: `modules/local/guide_index/main.nf`, `modules/local/guide_count/main.nf`, `subworkflows/local/guide_quant/main.nf`, 005 결정 기록
- **DoD**:
  - test 프로파일에서 `results/guides/<sample>/guide_counts.h5ad` 생성
  - 행렬 열 수 == `guide_library_test.csv` 행 수
  - 행렬 행(바코드) 집합 ⊆ GEX 행렬 바코드 집합 ∪ 미필터 바코드 (교집합 비율 로그 출력)
  - `nf-test` 단위 테스트: 합성 guide FASTQ(리드 20개, guide 2종) → 기대 count 정확 일치
- **설명 체크**: kite가 mismatch를 다루는 방식, protospacer 길이와 k 선택의 관계

### T-13 guide_assign (local 모듈)

- **목표**: 세포별 guide UMI 분포 → 할당.
- **선행**: T-12
- **방법**: 두 가지 구현, `--assign_method {threshold,mixture}`:
  - (a) threshold: top1 UMI ≥ `--min_umi`(기본값은 **사람 지정**), top1/top2 ≥ `--min_ratio`
  - (b) 혼합모델: 원논문 methods 확인 후 결정(예: guide별 Poisson–Gaussian 혼합) — 알고리즘은 `NEEDS_HUMAN:`로 확인받은 뒤 구현
- **산출물**: `bin/guide_assign.py`, `modules/local/guide_assign/main.nf`, `assignment.tsv` 규격(§2), `tests/guide_assign.nf.test`
- **DoD**:
  - nf-test: 합성 입력 5종(명확한 single, 명확한 multi, 경계 ratio, 0 UMI, top1==top2) 각각 기대 status 정확 일치, 두 method 모두
  - `assignment.tsv`에 모든 근거 컬럼 존재(`head -1`로 확인)
  - test 프로파일 완주
- **설명 체크**: (a)와 (b)가 갈리는 세포의 특징, multi 판정 세포를 ALIVE에서 어떻게 다룰지

### T-14 to_alive_h5ad

- **목표**: ALIVE 로더 규격 h5ad.
- **선행**: T-11, T-13
- **산출물**: `bin/to_alive_h5ad.py`, `modules/local/to_alive_h5ad/main.nf`, `docs/alive_schema.md`(obs 컬럼 정의, ALIVE 로더 코드 링크)
- **DoD**:
  - test 프로파일에서 `results/alive/<sample>.h5ad` 생성
  - ALIVE 저장소에서 로더로 읽기 성공(사람 실행, 명령과 출력 첨부) — 로더 수정 0줄
  - `obs` 컬럼 == `docs/alive_schema.md` 정의와 정확 일치(스크립트 검사)
  - `status != single` 세포의 처리(제외 또는 플래그)가 결정 기록 006에 명시
- **설명 체크**: obs 컬럼 각각의 의미와 ALIVE에서 소비하는 지점

### T-15 MultiQC

- **목표**: 한 리포트.
- **선행**: T-11, T-13 (병렬 가능)
- **산출물**: `modules/nf-core/multiqc`, `assets/multiqc_config.yml`, guide 할당 통계 custom content(`*_mqc.tsv`) 생성 로직
- **DoD**:
  - `results/multiqc/multiqc_report.html`에 FastQC, 정량기, "Guide assignment" 섹션 3개 모두 존재(`grep -c` 확인)
  - Guide 섹션에 single/multi/unassigned 비율 표시
- **설명 체크**: custom content 주입 방식

### T-16 전체 샘플 실행 + 할당 검증 ★ 최소 산출물

- **목표**: 선정 데이터 1샘플 완주, 원논문 할당과 비교.
- **선행**: T-14, T-15
- **산출물**: `docs/01_guide_assignment_validation.md`, `bin/compare_assignments.py`
- **DoD**:
  - 선택 호스트에서 `nextflow run . -profile local,docker --input <real samplesheet> ...` 완주, `pipeline_info/execution_report.html` 첨부
  - 비교 문서에: 공통 바코드 수, 일치율(single↔single, guide 동일), 불일치를 최소 3범주(threshold 경계 / multi 판정 차이 / 바코드 미검출)로 분류한 표, method (a)/(b) 각각
  - **일치율 목표 없음**. 수치가 낮으면 원인 분석이 산출물(CLAUDE.md 규칙 6)
  - 실행 시간·피크 메모리 기록(`execution_trace.txt`)
- **설명 체크**: 불일치 주요 원인 3가지, 원논문 방법과 우리 방법의 차이

---

## 6. Phase 3 — 프로덕션화 (에이전트, 7~8주차)

### T-20 CI

- **선행**: T-16
- **산출물**: `.github/workflows/ci.yml` — lint, `-profile test,docker`, `nf-test`
- **DoD**: PR에서 3개 잡 모두 녹색, main 브랜치 보호 규칙(CI 통과 필수) 설정 스크린샷

### T-21 -resume 검증

- **선행**: T-16
- **산출물**: `docs/02_resume_check.md`
- **DoD**: test 프로파일 실행 중 정량 프로세스 시점에 `kill`, `-resume` 재실행, `execution_trace.txt`에서 `CACHED`와 재실행 프로세스 목록 첨부, 재실행이 중단 지점 이후뿐임을 표로 증명

### T-22 스키마·lint

- **선행**: T-16
- **DoD**: `nf-core pipelines schema build` 성공, `nf-core pipelines lint` 오류 0(경고는 목록 첨부 후 허용), `--help` 출력에 모든 파라미터 설명

### T-23 Singularity

- **선행**: T-16
- **DoD**: `nextflow run . -profile test,singularity` 성공(호스트에 Singularity/Apptainer 없으면 Discovery 또는 WSL2에서 실행, 위치 기록)

### T-24 README v1

- **선행**: T-20~T-23
- **DoD**: Mermaid 다이어그램, 설치·실행, 입출력 규격(§2 그대로), 결정 기록 링크, "Status: in development" 배지. 사람 리뷰 승인 커밋

---

## 7. Phase 4 — HPC·클라우드 (에이전트 구성, 사람 실행, 9~10주차)

### T-30 slurm 프로파일 (Discovery 계정 확보 시)

- **산출물**: `conf/slurm.config`
- **DoD**: 전체 샘플 완주, `sha256sum results/alive/<sample>.h5ad` == T-16 값 → `docs/03_cross_profile_hashes.md`

### T-31 AWS Batch 프로파일 (실행 면제 — 010, 2026-09-16; 설정 파일만 산출물)

- **산출물**: `conf/awsbatch.config`, `docs/aws_setup.md`(S3 버킷, compute environment, job queue, IAM 최소 권한 정책 JSON, 리전)
- **DoD**:
  - 사람이 실행. 전체 샘플 완주, h5ad `sha256` == T-16
  - Cost Explorer 스크린샷, 총비용 기록(상한 $100)
  - 종료 후 compute environment 비활성화, S3 work dir 삭제 확인
- **주의**: h5ad가 부동소수 저장 순서 등으로 해시가 갈릴 수 있음. 갈리면 `obs`/`var`/`X` 각각 비교해 수치 동일성으로 대체하고 사유 기록.

### T-32 실행 통계

- **DoD**: README에 표 — 프로파일별 wall time, 피크 메모리, 비용

---

## 8. Phase 5 — 공개 (11주차~)

### T-40 README 완성

- **DoD**: F11 전부, "Status: v1.0" 배지, ALIVE README에서 upstream 링크 커밋

### T-41 nf-core 기여 (선택)

- **DoD**: `nf-core/modules`에 guide_count 또는 guide_assign PR open(머지는 목표 아님, 리뷰 수 주~수 개월)

### T-42 이력서 문구 확정

> Built **<pipeline name — 004 결정>**, a Nextflow DSL2 / nf-core-conventions pipeline processing Perturb-seq raw reads (FASTQ → gene and sgRNA count matrices → per-cell guide assignment → ML-ready h5ad); containerized (Docker/Singularity), CI-tested (GitHub Actions, nf-test), executed reproducibly on local and SLURM (AWS Batch waived by 010); guide assignment validated against published annotations (XX% concordance). Feeds ALIVE, a perturbation-response ML project.

- **DoD**: 문구의 모든 주장이 F1~F13 증빙에 대응. 대응 없는 주장은 삭제.

---

## 9. 병렬 가능 조합

T-01 ∥ T-02 ∥ T-03 ∥ T-05 · T-11 ∥ T-12 · T-13 ∥ T-15 · T-20 ∥ T-21 ∥ T-22 ∥ T-23 · T-30 ∥ T-31

## 10. 리스크

| 리스크                                           | 대응                                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------------------- |
| 적당한 raw Perturb-seq 데이터 부재               | T-01 후보 3개 병렬 확인. 최악: 10x 데모로 완성, Replogle은 README에 "확장 대상" |
| Apple Silicon에서 amd64 컨테이너 에뮬레이션 느림 | T-02에서 실측. WSL2 전환                                                        |
| STAR 인덱스 메모리 부족                          | kallisto 기본                                                                   |
| 에이전트 코드를 설명 못 함                       | §0.3. 부채 있으면 Phase 진행 금지                                               |
| 에이전트가 테스트 약화·값 추측                   | CLAUDE.md 규칙 1·2. PR 리뷰 시 `tests/`, `assets/test_data/` diff 우선 확인     |
| 할당 일치율 낮음                                 | 분석 결과로 문서화(CLAUDE.md 규칙 6)                                            |
| 학기 병행 지연                                   | T-16이 최소 산출물. Phase 4 이후 지연 허용, 이력서 문구에서 해당 주장 삭제      |
| AWS 비용                                         | 예산 알람, 사람만 실행, 종료 후 리소스 삭제 DoD                                 |

## 11. 미검증 항목 (플랜 작성 시점에 확인하지 못한 것)

- Replogle 2022 raw 데이터의 샘플 단위 크기와 guide FASTQ 분리 여부 (Figshare+ 매니페스트 접근 불가였음)
- Adamson/Dixit 2016의 정확한 GEO 접근번호와 guide 캡처 방식
- nf-core 컨테이너의 arm64 지원 범위
- MacBook 사양(칩·RAM)
- NEU Discovery MS 학생 계정 정책
- 위 항목은 각각 T-01, T-02, T-03에서 실측으로 해소한다.

## 12. 결정 기록 색인 (예정)

| 번호 | 주제                                                 | 생성 태스크 |
| ---- | ---------------------------------------------------- | ----------- |
| 001  | 데이터셋                                             | T-01        |
| 002  | GEX 정량기                                           | T-02        |
| 003  | 개발 호스트                                          | T-02        |
| 004  | 저장소·파이프라인 이름                               | T-00        |
| 005  | guide 정량 방법 (kite vs 직접 매칭)                  | T-12        |
| 006  | non-single 세포 처리 (제외/플래그)                   | T-14        |
| 007+ | 필요 시 추가. `docs/decisions/README.md`가 실제 색인 |
