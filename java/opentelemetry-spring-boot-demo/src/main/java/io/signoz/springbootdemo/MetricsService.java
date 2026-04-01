package io.signoz.springbootdemo;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.metrics.LongCounter;
import io.opentelemetry.api.metrics.Meter;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

@Service
public class MetricsService {
        private static final AttributeKey<String> FIBONACCI_RESULT_BAND = AttributeKey
                        .stringKey("fibonacci.result.band");

        private LongCounter fibonacciCalculations;

        @PostConstruct
        public void init() {
                Meter meter = GlobalOpenTelemetry.getMeter("opentelemetry-spring-boot-demo");

                fibonacciCalculations = meter
                                .counterBuilder("app.fibonacci.calculations")
                                .setDescription("Count of successful Fibonacci calculations by result band")
                                .setUnit("1")
                                .build();
        }

        public void recordFibonacciCalculation(long result) {
                fibonacciCalculations.add(1, Attributes.of(
                                FIBONACCI_RESULT_BAND, toResultBand(result)));
        }

        private String toResultBand(long result) {
                if (result < 10) {
                        return "single_digit";
                }
                if (result < 100) {
                        return "double_digit";
                }
                if (result < 1_000_000) {
                        return "medium";
                }
                if (result < 1_000_000_000_000L) {
                        return "large";
                }
                return "huge";
        }
}
