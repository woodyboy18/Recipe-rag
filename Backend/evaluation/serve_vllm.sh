#!/bin/bash
# ==============================================================================
# vLLM Model Serving Script for College Server (2 x NVIDIA A100 80GB)
# ==============================================================================

set -e

MODEL_TYPE=${1:-"llama3"}

echo "=================================================================="
echo "Starting vLLM Inference Server for LLM-as-a-Judge Evaluation"
echo "Target Model: $MODEL_TYPE"
echo "=================================================================="

# Check NVIDIA GPU setup
nvidia-smi

if [ "$MODEL_TYPE" == "llama3" ]; then
    echo "Serving Meta Llama 3 70B Instruct across 2 x A100 (TP=2, BF16)..."
    vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
        --tensor-parallel-size 2 \
        --dtype bfloat16 \
        --port 8000 \
        --max-model-len 8192 \
        --gpu-memory-utilization 0.90 \
        --trust-remote-code
elif [ "$MODEL_TYPE" == "gemma" ]; then
    echo "Serving Google Gemma 2 27B IT (BF16)..."
    vllm serve google/gemma-2-27b-it \
        --tensor-parallel-size 1 \
        --dtype bfloat16 \
        --port 8000 \
        --max-model-len 8192 \
        --gpu-memory-utilization 0.90 \
        --trust-remote-code
else
    echo "Unknown model type: $MODEL_TYPE. Choose 'llama3' or 'gemma'."
    exit 1
fi
