## Guide assignment vs authors (mixture)

| quantity                                    | value                                            |
| ------------------------------------------- | ------------------------------------------------ |
| authors' cells (GEM group)                  | 3681                                             |
| pipeline cells (GEX filtered)               | 7132                                             |
| common barcodes                             | 3681                                             |
| pipeline single among common                | 3398 (92.3%)                                     |
| concordant (single, same vector)            | 3379 = 91.8% of common, 99.4% of pipeline-single |
| concordant at gene level (same target gene) | 3389 (92.1% of common)                           |

| category                    | cells | % of common |
| --------------------------- | ----- | ----------- |
| not_in_authors              | 3451  | 93.8        |
| concordant                  | 3379  | 91.8        |
| multi_pipeline_top1_matches | 148   | 4.0         |
| unassigned_other            | 75    | 2.0         |
| multi_pipeline_top2_matches | 33    | 0.9         |
| unassigned_threshold        | 26    | 0.7         |
| concordant_gene             | 10    | 0.3         |
| discordant_vector           | 9     | 0.2         |
| multi_pipeline_other        | 1     | 0.0         |
