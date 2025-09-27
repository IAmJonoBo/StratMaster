import http from 'k6/http';
import { check, group, sleep, Trend } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.4/index.js';

/**
 * StratMaster Phase 5 load test baseline (SCRATCH.md).
 *
 * Provides a configurable smoke profile that exercises the public API
 * endpoints used by the research→reason→decide pipeline. The script focuses
 * on RED metrics (rate, errors, duration) and records latency trends so they
 * can be published into Grafana or compared between local/remote runs.
 */

const apiBase = __ENV.API_BASE || 'http://localhost:8000';
const authToken = __ENV.API_TOKEN || ''; // optional bearer token
const pauseSeconds = Number(__ENV.PAUSE_SECONDS || 1);

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '1m',
  thresholds: {
    http_req_duration: [
      'p(50)<300', // keep p50 under 300ms
      'p(95)<1200', // align with SCRATCH quality gate for long-tail
    ],
    http_req_failed: ['rate<0.01'],
  },
};

const debateLatency = new Trend('stratmaster_debate_latency', true);
const retrievalLatency = new Trend('stratmaster_retrieval_latency', true);
const recommendationLatency = new Trend('stratmaster_recommend_latency', true);

function request(path, payload) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  if (authToken) {
    params.headers.Authorization = `Bearer ${authToken}`;
  }

  const res = http.post(`${apiBase}${path}`, JSON.stringify(payload), params);
  check(res, {
    [`${path} status 2xx`]: (r) => r.status >= 200 && r.status < 300,
  });
  return res;
}

export default function () {
  group('router/model recommendation', () => {
    const body = {
      task_type: 'reasoning',
      prompt: 'Provide an analysis of quarterly revenue trends.',
      context_tokens: 2048,
    };
    const res = request('/tools/models/recommend', body);
    recommendationLatency.add(res.timings.duration);
  });

  group('retrieval/hybrid', () => {
    const body = {
      query: 'What were the key marketing initiatives in Q4?',
      workspace: 'benchmark',
      top_k: 5,
      rerank: true,
    };
    const res = request('/retrieval/hybrid', body);
    retrievalLatency.add(res.timings.duration);
  });

  group('debate/learning', () => {
    const body = {
      topic: 'Launch strategy for eco-friendly product line',
      positions: ['aggressive-growth', 'risk-mitigated'],
      rounds: 2,
    };
    const res = request('/debate/learning/predict', body);
    debateLatency.add(res.timings.duration);
  });

  sleep(pauseSeconds);
}

export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
    'k6-smoke-summary.json': JSON.stringify({
      metadata: {
        apiBase,
        generatedAt: new Date().toISOString(),
        vus: options.vus,
        duration: options.duration,
      },
      thresholds: data.thresholds,
      metrics: {
        debate: debateLatency.stats,
        retrieval: retrievalLatency.stats,
        recommendation: recommendationLatency.stats,
      },
    }, null, 2),
  };
}
