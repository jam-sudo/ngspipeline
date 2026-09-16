# 04 — Explanation checks: questions and answers

Written by the agent on 2026-09-16 under the human's delegation ("설명 체크 질문들 너 답변 승인"). PLAN.md §0.3 intends these as the human's interview preparation; this document is the reference answer set. `docs/learning_debt.md` records that no question is currently unanswered by the human because the human has not yet attempted them, not because they were answered.

Numbering: `T-xx.n` = question n of the PR for task T-xx (PR bodies #1–#19).

## T-00 저장소 초기화 (PR #1)

**T-00.1 `main.nf`와 `workflows/ngspipeline.nf`의 역할 분리.** `main.nf`는 진입점이다. 파라미터 검증(nf-schema), 샘플시트 파싱, 초기화·완료 서브워크플로(`PIPELINE_INITIALISATION`, `PIPELINE_COMPLETION`) 같은 "런타임 껍데기"를 담당하고, 실제 분석 로직은 `workflows/ngspipeline.nf`의 `NGSPIPELINE` 워크플로에 있다. 분리해 두면 분석 워크플로를 다른 진입점(테스트 하네스, 상위 파이프라인)에서 `include`해 재사용할 수 있고, nf-core 템플릿 동기화 때 껍데기만 갱신되어 분석 코드와 충돌하지 않는다.

**T-00.2 `TEMPLATE` 브랜치.** nf-core 템플릿 원본만 담는 브랜치다. `nf-core pipelines sync`는 새 템플릿 버전을 이 브랜치에 커밋하고, 그 diff를 `dev`에 병합하는 PR을 만든다. 사람이 `TEMPLATE`에 직접 커밋하면 "템플릿 원본"이라는 전제가 깨져 다음 sync의 3-way 병합 기준이 사라지고 충돌이 폭증한다.

**T-00.3 `-profile test,docker`.** 프로파일은 쉼표 순서대로 적용되며 나중 것이 앞의 설정을 덮어쓴다. `test`는 파라미터(입력 경로, `chemistry`, 자원 상한)를, `docker`는 컨테이너 엔진을 켠다. 두 프로파일이 같은 키를 건드리지 않으면 순서는 무관하지만, 예를 들어 둘 다 `process.resourceLimits`를 정의하면 뒤에 쓴 프로파일 값이 이긴다. 그래서 자원 캡을 정하는 `test`를 앞에, 실행 환경을 뒤에 두는 관례를 따른다.

## T-01 데이터셋 (PR #2)

**T-01.1 왜 Replogle 2022 K562 essential lane_4인가.** ALIVE가 학습하는 바로 그 연구의 원 리드라서 파이프라인이 ALIVE 입력을 "처음부터" 재생산한다는 주장이 성립한다. 한 GEM group(15.9 GB)이면 50 GB 기준을 만족하고, 저자의 세포별 guide 할당이 CC BY 4.0 h5ad에 있다. 기각 사유: RPE1은 ALIVE의 봉인 holdout 세포주(규칙 11); Dixit 2016은 guide 바코드가 전사체 리드 안에 있어 별도 guide FASTQ가 없음; Adamson 2016은 SRA에 BAM만 있고 화학 버전이 미기재; 10x 데모 두 개는 표준 형식이지만 "저자 독립적 할당"이 Cell Ranger 자체 결과뿐이라 검증 대상으로 약해 대체 후보로만 둠.

**T-01.2 guide 캡처 라이브러리가 별도 FASTQ인 이유.** direct-capture Perturb-seq은 sgRNA 스캐폴드에 capture sequence(cs1)를 넣어 gel bead 위의 상보 서열이 sgRNA를 직접 잡는다. 이렇게 잡힌 sgRNA 분자는 polyA cDNA와는 별도의 feature-barcode 라이브러리로 증폭·시퀀싱되므로 FASTQ가 따로 나온다. Dixit 2016은 이 화학 이전 세대라 guide 벡터가 polyA가 붙은 전사체(GBC)를 발현하게 하고 그 전사체를 일반 3' cDNA 라이브러리에서 읽었다. 그래서 guide 정보가 GEX 리드 안에 섞여 있다.

**T-01.3 whitelist와 feature-barcode 바코드가 다르다는 것.** 3' v3 gel bead는 한 비드에 두 종류의 바코드 변이(GEX용, feature용)를 실어 나른다. 같은 세포에서 나온 GEX 리드와 guide 리드는 서로 다른 16-mer를 갖고, `3M-february-2018` 번역 표의 같은 행으로 대응된다. lane_4 실측에서 guide R1 바코드가 GEX 바코드와 직접 일치하는 비율은 0.2 %, 번역 후 일치는 36 %였다. 파이프라인에서는 kb의 `kite:10xFB` 워크플로가 번역을 수행하며(`GUIDE_COUNT`), 그 결과 guide 행렬의 바코드가 GEX 바코드 형태로 나와 `GUIDE_ASSIGN`에서 바로 join된다.

## T-02 개발 호스트·정량기 (PR #3)

**T-02.1 pseudoalignment vs alignment.** kallisto는 리드의 k-mer가 어떤 전사체 집합(equivalence class)과 양립하는지만 결정하고 염기 단위 정렬 위치는 구하지 않는다. 그래서 수십 배 빠르고 메모리가 작지만 BAM(정렬 좌표), splice junction, 변이 정보를 잃는다. STARsolo는 게놈에 spliced alignment를 수행해 좌표·intron 정보를 얻지만 인간 인덱스에 약 32 GB가 필요하고 느리다. 세포×유전자 count가 목적인 이 프로젝트에는 pseudoalignment의 손실이 문제되지 않는다.

**T-02.2 선택 근거.** PLAN의 규칙은 "어느 호스트에서도 STAR 인덱스가 안 되면 kallisto 기본"이다. 실측: MacBook 24 GB(VM 최대 20 GB) < 32 GB, WSL2 데스크톱은 Tailscale에서 124일째 오프라인, Discovery 계정 없음. 덧붙여 nf-core `kb ref`조차 전체 게놈 분할 단계에서 20 GB를 넘겨 OOM되었고, cDNA+ncRNA로 만든 kallisto 인덱스는 297초/15.7 GiB에 빌드되었다. 그래서 정량기는 kallisto|bustools, 전체 참조는 사전 빌드 인덱스(`--reference_index`)다.

**T-02.3 Apple Silicon에서 amd64 컨테이너.** 컨테이너 안의 x86-64 바이너리는 커널의 binfmt_misc가 가로채 사용자 공간 에뮬레이터로 넘긴다. Rosetta 2는 x86-64 코드를 arm64로 미리 번역(AOT/JIT)해 거의 네이티브에 가깝고, QEMU user-mode는 명령어를 하나씩 해석해 수 배~수십 배 느리다. 이 프로젝트에서 Rosetta가 실제로는 설치되지 않아 QEMU로 돌던 동안 FastQC 한 작업이 6분 넘게 걸렸고, Rosetta 설치 후 같은 작업이 6초였다. 결과 자체(수치)는 동일해야 하지만, 실행 시간이 달라지고 부동소수 연산 경로 차이로 아주 드물게 하위 비트가 달라질 수 있어 프로파일 간 해시 비교(F7)를 둔다.

## T-10 테스트 데이터 (PR #4)

**T-10.1 바코드 기준 + UMI 패밀리 서브샘플링.** 세포를 기준으로 자르면 선택한 세포의 리드가 전부 보존되어 세포 호출, guide 할당, 세포×유전자 행렬이 실제와 같은 구조를 가진다. 그러나 한 세포에 약 29,000 리드가 있어 120세포면 15 MB 예산을 넘긴다. 그래서 각 세포 안에서 UMI 단위로 5 %를 남겼다. `md5(barcode+UMI)`가 임계값 아래인 UMI의 리드를 전부 남기므로 한 UMI의 리드 무리(패밀리)는 통째로 남거나 통째로 빠진다.

**T-10.2 리드를 무작위로 뽑으면.** UMI 패밀리가 쪼개진다. 어떤 UMI는 리드 1개만 남아 "중복 제거"가 무의미해지고, 리드 수 대비 UMI 수(포화도)가 실제 데이터와 전혀 다른 분포가 된다. 또 낮은 깊이의 세포는 UMI가 거의 남지 않아 세포 호출(knee)이 왜곡된다. UMI 패밀리 단위 샘플링은 UMI 수를 일정 비율로 줄이되 패밀리 내부 구조는 유지한다.

**T-10.3 미니 게놈의 효과.** 참조가 200개 유전자 locus 뿐이지만 `kb ref`(인덱스 빌드)와 `kb count`(pseudoalignment, 바코드 보정, UMI 카운트, 세포 필터)가 실제 참조와 똑같이 실행된다. 대신 다른 유전자에서 온 리드는 어디에도 맞지 않으므로 pseudoalignment 비율이 27.5 %로 낮고(실제 lane_4는 69.2 %), 세포당 UMI도 낮다. 매핑률·UMI 깊이는 테스트 데이터에서 해석하지 않는다.

## T-11 GEX 정량 (PR #5)

**T-11.1 whitelist(on-list) 사용.** `-x 10XV3`를 주면 kb-python이 컨테이너에 동봉된 `10x_version3_whitelist.txt`(6,794,880개)를 복사해 쓴다. 순서는 kallisto가 BUS 파일(바코드·UMI·equivalence class 레코드)을 만들고, `bustools sort` 뒤 `bustools correct`가 각 바코드를 on-list와 비교해 해밍 거리 1 이내면 on-list 서열로 교정한다. 교정 단계는 pseudoalignment 뒤, 카운트 전이다.

**T-11.2 UMI 중복 제거.** `bustools count` 단계에서 (교정된 바코드, UMI, equivalence class) 조합이 같은 레코드를 하나로 합친다. 즉 단위는 세포 바코드 × UMI × equivalence class이며, 같은 UMI가 여러 리드에서 관측되어도 한 분자로 센다. 유전자 수준 행렬은 equivalence class를 t2g로 유전자에 사상해 얻고, 여러 유전자에 걸치는 class는 기본 설정에서 버려진다.

**T-11.3 `--filter bustools`.** UMI 총합으로 바코드를 정렬한 곡선의 knee(변곡점)를 찾아 그 위를 세포로 본다. 테스트 데이터는 설계상 세포 120개 + 배경 바코드 300개였고, 필터 결과 119개가 남았으니 배경을 거의 정확히 걸러낸 것이다. 빠진 1개는 UMI가 낮아 배경과 겹친 세포다.

## T-12 guide 정량 (PR #6)

**T-12.1 kite와 mismatch.** kite는 각 protospacer(20-mer)와 그 해밍 거리 1 변이(20×3 = 60개)를 모두 "전사체"로 삼는 kallisto 인덱스를 만든다. 리드 안에 정확히 일치하거나 1 mismatch인 20-mer가 있으면 그 feature에 배정된다. 오류가 2개면 어떤 변이와도 일치하지 않아 셀 수 없다. 이는 설계상의 한계이며, lane_4에서 라이브러리와 일치하지 않은 리드 26 %의 대부분이 여기에 해당한다(전체 라이브러리로 대조해도 24 %는 여전히 불일치).

**T-12.2 k와 protospacer 길이.** kite는 k = feature 길이(20)로 인덱스를 만든다. k를 20보다 작게 잡으면 한 리드의 k-mer가 여러 protospacer에 걸쳐 모호해지고(특히 공유 서열이 많은 라이브러리), 크게 잡으면 20-mer 하나로는 k-mer가 만들어지지 않아 아무것도 셀 수 없다. 그래서 k = 20이 유일한 선택이고, 라이브러리의 protospacer가 모두 같은 길이여야 한다(`GUIDE_INDEX`가 검사).

**T-12.3 바코드 번역.** guide 리드의 R1 바코드는 feature 변이라서 번역하지 않으면 GEX 행렬의 바코드와 99.8 %가 서로 다른 문자열이 된다. join하면 거의 모든 세포가 "guide 없음"이 되고, 우연히 일치한 소수는 엉뚱한 세포에 붙는다. `kite:10xFB`가 번역 표를 써서 guide 행렬의 바코드를 GEX 형태로 바꿔 놓으므로 `GUIDE_ASSIGN`은 문자열 그대로 join한다.

## T-13 guide 할당 (PR #7)

**T-13.1 두 방식이 갈리는 세포.** (a) top-1 UMI가 `min_umi`는 넘지만 그 벡터의 양성군(예: 40–60 UMI)보다 훨씬 낮은 세포: threshold는 single, mixture는 배경으로 보아 unassigned. 합성 테스트에서 V1 = 30이 정확히 이 경우였다. (b) 두 벡터가 모두 양성군 수준인 세포: threshold는 비율 < 3이면 multi, mixture도 두 posterior가 모두 > 0.5면 multi로 대체로 일치. (c) top-2가 양성군 하단에 걸친 세포: threshold는 비율에 따라, mixture는 그 벡터의 posterior에 따라 갈린다. lane_4에서 두 방식이 다른 세포는 3,681개 중 207개였다.

**T-13.2 multi 세포와 ALIVE.** ALIVE는 obs 라벨 하나를 perturbation으로 읽고 빈 라벨이면 중단하므로 multi 세포에 줄 수 있는 라벨이 없다. 제외(006 채택)는 학습 데이터를 깨끗하게 하지만 doublet 비율만큼 세포를 잃고, 플래그(라벨을 "multi"로)는 세포를 보존하지만 ALIVE가 그것을 하나의 perturbation으로 학습해 버린다. 그래서 기본은 제외, `--keep_nonsingle`은 검사용이며 상태 집계는 h5ad `uns`와 MultiQC에 남는다.

**T-13.3 posterior > 0.5와 fitting 한계.** 벡터마다 log2 UMI 분포를 배경(Poisson)과 양성(Gaussian) 두 성분의 혼합으로 보고, 어떤 세포의 값이 양성 성분에서 왔을 사후확률이 0.5를 넘으면 그 벡터를 가진 것으로 본다. 0.5는 두 성분 중 더 그럴듯한 쪽을 택하는 최대 사후 결정이다. 벡터당 세포가 몇 개뿐이면(lane_4는 벡터당 중앙값 2세포) 두 성분의 평균·분산을 추정할 자료가 없어 EM이 무의미하므로, `min_cells_fit`(10) 미만인 벡터는 count 기준 폴백을 쓴다. 저자는 31만 세포 전체로 적합했다.

## T-15 MultiQC (PR #8)

**T-15.1 custom content 주입.** 파일명이 `*_mqc.tsv`(또는 `.txt/.json/.yaml`)이면 MultiQC가 custom content로 읽는다. 첫 줄들의 `# id:`, `# section_name:`, `# plot_type:`, `# pconfig:` 주석이 섹션 이름과 플롯 종류를 정한다. `bargraph`는 샘플별 범주 개수를 막대로, `table`은 열 단위 값 표로 그리고, `generalstats`는 리포트 맨 위 General Statistics 표에 열을 추가한다.

**T-15.2 `collectFile`로 만드는 장단점.** 프로세스가 없으니 규칙 4(손 모듈 4개 제한)를 지키고 컨테이너도 필요 없다. 단점은 `collectFile` 산출물이 태스크 캐시가 아니라서 `-resume` 때마다 다시 만들어지고, 그것을 입력으로 받는 MULTIQC도 매번 재실행된다(약 15초). 또 Groovy 코드가 워크플로 파일 안에 있어 단위 테스트가 어렵다.

**T-15.3 낮은 pseudoaligned %.** 테스트 참조가 200개 유전자뿐이라 나머지 유전자 리드는 어디에도 맞지 않는다(27.5 %). 실제 lane_4는 69.2 %였고, 10x 3' 데이터에서 kallisto 전사체 참조 기준 60–75 %가 보통이다. guide 라이브러리는 TSO·scaffold 부분이 인덱스에 없으니 protospacer만 맞아 68 % 수준이 정상이다.

## T-14 ALIVE h5ad (PR #9)

**T-14.1 obs 컬럼과 ALIVE 소비 지점.** `gene`은 perturbation 라벨(ALIVE `perturbation_key`, 대조군 `non-targeting`)로 `replogle.py`의 `build_index`가 세포를 라벨별로 묶을 때 쓰는 유일한 컬럼이다. `cell_barcode`는 인덱스, `guide_id`는 할당된 벡터(A|B), `target_gene`은 그 유전자, `assignment_status`/`assignment_confidence`/`assignment_method`/`top1_umi`/`top2_umi`/`total_guide_umi`는 할당 근거, `sample_id`는 샘플 이름이다. ALIVE는 `gene` 외의 obs를 읽지 않는다.

**T-14.2 ALIVE가 QC를 하지 않는 것의 의미.** 세포 호출(bustools knee), guide 할당, multiplet 제거는 전적으로 이 파이프라인의 책임이다. h5ad에 들어간 세포는 그대로 학습 대상이 되므로, 세포 수·라벨 품질을 보고하는 것(MultiQC, `uns["assignment"]`)과 006 같은 제외 정책이 파이프라인 문서에 있어야 한다.

**T-14.3 non-single 제외의 편향과 기록.** doublet과 guide 미검출 세포를 빼면 남는 세포가 "깨끗한 단일 perturbation"으로 편향되고, 벡터당 세포 수가 줄어 ALIVE의 `min_cells` 문턱을 넘지 못하는 perturbation이 늘어난다. 또 같은 벡터의 doublet은 잡히지 않는다. 제외된 세포는 `guides/<sample>/assignment.tsv`에 전부 남고, 개수는 h5ad `uns["assignment"]["status_counts"]`와 MultiQC guide 섹션에 있다.

## T-16 전체 샘플 실행·검증 (PR #10; PLAN 설명 체크)

**T-16.1 불일치의 주요 원인 3가지.** (1) 두 벡터가 모두 높은 세포(multi, 91개): 저자의 벡터가 top-1이거나 top-2인데 두 번째 벡터가 1/3 이상이라 threshold가 multi로 판정 — doublet 또는 같은 유전자의 두 벡터. (2) `min_umi` 경계(26개): 저자 벡터가 top-1이지만 UMI 1–4개라 unassigned. (3) 벡터 불일치(15개): 파이프라인이 다른 벡터를 single로 택했고 13개에서 저자 벡터가 top-2. 여기에 같은 유전자의 다른 벡터(10개)와 기타 미할당(7개)이 더해져 공통 3,681세포의 4 %다.

**T-16.2 원논문 방법과 우리 방법의 차이.** 저자는 Cell Ranger로 세포·guide를 세고 31만 세포 전체에서 guide별 Poisson–Gaussian 혼합모델을 100회 적합해 posterior > 0.5로 할당했으며, 단일 guide이거나 같은 유전자의 두 guide인 세포만 남겼다. 우리는 kallisto|bustools(GEX)와 kite(guide)로 세고, 한 GEM group만 있어 기본은 threshold(10/3), mixture는 벡터당 세포가 적어 대부분 폴백이다. 세포 호출도 다르다(bustools knee 7,132 vs 저자 3,681).

**T-16.3 저자 표에 없는 3,451세포.** GEX 깊이는 저자 세포와 같고(중앙값 14,286 vs 13,811 UMI), 1,525개는 single이다. multi 1,394개와 unassigned 532개는 저자의 multiplet·guide 미검출 제거와 맞지만, single 1,525개가 빠진 이유는 저자 표만으로는 알 수 없다(추가 QC로 추정). 문서에는 "기록만, 해결 안 됨"으로 남겼다.

## T-20 CI (PR #11)

**T-20.1 `matrix.ec`가 달라지는 이유.** kallisto가 pseudoalignment 중에 만나는 equivalence class에 번호를 붙이는데, 멀티스레드 실행에서 리드 처리 순서가 달라지면 같은 class 집합이 다른 번호를 받는다. `matrix.ec`는 이 번호→전사체 집합 표이므로 바이트가 달라진다. 카운트는 (바코드, UMI, class 집합) 단위로 세고 유전자로 사상하므로 번호 부여와 무관하게 같다.

**T-20.2 `nf_test_content`가 versions.yml 스냅샷을 요구하는 이유.** 파이프라인 수준 테스트가 소프트웨어 버전 파일을 스냅샷하면 도구 버전이 바뀔 때 테스트가 알려 주고, 결과 변화의 원인을 버전 변경과 분리할 수 있다. nf-core는 `tests/` 아래 테스트를 파이프라인 테스트로 간주해 이 규칙을 적용한다. 모듈 단위 테스트는 `modules/local/*/tests/`에 두어 이 규칙 밖에 둔다.

**T-20.3 두 Nextflow 버전과 최소 버전.** 고정 버전(25.10.4)은 `manifest.nextflowVersion = '!>=25.10.4'`의 하한과 같아 "선언한 최소 버전에서 실제로 돌아간다"를 보증하고, latest-everything은 새 버전에서의 회귀를 미리 알려 준다(continue-on-error라 실패해도 PR을 막지 않음). 최소 버전은 파이프라인이 쓰는 문법·기능(topic 채널, `eval` 출력, 엄격 문법)이 처음 안정화된 버전으로 정하며, 템플릿이 기본값을 준다.

## T-21 -resume (PR #13/#17)

**T-21.1 CACHED 판정 기준.** 태스크 해시는 프로세스 이름, 스크립트 본문, 컨테이너 이미지, 입력 값과 입력 파일의 경로·크기·수정시각(기본 모드), 그리고 `ext.args` 같은 설정 값으로 만든다. cpus/memory/time 같은 자원 지시자, 출력 파일, `publishDir` 설정은 해시에 들어가지 않는다. 같은 해시의 work 디렉토리에 `.exitcode` 0과 출력이 있으면 CACHED다.

**T-21.2 MULTIQC가 매번 도는 이유.** 입력 중 `collectFile`로 만든 파일(버전 yml, `kb_quant_mqc.tsv`, 워크플로 요약)은 실행마다 새 경로·수정시각으로 생성되어 해시가 바뀐다. 피하려면 그 표를 만드는 단계를 프로세스로 만들어 캐시되게 하거나, `collectFile`에 `storeDir`/고정 이름을 주고 내용 해시 기반 스테이징(`cache = 'lenient'`)을 쓰면 된다. 15초짜리라 그대로 둔 것은 의도된 선택이다.

**T-21.3 SIGTERM 받은 태스크.** Nextflow가 컨테이너를 죽이고 태스크를 ABORTED로 기록하며 work 디렉토리에는 `.exitcode`가 없거나 0이 아니다. 재실행 시 같은 해시의 디렉토리에 완료 표시가 없으므로 새 work 디렉토리에서 처음부터 다시 돌리고, 완료된 상류 태스크는 CACHED로 건너뛴 뒤 DAG 순서대로 하류가 이어진다.

## T-24 README (PR #12/#18)

**T-24.1 nf-core 모듈과 local 모듈의 경계.** FASTQC, KALLISTOBUSTOOLS_REF/COUNT, MULTIQC는 nf-core 모듈이고 GUIDE_INDEX, GUIDE_COUNT, GUIDE_ASSIGN, TO_ALIVE_H5AD 넷이 local이다. kite 인덱스 빌드, feature-barcode 번역이 있는 kite 카운트, 벡터 단위 할당, ALIVE 규격 h5ad는 nf-core에 대응 모듈이 없거나(kite), 이 프로젝트 고유 규격이라서 손으로 썼다. CLAUDE.md 규칙 4가 이 넷으로 제한한다.

**T-24.2 `expected_cells`.** 샘플시트 열로 `meta.expected_cells`에 들어가고, `GEX_QUANT`가 필터된 세포 수를 로그로 찍을 때 "기대 대비 %"를 계산하는 데만 쓴다(T-11 DoD의 80 % 기준). 세포 호출 자체(bustools knee)에는 쓰지 않는다.

**T-24.3 v1.0 배지의 조건.** PLAN §1의 F1~F13 전부에 증빙이 있어야 한다. 현재 열린 것은 F5(최근 10커밋 CI 녹색), F7(3개 프로파일 h5ad 해시), F9(ALIVE 베이스라인 1회 실행), F11(README 실행 통계의 slurm/AWS 행), F12(학습 부채 비어 있음 — 사람이 설명 체크에 답해야 함)이다.

## T-30 SLURM (PR #14)

**T-30.1 `queueSize`/`submitRateLimit`.** 공유 클러스터는 사용자당 동시 작업 수와 초당 제출 수를 제한하며, 한꺼번에 수백 개를 제출하면 스케줄러가 거부하거나 계정이 제재된다. `queueSize`는 동시에 큐에 넣는 작업 수, `submitRateLimit`는 제출 속도를 제한한다. 값은 클러스터 문서의 QOS 한도에 맞춘다(Discovery는 NEEDS_HUMAN).

**T-30.2 `resourceLimits`와 라벨.** `conf/base.config`의 라벨(process_low 2 CPU/12 GB, medium 6/36 GB, high 12/72 GB 등)이 요청량을 정하고, `resourceLimits`는 그 요청을 프로파일이 정한 상한으로 잘라 준다. 그래서 같은 모듈이 MacBook(16 GB 상한)에서는 잘려서, 클러스터(180 GB)에서는 라벨 그대로 요청된다. 재시도 시 라벨 값이 배수로 늘어나도 상한을 넘지 못한다.

**T-30.3 프로파일 간 해시 차이.** h5ad는 HDF5 컨테이너라 압축 청크, 문자열 인코딩, anndata 버전, 부동소수 합산 순서(스레드 수)에 따라 바이트가 달라질 수 있다. 그때는 해시 대신 `obs`·`var`·`X`를 수치로 비교한다(행 순서 정렬 후 X 동일성, obs 문자열 동일성). PLAN T-31 주석이 이 대체 검증을 허용한다.

## T-31 AWS Batch (PR #15)

**T-31.1 Spot 중단 시.** work 디렉토리가 S3에 있으므로 완료된 태스크의 출력과 `.exitcode`는 남고, 중단된 태스크만 Nextflow가 재시도(errorStrategy retry)하거나 `-resume`으로 다시 돈다. kb count 같은 단일 긴 태스크는 처음부터 다시 계산된다. 즉 보장되는 것은 완료 태스크의 재사용이고, 잃는 것은 진행 중이던 태스크의 시간이다.

**T-31.2 IAM 분리.** S3 권한은 특정 버킷 ARN으로 좁힐 수 있지만, Batch API(SubmitJob, DescribeJobs 등)는 자원 수준 제한을 지원하지 않는 호출이 많아 `Resource: *`가 사실상 필요하다. 그래서 데이터 접근(S3)은 최소 범위로, 작업 제어(Batch)는 API 화이트리스트로 제한하고, 실제 컴퓨팅 노드의 인스턴스 역할은 별도로 둔다.

**T-31.3 S3 work dir과 Fusion.** 태스크마다 입력을 S3에서 EBS로 내려받고 출력을 다시 올리므로(AWS CLI 스테이징) 전송 시간과 요청 비용이 든다. 15 GB FASTQ면 kb count 한 번에 수 분이 추가된다. Fusion 파일시스템을 쓰면 S3를 POSIX처럼 마운트해 스테이징 단계가 사라지고 `aws_cli` 설정이 필요 없어지지만 Wave 컨테이너와 라이선스 조건이 붙는다.

## T-32 실행 통계 (PR #16)

**T-32.1 벽시계와 realtime 합의 차이.** 태스크는 자원 한도 안에서 병렬로 돌고(FastQC와 kb count 동시), 큐 대기·컨테이너 기동·스테이징 시간은 realtime에 포함되지 않으며, 재시도된 태스크는 두 번 세어진다. lane_4는 FastQC 첫 시도 1h32m이 실패 후 재시도되어 벽시계 2h23m이 되었고, 그 시도를 빼면 약 50분이다.

**T-32.2 kb count 15.9 GB.** nf-core 모듈이 `bustools sort -m (task.memory − 1) GB`를 넘기므로 정렬 버퍼가 배정 메모리를 거의 다 쓴다. 메모리를 줄이면 버퍼가 작아져 정렬이 여러 번의 부분 정렬과 병합(외부 정렬)으로 바뀌어 디스크 I/O가 늘고 느려지지만 결과는 같다. kallisto 자체는 인덱스 크기(약 4 GB)만 필요하다.

**T-32.3 AWS 비용 추정.** vCPU-시간은 이 문서의 프로세스별 realtime × 배정 vCPU에서, 스팟 가격은 AWS Spot Instance Advisor 또는 `describe-spot-price-history`에서, S3 전송·요청 비용은 입력 크기(약 17 GB 업로드, 결과 약 1 GB)와 요청 수로 계산한다. lane_4 한 샘플은 16 vCPU 1시간 이내라 스팟 기준 수 달러 수준이다.

## T-13b 임계값 기본값 (PR #19)

**T-13b.1 빈 방울 99백분위 기준.** 빈 방울의 guide UMI는 ambient(세포 밖에서 떠다니는 guide 전사체)의 척도다. 세포가 "진짜로" 벡터를 가진다고 부르려면 그 벡터 UMI가 ambient 노이즈보다 확실히 커야 하므로 빈 방울 top-1의 99백분위(6) 위의 10을 택했다. 일치율 기준으로 정하면 저자 결과를 정답으로 놓고 맞추는 튜닝이 되어 독립 검증이 아니게 된다(CLAUDE.md 규칙 6).

**T-13b.2 T-16 표를 다시 계산하지 않는 이유.** 그 표는 "5/3으로 돌렸을 때의 발견"이며, 기본값을 바꾼 뒤 재계산해 더 좋아지거나 나빠진 수치를 싣는 순간 임계값 선택이 결과에 의존하게 된다. 새 기본값의 효과는 009에 "752세포가 min_umi 아래"로 기록했고, 다음 전체 실행부터 10/3이 적용된다.

**T-13b.3 테스트 프로파일이 5/3인 이유.** 테스트 데이터는 guide 리드를 10 %만 남겼으므로 세포당 guide UMI가 실제의 약 1/10이다. 기본값 10을 쓰면 대부분 세포가 unassigned가 되어 할당·h5ad 단계가 검증되지 않는다. 그래서 테스트 전용으로 5/3을 명시하고, 이 값이 운영 기본값이 아님을 `conf/test.config` 주석에 적었다.
