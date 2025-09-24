/**
 * Sprint 6 - Hardware Detection for Onboarding Wizard
 * 
 * Detects CPU/GPU/RAM and suggests configuration profiles for:
 * - Local vLLM vs remote API
 * - Retrieval store recommendations (OpenSearch/Qdrant)
 * - Model size suggestions based on available resources
 */

class HardwareDetector {
    constructor() {
        this.capabilities = {
            cpu: null,
            memory: null,
            gpu: null,
            connection: null,
            platform: null
        };
        
        this.profiles = {
            'high-end': {
                name: 'High Performance',
                description: 'Full local deployment with large models',
                requirements: { memory: 16, cpu: 8 },
                recommendations: {
                    deployment: 'local',
                    models: ['mixtral-8x7b', 'llama2-70b'],
                    retrieval: 'opensearch+qdrant',
                    features: ['full-debate', 'expert-council', 'real-time-analysis']
                }
            },
            'mid-range': {
                name: 'Balanced',
                description: 'Hybrid deployment with medium models',
                requirements: { memory: 8, cpu: 4 },
                recommendations: {
                    deployment: 'hybrid',
                    models: ['llama2-13b', 'mixtral-7b'],
                    retrieval: 'qdrant+cache',
                    features: ['debate', 'basic-analysis', 'export-integrations']
                }
            },
            'low-spec': {
                name: 'Cloud Optimized',
                description: 'Remote API with local caching',
                requirements: { memory: 4, cpu: 2 },
                recommendations: {
                    deployment: 'remote',
                    models: ['gpt-3.5-turbo', 'claude-haiku'],
                    retrieval: 'local-cache',
                    features: ['basic-strategy', 'research-assistance']
                }
            }
        };
    }
    
    async detectHardware() {
        console.log('🔍 Detecting system capabilities...');
        
        // Detect platform
        this.capabilities.platform = this.detectPlatform();
        
        // Detect CPU
        this.capabilities.cpu = await this.detectCPU();
        
        // Detect memory
        this.capabilities.memory = await this.detectMemory();
        
        // Detect GPU (limited in browser)
        this.capabilities.gpu = await this.detectGPU();
        
        // Detect connection
        this.capabilities.connection = await this.detectConnection();
        
        console.log('📊 Hardware capabilities:', this.capabilities);
        
        return this.capabilities;
    }
    
    detectPlatform() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (userAgent.includes('mac')) return 'macOS';
        if (userAgent.includes('win')) return 'Windows';
        if (userAgent.includes('linux')) return 'Linux';
        if (userAgent.includes('android')) return 'Android';
        if (userAgent.includes('iphone') || userAgent.includes('ipad')) return 'iOS';
        
        return 'Unknown';
    }
    
    async detectCPU() {
        // Use navigator.hardwareConcurrency for logical processor count
        const cores = navigator.hardwareConcurrency || 2;
        
        // Estimate performance with a simple benchmark
        const benchmarkStart = performance.now();
        
        // CPU-intensive task for benchmarking
        let sum = 0;
        for (let i = 0; i < 1000000; i++) {
            sum += Math.sqrt(i);
        }
        
        const benchmarkTime = performance.now() - benchmarkStart;
        
        // Rough performance categorization
        let performance_level = 'medium';
        if (benchmarkTime < 50 && cores >= 8) {
            performance_level = 'high';
        } else if (benchmarkTime > 150 || cores <= 2) {
            performance_level = 'low';
        }
        
        return {
            cores,
            performance_level,
            benchmark_time: Math.round(benchmarkTime)
        };
    }
    
    async detectMemory() {
        // Modern browsers support navigator.deviceMemory (approximate)
        const deviceMemory = navigator.deviceMemory || null;
        
        // Estimate available memory for the app (conservative)
        let estimatedAvailable = 2; // Default conservative estimate
        
        if (deviceMemory) {
            // Assume 25% available for the application
            estimatedAvailable = Math.floor(deviceMemory * 0.25);
        }
        
        // Try to detect through memory pressure API if available
        let memoryInfo = null;
        if ('memory' in performance) {
            memoryInfo = performance.memory;
        }
        
        return {
            device_memory_gb: deviceMemory,
            estimated_available_gb: estimatedAvailable,
            memory_info: memoryInfo
        };
    }
    
    async detectGPU() {
        try {
            // WebGL-based GPU detection
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return { available: false, reason: 'WebGL not supported' };
            }
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            let renderer = 'Unknown';
            let vendor = 'Unknown';
            
            if (debugInfo) {
                renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            }
            
            // Simple GPU performance test
            const startTime = performance.now();
            
            // Create a simple shader program for benchmarking
            const vertexShader = gl.createShader(gl.VERTEX_SHADER);
            gl.shaderSource(vertexShader, `
                attribute vec2 position;
                void main() {
                    gl_Position = vec4(position, 0.0, 1.0);
                }
            `);
            gl.compileShader(vertexShader);
            
            const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
            gl.shaderSource(fragmentShader, `
                precision mediump float;
                void main() {
                    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
                }
            `);
            gl.compileShader(fragmentShader);
            
            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);
            
            const renderTime = performance.now() - startTime;
            
            // Clean up
            canvas.remove();
            
            // Categorize GPU capability
            let capability = 'basic';
            if (renderer.toLowerCase().includes('nvidia') || renderer.toLowerCase().includes('radeon')) {
                capability = renderTime < 10 ? 'high' : 'medium';
            }
            
            return {
                available: true,
                renderer,
                vendor,
                capability,
                benchmark_time: Math.round(renderTime)
            };
            
        } catch (error) {
            return {
                available: false,
                reason: error.message
            };
        }
    }
    
    async detectConnection() {
        try {
            // Network Information API
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            
            let speed = 'unknown';
            let type = 'unknown';
            
            if (connection) {
                // Effective connection type: 'slow-2g', '2g', '3g', '4g'
                type = connection.effectiveType || 'unknown';
                
                // Downlink speed in Mbps
                const downlink = connection.downlink || 0;
                
                if (downlink > 10) speed = 'fast';
                else if (downlink > 1.5) speed = 'medium';
                else speed = 'slow';
            }
            
            // Simple latency test
            const latencyStart = performance.now();
            
            try {
                await fetch('/healthz', { method: 'HEAD' });
                const latency = performance.now() - latencyStart;
                
                return {
                    type,
                    speed,
                    latency: Math.round(latency),
                    downlink: connection?.downlink || null,
                    save_data: connection?.saveData || false
                };
            } catch {
                return {
                    type,
                    speed: 'offline',
                    latency: null,
                    downlink: connection?.downlink || null,
                    save_data: connection?.saveData || false
                };
            }
            
        } catch (error) {
            return {
                type: 'unknown',
                speed: 'unknown',
                latency: null,
                error: error.message
            };
        }
    }
    
    recommendProfile() {
        const { cpu, memory, gpu, connection } = this.capabilities;
        
        let score = 0;
        let reasoning = [];
        
        // CPU scoring
        if (cpu?.cores >= 8 && cpu?.performance_level === 'high') {
            score += 40;
            reasoning.push('High-performance CPU detected');
        } else if (cpu?.cores >= 4) {
            score += 20;
            reasoning.push('Mid-range CPU suitable for hybrid deployment');
        } else {
            reasoning.push('Limited CPU - cloud deployment recommended');
        }
        
        // Memory scoring
        if (memory?.estimated_available_gb >= 8) {
            score += 30;
            reasoning.push('Sufficient memory for local models');
        } else if (memory?.estimated_available_gb >= 4) {
            score += 15;
            reasoning.push('Moderate memory - medium models possible');
        } else {
            reasoning.push('Limited memory - remote API recommended');
        }
        
        // GPU scoring (bonus)
        if (gpu?.available && gpu?.capability === 'high') {
            score += 20;
            reasoning.push('Dedicated GPU can accelerate inference');
        } else if (gpu?.available) {
            score += 10;
            reasoning.push('Basic GPU support available');
        }
        
        // Connection adjustment
        if (connection?.speed === 'slow' || connection?.save_data) {
            score -= 10;
            reasoning.push('Network constraints favor local deployment');
        } else if (connection?.speed === 'fast') {
            reasoning.push('Good network enables hybrid options');
        }
        
        // Determine profile
        let recommendedProfile = 'low-spec';
        if (score >= 70) {
            recommendedProfile = 'high-end';
        } else if (score >= 40) {
            recommendedProfile = 'mid-range';
        }
        
        return {
            profile: recommendedProfile,
            score,
            reasoning,
            details: this.profiles[recommendedProfile]
        };
    }
    
    generateConfigSuggestions() {
        const recommendation = this.recommendProfile();
        const profile = recommendation.details;
        
        const config = {
            // Model configuration
            models: {
                completion: profile.recommendations.models,
                embedding: profile.recommendations.deployment === 'local' 
                    ? ['all-minilm-l6-v2', 'bge-large'] 
                    : ['text-embedding-3-small'],
                rerank: profile.recommendations.deployment === 'local'
                    ? ['bge-reranker-large']
                    : ['cohere-rerank-english-v3.0']
            },
            
            // Deployment configuration
            deployment: {
                mode: profile.recommendations.deployment,
                retrieval_backend: profile.recommendations.retrieval,
                enable_local_cache: true,
                max_concurrent_requests: recommendation.score >= 50 ? 4 : 2
            },
            
            // Feature flags based on capabilities
            features: {
                enable_debate: profile.recommendations.features.includes('debate') || profile.recommendations.features.includes('full-debate'),
                enable_expert_council: profile.recommendations.features.includes('expert-council'),
                enable_real_time_analysis: profile.recommendations.features.includes('real-time-analysis'),
                enable_export_integrations: profile.recommendations.features.includes('export-integrations'),
                max_document_size_mb: recommendation.score >= 50 ? 50 : 10,
                enable_batch_processing: recommendation.score >= 40
            },
            
            // Performance tuning
            performance: {
                max_tokens_per_request: recommendation.score >= 70 ? 4096 : recommendation.score >= 40 ? 2048 : 1024,
                request_timeout_seconds: 300,
                enable_streaming: true,
                cache_ttl_hours: 24
            }
        };
        
        return {
            recommendation,
            config,
            setup_instructions: this.generateSetupInstructions(recommendation.profile)
        };
    }
    
    generateSetupInstructions(profileName) {
        const instructions = {
            'high-end': [
                '1. Install Docker Desktop for local model serving',
                '2. Allocate 8GB+ RAM to Docker containers',
                '3. Download recommended models: mixtral-8x7b, llama2-70b',
                '4. Enable GPU acceleration if available',
                '5. Configure OpenSearch + Qdrant for retrieval',
                '6. Set up local vLLM serving with model rotation'
            ],
            'mid-range': [
                '1. Install Docker Desktop with 4GB+ RAM allocation',
                '2. Configure hybrid deployment (local + remote)',
                '3. Download medium models: llama2-13b, mixtral-7b',
                '4. Set up Qdrant with local caching',
                '5. Enable selective feature flags',
                '6. Configure API rate limiting for remote calls'
            ],
            'low-spec': [
                '1. Configure remote API keys (OpenAI, Anthropic)',
                '2. Set up local caching for frequently used data',
                '3. Enable data-saving mode',
                '4. Use lightweight embedding models',
                '5. Configure request batching and queuing',
                '6. Enable offline mode for basic operations'
            ]
        };
        
        return instructions[profileName] || instructions['low-spec'];
    }
}

// Export for use in onboarding wizard
window.HardwareDetector = HardwareDetector;

// Usage example:
async function runHardwareDetection() {
    const detector = new HardwareDetector();
    
    try {
        const capabilities = await detector.detectHardware();
        const suggestions = detector.generateConfigSuggestions();
        
        console.log('🚀 Configuration Suggestions:', suggestions);
        
        return suggestions;
        
    } catch (error) {
        console.error('❌ Hardware detection failed:', error);
        
        // Fallback to conservative configuration
        return {
            recommendation: {
                profile: 'low-spec',
                reasoning: ['Hardware detection failed - using safe defaults']
            },
            config: {
                deployment: { 
                    mode: 'remote',
                    retrieval_backend: 'local-cache'
                },
                features: {
                    enable_debate: false,
                    max_document_size_mb: 5
                }
            }
        };
    }
}

// Auto-run on page load for demo
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔧 StratMaster Hardware Detection Ready');
        
        // Add to window for interactive use
        window.runHardwareDetection = runHardwareDetection;
    });
}