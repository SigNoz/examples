package io.signoz.springbootdemo;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.metrics.DoubleHistogram;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

/**
 * Optional custom business metrics via the OTel API directly.
 *
 * The Java Agent auto-instruments Spring MVC and provides
 * http.server.request.duration
 * and may provide http.server.active_requests metrics automatically depending
 * on
 * the active instrumentation setup. This service keeps an example
 * application-level metric implementation available in the codebase without
 * recording it by default.
 *
 * GlobalOpenTelemetry is populated by the agent at startup before any Spring
 * beans are created,
 * so it is safe to call here.
 */
@Service
public class MetricsService {
        private static final AttributeKey<Long> HTTP_RESPONSE_STATUS_CODE = AttributeKey
                        .longKey("http.response.status_code");

        private DoubleHistogram requestDuration;

        @PostConstruct
        public void init() {
                Meter meter = GlobalOpenTelemetry.getMeter("opentelemetry-spring-boot-demo");

                requestDuration = meter
                                .histogramBuilder("app.fibonacci.duration")
                                .setDescription("Duration of fibonacci computation including simulated delay (seconds)")
                                .setUnit("s")
                                // OTel-recommended HTTP latency bucket boundaries (in seconds).
                                // Without these, requests without huge interval gaps collapse into the same
                                // bucket, and make p95/p99 meaningless
                                .setExplicitBucketBoundariesAdvice(java.util.List.of(
                                                0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0,
                                                7.5, 10.0))
                                .build();
        }

        public void recordFibonacciDuration(double seconds, String method, String path, int statusCode) {
                requestDuration.record(seconds, Attributes.of(
                                HTTP_RESPONSE_STATUS_CODE, (long) statusCode));
        }
}
