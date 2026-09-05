import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    steady_api: {
      executor: "constant-vus",
      vus: Number(__ENV.SLO_VUS || 10),
      duration: __ENV.SLO_DURATION || "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.005"],
    http_req_duration: ["p(95)<500"],
    checks: ["rate>0.995"],
  },
};

const baseUrl = (__ENV.BASE_URL || "http://127.0.0.1:8001").replace(/\/$/, "");
const requestOptions = __ENV.HOST_HEADER
  ? { headers: { Host: __ENV.HOST_HEADER } }
  : {};

export default function () {
  const health = http.get(`${baseUrl}/health`, {
    ...requestOptions,
    tags: { endpoint: "health" },
  });
  check(health, { "health is 200": (response) => response.status === 200 });

  const ready = http.get(`${baseUrl}/ready`, {
    ...requestOptions,
    tags: { endpoint: "ready" },
  });
  check(ready, { "ready is 200": (response) => response.status === 200 });
  sleep(0.2);
}
