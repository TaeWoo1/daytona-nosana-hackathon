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

### mode: rendered_text_v2

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 67% (n=6) | 50% (n=10) | 100% (n=9) | 100% (n=8) | 50% (gpt-oss-20b) |
| C_faq_structured | 100% (n=5) | 100% (n=5) | 100% (n=5) | 100% (n=5) | 100% (claude) |
| NOPAGE | 0% (n=15) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 9 | 0 | 0 | 12 |
| NOPAGE | q5_windows | 0 | 12 | 0 | 0 | 12 |
| A_original | q1_gpu_ondemand | 21 | 0 | 12 | 0 | 33 |
| C_faq_structured | q1_gpu_ondemand | 20 | 0 | 0 | 0 | 20 |

### mode: rendered_text_v2_n3

| layout | qwen3.5-9b | gpt-oss-20b | gemma4-26b | claude | worst model |
|---|---|---|---|---|---|
| A_original | 100% (n=3) | 50% (n=3) | 100% (n=3) | 100% (n=3) | 50% (gpt-oss-20b) |
| C_faq_structured | 100% (n=3) | 100% (n=3) | 100% (n=3) | 100% (n=3) | 100% (claude) |
| NOPAGE | 0% (n=15) | 3% (n=15) | 0% (n=15) | 20% (n=15) | 0% (gemma4-26b) |

| layout | question | correct | not_found | wrong | invalid | n |
|---|---|---|---|---|---|---|
| NOPAGE | q1_gpu_ondemand | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q2_cpu_sandbox_cost | 0 | 12 | 0 | 0 | 12 |
| NOPAGE | q3_signup | 0 | 11 | 1 | 0 | 12 |
| NOPAGE | q4_billing | 3 | 9 | 0 | 0 | 12 |
| NOPAGE | q5_windows | 0 | 12 | 0 | 0 | 12 |
| A_original | q1_gpu_ondemand | 9 | 0 | 3 | 0 | 12 |
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

Excluded infra errors: {'openai: RateLimitError': 60, 'claude: BrowserRenderError': 2, 'qwen3.5-9b: BrowserRenderError': 3, 'qwen3.5-9b: DaytonaProcessExecutionTimeoutError': 1, 'gemma4-26b: DaytonaProcessExecutionTimeoutError': 1}

### Browser behaviour (rendered_text runs): click vs outcome, per run set × layout × model

**Real browser in Daytona, styled page, q1: on the original tabbed layout A, agents that clicked the On-demand tab were fully correct 21/23, agents that didn't click 0/10; A overall 21/33 correct with 12/33 confident wrong answers, while the explicit layout C was 20/20 correct.**

Each cell is k/n (rate). confident_wrong = a value was asserted and it was wrong.

| run set | layout | model | click | correct | confident_wrong | not_found | invalid | correct given clicked | correct given no click |
|---|---|---|---|---|---|---|---|---|---|
| runs_rendered | A_original | ALL | 8/12 (67%) | 8/12 (67%) | 1/12 (8%) | 3/12 (25%) | 0/12 (0%) | 8/8 (100%) | 0/4 (0%) |
| runs_rendered | A_original | claude | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered | A_original | gemma4-26b | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/0 (–) | 0/3 (0%) |
| runs_rendered | A_original | gpt-oss-20b | 2/3 (67%) | 2/3 (67%) | 1/3 (33%) | 0/3 (0%) | 0/3 (0%) | 2/2 (100%) | 0/1 (0%) |
| runs_rendered | A_original | qwen3.5-9b | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered | C_faq_structured | ALL | 3/12 (25%) | 12/12 (100%) | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 3/3 (100%) | 9/9 (100%) |
| runs_rendered | C_faq_structured | claude | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered | C_faq_structured | gemma4-26b | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered | C_faq_structured | gpt-oss-20b | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered | C_faq_structured | qwen3.5-9b | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered_v2 | A_original | ALL | 9/12 (75%) | 9/12 (75%) | 3/12 (25%) | 0/12 (0%) | 0/12 (0%) | 9/9 (100%) | 0/3 (0%) |
| runs_rendered_v2 | A_original | claude | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered_v2 | A_original | gemma4-26b | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered_v2 | A_original | gpt-oss-20b | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 0/3 (0%) |
| runs_rendered_v2 | A_original | qwen3.5-9b | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered_v2 | C_faq_structured | ALL | 3/12 (25%) | 12/12 (100%) | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 3/3 (100%) | 9/9 (100%) |
| runs_rendered_v2 | C_faq_structured | claude | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered_v2 | C_faq_structured | gemma4-26b | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered_v2 | C_faq_structured | gpt-oss-20b | 0/3 (0%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/0 (–) | 3/3 (100%) |
| runs_rendered_v2 | C_faq_structured | qwen3.5-9b | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 0/0 (–) |
| runs_rendered_v2_n10 | A_original | ALL | 23/33 (70%) | 21/33 (64%) | 12/33 (36%) | 0/33 (0%) | 0/33 (0%) | 21/23 (91%) | 0/10 (0%) |
| runs_rendered_v2_n10 | A_original | claude | 8/8 (100%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) | 0/8 (0%) | 8/8 (100%) | 0/0 (–) |
| runs_rendered_v2_n10 | A_original | gemma4-26b | 9/9 (100%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) | 0/9 (0%) | 9/9 (100%) | 0/0 (–) |
| runs_rendered_v2_n10 | A_original | gpt-oss-20b | 0/10 (0%) | 0/10 (0%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) | 0/0 (–) | 0/10 (0%) |
| runs_rendered_v2_n10 | A_original | qwen3.5-9b | 6/6 (100%) | 4/6 (67%) | 2/6 (33%) | 0/6 (0%) | 0/6 (0%) | 4/6 (67%) | 0/0 (–) |
| runs_rendered_v2_n10 | C_faq_structured | ALL | 5/20 (25%) | 20/20 (100%) | 0/20 (0%) | 0/20 (0%) | 0/20 (0%) | 5/5 (100%) | 15/15 (100%) |
| runs_rendered_v2_n10 | C_faq_structured | claude | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/0 (–) | 5/5 (100%) |
| runs_rendered_v2_n10 | C_faq_structured | gemma4-26b | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/0 (–) | 5/5 (100%) |
| runs_rendered_v2_n10 | C_faq_structured | gpt-oss-20b | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/0 (–) | 5/5 (100%) |
| runs_rendered_v2_n10 | C_faq_structured | qwen3.5-9b | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 0/0 (–) |