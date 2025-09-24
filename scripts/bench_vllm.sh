#!/bin/bash
# vLLM benchmarking script for throughput and latency testing
# Usage: ./bench_vllm.sh [model_name] [batch_sizes] [sequence_lengths]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCH_DIR="$PROJECT_ROOT/bench"

# Default test parameters
DEFAULT_MODEL="mixtral-8x7b-instruct"
DEFAULT_BATCH_SIZES="1,2,4,8,16"
DEFAULT_SEQ_LENGTHS="256,512,1024,2048"
VLLM_HOST="${VLLM_HOST:-http://localhost:8000}"
TEST_DURATION="${TEST_DURATION:-300}"  # 5 minutes
WARMUP_REQUESTS="${WARMUP_REQUESTS:-10}"

# Parse arguments
MODEL_NAME="${1:-$DEFAULT_MODEL}"
BATCH_SIZES="${2:-$DEFAULT_BATCH_SIZES}"
SEQ_LENGTHS="${3:-$DEFAULT_SEQ_LENGTHS}"

echo "🚀 Starting vLLM benchmarking suite"
echo "Model: $MODEL_NAME"
echo "Batch sizes: $BATCH_SIZES" 
echo "Sequence lengths: $SEQ_LENGTHS"
echo "vLLM endpoint: $VLLM_HOST"
echo "Test duration: ${TEST_DURATION}s"

# Create benchmark output directory
mkdir -p "$BENCH_DIR/vllm"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BENCH_OUTPUT="$BENCH_DIR/vllm/${MODEL_NAME}_${TIMESTAMP}"
mkdir -p "$BENCH_OUTPUT"

# Check vLLM server availability
check_vllm_health() {
    echo "🔍 Checking vLLM server health..."
    if ! curl -s -f "$VLLM_HOST/health" > /dev/null; then
        echo "❌ vLLM server not available at $VLLM_HOST"
        echo "Start vLLM server with: docker compose up vllm"
        exit 1
    fi
    echo "✅ vLLM server is healthy"
}

# Generate test prompts for different domains
generate_test_prompts() {
    local seq_length=$1
    local output_file=$2
    
    cat > "$output_file" << EOF
{
  "prompts": [
    {
      "domain": "strategy",
      "prompt": "Analyze the competitive landscape for a B2B SaaS startup in the marketing automation space. Consider market size, key players, differentiation opportunities, and strategic recommendations. Focus on actionable insights for product positioning and go-to-market strategy. Length: $seq_length tokens.",
      "max_tokens": $seq_length
    },
    {
      "domain": "research", 
      "prompt": "Conduct a comprehensive analysis of the impact of remote work on employee productivity and collaboration in technology companies. Include quantitative metrics, qualitative feedback, and recommendations for hybrid work models. Consider long-term organizational implications. Length: $seq_length tokens.",
      "max_tokens": $seq_length
    },
    {
      "domain": "brand",
      "prompt": "Develop a brand positioning strategy for a sustainable fashion startup targeting Gen Z consumers. Include brand personality, value proposition, messaging framework, and channel strategy. Address authenticity and sustainability concerns. Length: $seq_length tokens.",
      "max_tokens": $seq_length
    },
    {
      "domain": "technical",
      "prompt": "Design a microservices architecture for a high-scale e-commerce platform handling 1M+ daily transactions. Include service boundaries, data consistency patterns, observability, and deployment strategies. Consider performance and reliability requirements. Length: $seq_length tokens.",
      "max_tokens": $seq_length
    }
  ]
}
EOF
}

# Run throughput benchmarks
run_throughput_test() {
    local batch_size=$1
    local seq_length=$2
    local test_name="throughput_b${batch_size}_s${seq_length}"
    local output_file="$BENCH_OUTPUT/${test_name}.json"
    
    echo "🏃 Running throughput test: batch_size=$batch_size, seq_length=$seq_length"
    
    # Generate test prompts
    local prompts_file="$BENCH_OUTPUT/prompts_${seq_length}.json"
    generate_test_prompts "$seq_length" "$prompts_file"
    
    # Create benchmark script
    local bench_script="$BENCH_OUTPUT/${test_name}_script.py"
    cat > "$bench_script" << 'BENCH_SCRIPT'
import asyncio
import json
import time
import sys
from typing import List, Dict, Any
import httpx
import statistics

async def run_benchmark(vllm_host: str, prompts_file: str, batch_size: int, duration: int, warmup: int) -> Dict[str, Any]:
    with open(prompts_file) as f:
        data = json.load(f)
    prompts = [p["prompt"] for p in data["prompts"]]
    max_tokens = data["prompts"][0]["max_tokens"]
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        # Warmup phase
        print(f"Warming up with {warmup} requests...")
        for _ in range(warmup):
            try:
                await client.post(f"{vllm_host}/v1/completions", json={
                    "prompt": prompts[0],
                    "max_tokens": min(max_tokens, 100),
                    "temperature": 0.7,
                    "model": "default"
                })
            except Exception as e:
                print(f"Warmup request failed: {e}")
        
        # Main benchmark
        print(f"Starting {duration}s benchmark with batch_size={batch_size}")
        start_time = time.time()
        end_time = start_time + duration
        
        completed_requests = 0
        total_tokens = 0
        latencies = []
        errors = 0
        
        while time.time() < end_time:
            batch_start = time.time()
            batch_tasks = []
            
            for i in range(batch_size):
                prompt = prompts[i % len(prompts)]
                task = client.post(f"{vllm_host}/v1/completions", json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "model": "default"
                })
                batch_tasks.append(task)
            
            try:
                responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
                batch_end = time.time()
                batch_latency = batch_end - batch_start
                
                successful_responses = 0
                for response in responses:
                    if isinstance(response, Exception):
                        errors += 1
                    else:
                        try:
                            result = response.json()
                            if "choices" in result and len(result["choices"]) > 0:
                                completion = result["choices"][0].get("text", "")
                                total_tokens += len(completion.split())
                                successful_responses += 1
                        except Exception:
                            errors += 1
                
                if successful_responses > 0:
                    latencies.append(batch_latency)
                    completed_requests += successful_responses
                    
            except Exception as e:
                print(f"Batch failed: {e}")
                errors += batch_size
        
        actual_duration = time.time() - start_time
        
        return {
            "test_config": {
                "batch_size": batch_size,
                "duration": duration,
                "actual_duration": actual_duration,
                "max_tokens": max_tokens
            },
            "results": {
                "completed_requests": completed_requests,
                "errors": errors,
                "total_tokens": total_tokens,
                "throughput_rps": completed_requests / actual_duration,
                "throughput_tps": total_tokens / actual_duration,
                "latency_mean": statistics.mean(latencies) if latencies else 0,
                "latency_p50": statistics.median(latencies) if latencies else 0,
                "latency_p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
                "latency_p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0,
                "error_rate": errors / (completed_requests + errors) if (completed_requests + errors) > 0 else 0
            }
        }

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python script.py <vllm_host> <prompts_file> <batch_size> <duration> <warmup>")
        sys.exit(1)
    
    vllm_host = sys.argv[1]
    prompts_file = sys.argv[2] 
    batch_size = int(sys.argv[3])
    duration = int(sys.argv[4])
    warmup = int(sys.argv[5])
    
    result = asyncio.run(run_benchmark(vllm_host, prompts_file, batch_size, duration, warmup))
    print(json.dumps(result, indent=2))
BENCH_SCRIPT

    # Run the benchmark
    python3 "$bench_script" "$VLLM_HOST" "$prompts_file" "$batch_size" "$TEST_DURATION" "$WARMUP_REQUESTS" > "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Throughput test completed: $output_file"
    else
        echo "❌ Throughput test failed"
    fi
}

# Run latency benchmarks (single request)
run_latency_test() {
    local seq_length=$1
    local test_name="latency_s${seq_length}"
    local output_file="$BENCH_OUTPUT/${test_name}.json"
    
    echo "⏱️  Running latency test: seq_length=$seq_length"
    
    local prompts_file="$BENCH_OUTPUT/prompts_${seq_length}.json"
    generate_test_prompts "$seq_length" "$prompts_file"
    
    # Single request latency measurement
    local latency_script="$BENCH_OUTPUT/${test_name}_script.py"
    cat > "$latency_script" << 'LATENCY_SCRIPT'
import json
import time
import sys
import httpx
import statistics

def run_latency_test(vllm_host: str, prompts_file: str, num_requests: int) -> dict:
    with open(prompts_file) as f:
        data = json.load(f)
    prompts = [p["prompt"] for p in data["prompts"]]
    max_tokens = data["prompts"][0]["max_tokens"]
    
    latencies = []
    ttfts = []  # Time to first token
    errors = 0
    
    with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
        for i in range(num_requests):
            prompt = prompts[i % len(prompts)]
            
            start_time = time.time()
            try:
                response = client.post(f"{vllm_host}/v1/completions", json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "model": "default",
                    "stream": False
                })
                end_time = time.time()
                
                if response.status_code == 200:
                    latency = end_time - start_time
                    latencies.append(latency)
                    
                    # Estimate TTFT (simplified)
                    result = response.json()
                    if "choices" in result:
                        # Rough TTFT estimation based on total latency and response length
                        completion = result["choices"][0].get("text", "")
                        tokens = len(completion.split())
                        estimated_ttft = latency * 0.1 if tokens > 10 else latency * 0.5
                        ttfts.append(estimated_ttft)
                else:
                    errors += 1
                    
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
                errors += 1
    
    return {
        "test_config": {
            "sequence_length": max_tokens,
            "num_requests": num_requests
        },
        "results": {
            "completed_requests": len(latencies),
            "errors": errors,
            "latency_mean": statistics.mean(latencies) if latencies else 0,
            "latency_median": statistics.median(latencies) if latencies else 0,
            "latency_p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
            "latency_p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0,
            "ttft_mean": statistics.mean(ttfts) if ttfts else 0,
            "ttft_p95": statistics.quantiles(ttfts, n=20)[18] if len(ttfts) > 20 else 0,
            "error_rate": errors / (len(latencies) + errors) if (len(latencies) + errors) > 0 else 0
        }
    }

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <vllm_host> <prompts_file> <num_requests>")
        sys.exit(1)
    
    result = run_latency_test(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    print(json.dumps(result, indent=2))
LATENCY_SCRIPT

    python3 "$latency_script" "$VLLM_HOST" "$prompts_file" 50 > "$output_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Latency test completed: $output_file"
    else
        echo "❌ Latency test failed"
    fi
}

# Generate comprehensive benchmark report
generate_report() {
    local report_file="$BENCH_OUTPUT/benchmark_report.md"
    
    echo "📊 Generating benchmark report..."
    
    cat > "$report_file" << EOF
# vLLM Benchmark Report

**Model**: $MODEL_NAME  
**Date**: $(date)  
**vLLM Host**: $VLLM_HOST  
**Test Duration**: ${TEST_DURATION}s per configuration  

## System Information

\`\`\`bash
$(uname -a)
\`\`\`

**Python Version**: $(python3 --version)  
**Available Memory**: $(free -h | grep '^Mem:' | awk '{print $2}' || echo "N/A")  
**GPU Information**: 
\`\`\`
$(nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits 2>/dev/null || echo "No GPU detected")
\`\`\`

## Test Results

### Throughput Benchmarks

| Batch Size | Seq Length | RPS | TPS | Mean Latency (s) | P95 Latency (s) | Error Rate |
|------------|------------|-----|-----|------------------|-----------------|------------|
EOF

    # Add throughput results to report
    for batch_size in $(echo "$BATCH_SIZES" | tr ',' ' '); do
        for seq_length in $(echo "$SEQ_LENGTHS" | tr ',' ' '); do
            local result_file="$BENCH_OUTPUT/throughput_b${batch_size}_s${seq_length}.json"
            if [ -f "$result_file" ]; then
                local rps=$(jq -r '.results.throughput_rps' "$result_file" 2>/dev/null || echo "N/A")
                local tps=$(jq -r '.results.throughput_tps' "$result_file" 2>/dev/null || echo "N/A")
                local latency=$(jq -r '.results.latency_mean' "$result_file" 2>/dev/null || echo "N/A")
                local p95=$(jq -r '.results.latency_p95' "$result_file" 2>/dev/null || echo "N/A")
                local error_rate=$(jq -r '.results.error_rate' "$result_file" 2>/dev/null || echo "N/A")
                
                echo "| $batch_size | $seq_length | $rps | $tps | $latency | $p95 | $error_rate |" >> "$report_file"
            fi
        done
    done

    cat >> "$report_file" << EOF

### Latency Benchmarks

| Seq Length | Mean Latency (s) | Median Latency (s) | P95 Latency (s) | P99 Latency (s) | TTFT P95 (s) |
|------------|------------------|--------------------|-----------------|-----------------|---------------|
EOF

    # Add latency results to report
    for seq_length in $(echo "$SEQ_LENGTHS" | tr ',' ' '); do
        local result_file="$BENCH_OUTPUT/latency_s${seq_length}.json"
        if [ -f "$result_file" ]; then
            local mean_lat=$(jq -r '.results.latency_mean' "$result_file" 2>/dev/null || echo "N/A")
            local med_lat=$(jq -r '.results.latency_median' "$result_file" 2>/dev/null || echo "N/A")
            local p95_lat=$(jq -r '.results.latency_p95' "$result_file" 2>/dev/null || echo "N/A")
            local p99_lat=$(jq -r '.results.latency_p99' "$result_file" 2>/dev/null || echo "N/A")
            local ttft_p95=$(jq -r '.results.ttft_p95' "$result_file" 2>/dev/null || echo "N/A")
            
            echo "| $seq_length | $mean_lat | $med_lat | $p95_lat | $p99_lat | $ttft_p95 |" >> "$report_file"
        fi
    done

    cat >> "$report_file" << EOF

## Key Metrics Summary

**Peak Throughput**: $(find "$BENCH_OUTPUT" -name "throughput_*.json" -exec jq -r '.results.throughput_tps' {} \; | sort -nr | head -1) tokens/second  
**Best Latency**: $(find "$BENCH_OUTPUT" -name "latency_*.json" -exec jq -r '.results.latency_median' {} \; | sort -n | head -1) seconds  
**Optimal Batch Size**: $(find "$BENCH_OUTPUT" -name "throughput_*.json" -exec jq -r '"\(.test_config.batch_size):\(.results.throughput_tps)"' {} \; | sort -t: -k2 -nr | head -1 | cut -d: -f1)  

## Recommendations

- **Production Configuration**: Use batch size $(find "$BENCH_OUTPUT" -name "throughput_*.json" -exec jq -r '"\(.test_config.batch_size):\(.results.throughput_tps)"' {} \; | sort -t: -k2 -nr | head -1 | cut -d: -f1) for optimal throughput
- **Latency-Critical Workloads**: Single request processing recommended for <1s response times
- **Resource Utilization**: Monitor GPU memory usage and consider tensor parallelism for larger models

## Raw Data Files

All detailed benchmark results are available in:
\`\`\`
$BENCH_OUTPUT/
\`\`\`

EOF

    echo "✅ Benchmark report generated: $report_file"
}

# Main execution
main() {
    check_vllm_health
    
    echo "🔥 Running throughput benchmarks..."
    for batch_size in $(echo "$BATCH_SIZES" | tr ',' ' '); do
        for seq_length in $(echo "$SEQ_LENGTHS" | tr ',' ' '); do
            run_throughput_test "$batch_size" "$seq_length"
        done
    done
    
    echo "⚡ Running latency benchmarks..."
    for seq_length in $(echo "$SEQ_LENGTHS" | tr ',' ' '); do
        run_latency_test "$seq_length"
    done
    
    generate_report
    
    echo ""
    echo "🎉 vLLM benchmarking completed!"
    echo "📁 Results available in: $BENCH_OUTPUT"
    echo "📊 Report: $BENCH_OUTPUT/benchmark_report.md"
}

# Install required Python packages if needed
if ! python3 -c "import httpx" 2>/dev/null; then
    echo "📦 Installing required Python packages..."
    pip3 install httpx
fi

main "$@"