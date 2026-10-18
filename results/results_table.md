### mode: html_text

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 73% (n=15) | 100% (n=15) | 80% (n=15) | 100% (n=15) | 73% (qwen3.5-9b) |
| B_explicit | 47% (n=15) | 100% (n=15) | 80% (n=15) | 100% (n=15) | 47% (qwen3.5-9b) |
| C_faq_structured | 80% (n=15) | 100% (n=15) | 100% (n=15) | 100% (n=15) | 80% (qwen3.5-9b) |
| NOPAGE | 0% (n=15) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| A_original | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |
| A_original | q2_cpu_sandbox_cost | 11 | 1 | 0 | 0 | 12 |
| A_original | q3_signup | 12 | 0 | 0 | 0 | 12 |
| A_original | q4_billing | 9 | 0 | 0 | 3 | 12 |
| A_original | q5_windows | 9 | 0 | 3 | 0 | 12 |
| B_explicit | q1_gpu_ondemand | 9 | 0 | 0 | 3 | 12 |
| B_explicit | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| B_explicit | q3_signup | 12 | 0 | 0 | 0 | 12 |
| B_explicit | q4_billing | 9 | 0 | 0 | 3 | 12 |
| B_explicit | q5_windows | 7 | 0 | 3 | 2 | 12 |
| C_faq_structured | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q3_signup | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q4_billing | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q5_windows | 9 | 0 | 0 | 3 | 12 |
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 9 | 0 | 0 | 12 |
| NOPAGE | q5_windows | 0 | 12 | 0 | 0 | 12 |

### mode: rendered_text

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 100% (n=3) | 83% (n=3) | 17% (n=3) | 100% (n=3) | 17% (gemma4-26b) |
| C_faq_structured | 100% (n=3) | 100% (n=3) | 100% (n=3) | 100% (n=3) | 100% (claude) |
| NOPAGE | 0% (n=15) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 9 | 0 | 0 | 12 |
| NOPAGE | q5_windows | 0 | 12 | 0 | 0 | 12 |
| A_original | q1_gpu_ondemand | 8 | 3 | 1 | 0 | 12 |
| C_faq_structured | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |

### mode: visible_text

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 80% (n=15) | 90% (n=15) | 67% (n=15) | 90% (n=15) | 67% (gemma4-26b) |
| B_explicit | 60% (n=15) | 100% (n=15) | 80% (n=15) | 93% (n=15) | 60% (qwen3.5-9b) |
| C_faq_structured | 80% (n=15) | 100% (n=15) | 100% (n=15) | 100% (n=15) | 80% (qwen3.5-9b) |
| NOPAGE | 0% (n=15) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 9 | 0 | 0 | 12 |
| NOPAGE | q5_windows | 0 | 12 | 0 | 0 | 12 |
| A_original | q1_gpu_ondemand | 0 | 8 | 4 | 0 | 12 |
| A_original | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| A_original | q3_signup | 12 | 0 | 0 | 0 | 12 |
| A_original | q4_billing | 12 | 0 | 0 | 0 | 12 |
| A_original | q5_windows | 9 | 0 | 3 | 0 | 12 |
| B_explicit | q1_gpu_ondemand | 10 | 0 | 0 | 2 | 12 |
| B_explicit | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| B_explicit | q3_signup | 12 | 0 | 0 | 0 | 12 |
| B_explicit | q4_billing | 10 | 0 | 0 | 2 | 12 |
| B_explicit | q5_windows | 6 | 0 | 4 | 2 | 12 |
| C_faq_structured | q1_gpu_ondemand | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q2_cpu_sandbox_cost | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q3_signup | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q4_billing | 12 | 0 | 0 | 0 | 12 |
| C_faq_structured | q5_windows | 9 | 0 | 0 | 3 | 12 |

Excluded infra errors: {'openai: RateLimitError': 60}