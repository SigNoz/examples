package io.signoz.springbootdemo;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.metrics.DoubleHistogram;
import io.opentelemetry.api.metrics.LongUpDownCounter;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

/**
 * Optional custom business metrics via the OTel API directly.
 *
 * The Java Agent auto-instruments Spring MVC and provides
 * http.server.request.duration
 * and may provide http.server.active_requests metrics automatically depending on
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
        private static final AttributeKey<String> HTTP_REQUEST_METHOD = AttributeKey.stringKey("http.request.method");
        private static final AttributeKey<String> URL_PATH = AttributeKey.stringKey("url.path");

        private DoubleHistogram requestDuration;
        private LongUpDownCounter activeRequests;

        @PostConstruct
        public void init() {
                Meter meter = GlobalOpenTelemetry.getMeter("opentelemetry-spring-boot-demo");

                // Example application-level latency metric retained for reference.
                requestDuration = meter
                                .histogramBuilder("app.fibonacci.duration")
                                .setDescription("Duration of fibonacci computation including simulated delay (seconds)")
                                .setUnit("s")
                                // OTel-recommended HTTP latency bucket boundaries (in seconds).
                                // Without these, all sub-second requests collapse into a single default [0, 5)
                                // bucket,
                                // making P95/P99 meaningless.
                                .setExplicitBucketBoundariesAdvice(java.util.List.of(
                                                0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0,
                                                7.5, 10.0))
                                .build();

                activeRequests = meter.upDownCounterBuilder("http.server.active_requests")
                                .setDescription("Number of active HTTP server requests")
                                .setUnit("1")
                                .build();
        }

        public void recordFibonacciDuration(double seconds, int number) {
                requestDuration.record(seconds, Attributes.of(
                                AttributeKey.longKey("fibonacci.number"), (long) number));
        }

        public void incrementActiveRequests(String method, String path) {
                activeRequests.add(1, Attributes.of(
                                HTTP_REQUEST_METHOD, method,
                                URL_PATH, path));
        }

        public void decrementActiveRequests(String method, String path) {
                activeRequests.add(-1, Attributes.of(
                                HTTP_REQUEST_METHOD, method,
                                URL_PATH, path));
        }
}
