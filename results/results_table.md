### mode: html_text

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 75% (n=12) | 100% (n=15) | 86% (n=14) | 100% (n=15) | 75% (qwen3.5-9b) |
| B_explicit | 50% (n=12) | 100% (n=15) | 80% (n=15) | 100% (n=15) | 50% (qwen3.5-9b) |
| C_faq_structured | 83% (n=12) | 100% (n=15) | 100% (n=15) | 100% (n=15) | 83% (qwen3.5-9b) |
| NOPAGE | 0% (n=13) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| A_original | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |
| A_original | q2_cpu_sandbox_cost | 11 | 1 | 0 | 0 | 12 |
| A_original | q3_signup | 11 | 0 | 0 | 0 | 11 |
| A_original | q4_billing | 9 | 0 | 0 | 2 | 11 |
| A_original | q5_windows | 8 | 0 | 2 | 0 | 10 |
| B_explicit | q1_gpu_ondemand | 9 | 0 | 0 | 3 | 12 |
| B_explicit | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| B_explicit | q3_signup | 11 | 0 | 0 | 0 | 11 |
| B_explicit | q4_billing | 9 | 0 | 0 | 2 | 11 |
| B_explicit | q5_windows | 7 | 0 | 3 | 1 | 11 |
| C_faq_structured | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q3_signup | 11 | 0 | 0 | 0 | 11 |
| C_faq_structured | q4_billing | 11 | 0 | 0 | 0 | 11 |
| C_faq_structured | q5_windows | 9 | 0 | 0 | 2 | 11 |
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 8 | 0 | 0 | 11 |
| NOPAGE | q5_windows | 0 | 11 | 0 | 0 | 11 |

### mode: visible_text

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | – | 90% (n=15) | – | 90% (n=15) | 90% (claude) |
| B_explicit | – | 100% (n=15) | – | 93% (n=15) | 93% (claude) |
| C_faq_structured | – | 100% (n=15) | 100% (n=1) | 100% (n=15) | 100% (claude) |
| NOPAGE | 0% (n=13) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 8 | 0 | 0 | 11 |
| NOPAGE | q5_windows | 0 | 11 | 0 | 0 | 11 |
| A_original | q1_gpu_ondemand | 0 | 3 | 3 | 0 | 6 |
| A_original | q2_cpu_sandbox_cost | 6 | 0 | 0 | 0 | 6 |
| A_original | q3_signup | 6 | 0 | 0 | 0 | 6 |
| A_original | q4_billing | 6 | 0 | 0 | 0 | 6 |
| A_original | q5_windows | 6 | 0 | 0 | 0 | 6 |
| B_explicit | q1_gpu_ondemand | 6 | 0 | 0 | 0 | 6 |
| B_explicit | q2_cpu_sandbox_cost | 6 | 0 | 0 | 0 | 6 |
| B_explicit | q3_signup | 6 | 0 | 0 | 0 | 6 |
| B_explicit | q4_billing | 6 | 0 | 0 | 0 | 6 |
| B_explicit | q5_windows | 5 | 0 | 1 | 0 | 6 |
| C_faq_structured | q1_gpu_ondemand | 7 | 0 | 0 | 0 | 7 |
| C_faq_structured | q2_cpu_sandbox_cost | 6 | 0 | 0 | 0 | 6 |
| C_faq_structured | q3_signup | 6 | 0 | 0 | 0 | 6 |
| C_faq_structured | q4_billing | 6 | 0 | 0 | 0 | 6 |
| C_faq_structured | q5_windows | 6 | 0 | 0 | 0 | 6 |

Excluded infra errors: {'openai: RateLimitError': 60}