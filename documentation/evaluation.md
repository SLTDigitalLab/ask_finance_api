# Evaluations

## Overview

Langsmith traces each llm operation done in the chat API. This traces are stored in the projects section of the LangSmith dashboard. After each trace the evaluations will be done. The evaluation matrices should be setup as follow.

## Set up Evaluation matrices.

1. Select the relevant project

<p align="center">
  <img src="assets/eval_a.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

2. Select Add Rules

<p align="center">
  <img src="assets/eval_b.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

3. Give a relevant name and select `LLM-as-judge-evaluator`

<p align="center">
  <img src="assets/eval_c.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

4. Select the LLM to calculate the metrics. Then select the suggested evaluator prompt.

<p align="center">
  <img src="assets/eval_e.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

5. Set the LLM's API key

<p align="center">
  <img src="assets/eval_d.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

6. Select the relevant metrics

<p align="center">
  <img src="assets/eval_f.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>

7. Set the relevant inputs to the prompt template and continue

<p align="center">
  <img src="assets/eval_g.png" alt= "Development Workflow" width='65%' style="display: block; margin: 0 auto;">
</p>