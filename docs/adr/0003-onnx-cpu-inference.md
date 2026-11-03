# ADR 0003: ONNX Runtime CPU Inference Engine for Server Serving

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Lebogang Masia, Antigravity AI Pair

## Context and Problem Statement
Machine learning models (Title Expander, Semantic Evaluator, and Application Tailor) must run locally on the user's host laptop (Intel Core i5-1235U, 7.4 GiB RAM) without a dedicated NVIDIA GPU. The inference engine must adhere to strict memory budgets (<= 1.0 GiB RAM) and low latencies (< 50ms for semantic scoring).

## Decision Drivers
- High CPU throughput without CUDA dependencies.
- Quantization support (INT8) to reduce model size and memory footprints.
- Memory isolation and explicit lifecycle management.

## Considered Options
1. PyTorch Default CPU Engine: Easy export, but large memory overhead (~1.5–2.0x model size) and higher CPU latency on complex graphs.
2. ONNX Runtime (CPUExecutionProvider): Native graph optimization, INT8 quantization, minimal memory overhead, and high multi-threaded CPU throughput.
3. Hosted Inference APIs (e.g. OpenAI / Hugging Face Inference): Strictly prohibited by project invariants for Milestones 1–3.

## Decision Outcome
Chosen option: **ONNX Runtime (CPUExecutionProvider) with INT8 Quantization**.
- Models exported from Kaggle as optimized ONNX graphs or `.safetensors`.
- Thread execution capped at 4 threads to prevent operating system freezes.
