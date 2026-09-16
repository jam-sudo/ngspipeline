# nf-core/scrnaseq 4.0.0 — `workflows/scrnaseq.nf` 채널 흐름도 (T-05)

작성: 2026-09-16, `workflows/scrnaseq.nf`(370줄)를 읽고 손으로 정리. 실행 증빙: `nextflow run nf-core/scrnaseq -r 4.0.0 -profile test,docker` 완주 7 min 7 s, 19 프로세스 (`docs/evidence/T-05_scrnaseq_pipeline_dag.html`, `T-05_scrnaseq_execution_trace.txt`; Nextflow 25.10.4 — 26.04.6의 엄격 파서는 이 버전의 `nextflow.config`를 거부한다).

## 채널 흐름 (test 프로파일 = `aligner star`, `protocol 10XV2`, `skip_cellbender true`)

```mermaid
flowchart TD
    IN[ch_fastq<br/>take: samplesheet에서 만든 meta + FASTQ] --> FQ[FASTQC_CHECK<br/>subworkflow, skip_fastqc면 생략]
    P[params.fasta / gtf / transcript_fasta / txp2gene<br/>→ file() 값 채널] --> GZ[GUNZIP_FASTA / GUNZIP_GTF<br/>.gz일 때만]
    GZ --> GF[GTF_GENE_FILTER<br/>local module]
    GF --> ALN{params.aligner}
    IN --> ALN
    ALN -->|kallisto| KB[KALLISTO_BUSTOOLS<br/>subworkflow: kb ref → kb count<br/>emit counts_raw, counts_filtered, txp2gene]
    ALN -->|star| SS[STARSOLO<br/>subworkflow: STAR_GENOMEGENERATE → STAR_ALIGN<br/>emit raw_counts, filtered_counts]
    ALN -->|simpleaf| SA[SIMPLEAF]
    ALN -->|cellranger*| CR[CELLRANGER_ALIGN / _MULTI_ / _ARC_]
    KB --> MTX[ch_mtx_matrices<br/>Channel.empty().mix(...) 로 정렬기 출력들을 한 채널에 모음<br/>meta.input_type = raw | filtered]
    SS --> MTX
    SA --> MTX
    CR --> MTX
    MTX --> H5[MTX_TO_H5AD<br/>local module, 샘플 × input_type 마다 1 태스크]
    H5 --> CB{skip_cellbender?}
    CB -->|no| CBS[H5AD_REMOVEBACKGROUND_BARCODES_CELLBENDER_ANNDATA<br/>raw만 filter → meta.input_type = cellbender_filter]
    CBS --> H5S[ch_h5ads.mix]
    CB -->|yes| H5S
    H5S --> CONV[H5AD_CONVERSION<br/>subworkflow: ANNDATAR_CONVERT(샘플별) → CONCAT_H5AD(combined) → ANNDATAR_CONVERT(combined)]
    FQ --> MQF[ch_multiqc_files.mix<br/>+ versions.yml collectFile + methods description]
    SS --> MQF
    MQF --> MQ[MULTIQC]
    MQ --> OUT[emit: multiqc_report]
```

## 읽으면서 확인한 것

- `take: ch_fastq` 하나만 받고 나머지 입력은 `params.*`를 `file()`로 감싼 값 채널이다. 우리 파이프라인이 파라미터를 `take:`로 모두 넘기는 것과 다른 스타일이다.
- 정렬기 분기는 `if (params.aligner == ...)`로 서브워크플로를 조건 호출하고, 결과를 `ch_mtx_matrices = Channel.empty().mix(...)`에 모은다. 그래서 하류(`MTX_TO_H5AD`)는 어느 정렬기가 돌았는지 모르고 `meta.input_type`(raw/filtered)만 본다.
- `H5AD_CONVERSION`이 샘플별 h5ad를 `CONCAT_H5AD (combined)`로 합친다. 우리 011의 `--pool_alive`와 같은 문제(샘플 간 바코드 충돌)를 다루는 지점으로, scrnaseq는 `meta`에서 sample id를 obs에 붙인다.
- test 프로파일은 mouse chr19 미니 게놈 + 2샘플, STAR 정렬 2 min이 가장 길다. cellbender는 작은 데이터에서 동작하지 않아 건너뛴다.
- 실행 DAG(`pipeline_dag_*.html`)에는 조건 분기에서 실제로 실행된 STARSOLO 경로만 나타난다. 코드에는 다섯 정렬기가 있어도 DAG는 한 번의 실행 기록이다.
