package io.signoz.springbootdemo;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.LongUpDownCounter;
import io.opentelemetry.api.metrics.Meter;
import jakarta.annotation.PostConstruct;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

@Service
@ConditionalOnProperty(
        name = "demo.metrics.manual-http-server-active-requests.enabled",
        havingValue = "true")
public class ManualHttpServerActiveRequestsMetrics {
    private static final AttributeKey<String> HTTP_REQUEST_METHOD = AttributeKey.stringKey("http.request.method");
    private static final AttributeKey<String> URL_PATH = AttributeKey.stringKey("url.path");

    private LongUpDownCounter activeRequests;

    @PostConstruct
    public void init() {
        Meter meter = GlobalOpenTelemetry.getMeter("opentelemetry-spring-boot-demo");
        activeRequests = meter.upDownCounterBuilder("http.server.active_requests")
                .setDescription("Number of active HTTP server requests")
                .setUnit("1")
                .build();
    }

    public void increment(String method, String path) {
        activeRequests.add(1, Attributes.of(
                HTTP_REQUEST_METHOD, method,
                URL_PATH, path));
    }

    public void decrement(String method, String path) {
        activeRequests.add(-1, Attributes.of(
                HTTP_REQUEST_METHOD, method,
                URL_PATH, path));
    }
}
