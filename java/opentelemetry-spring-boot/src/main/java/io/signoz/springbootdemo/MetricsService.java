package io.signoz.springbootdemo;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.metrics.Meter;
import io.opentelemetry.api.metrics.DoubleHistogram;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

@Service
public class MetricsService {
        private DoubleHistogram fibonacciInput;

        @PostConstruct
        public void init() {
                Meter meter = GlobalOpenTelemetry.getMeter("opentelemetry-spring-boot-demo");

                // define a fibonacci input metric to capture business insights
                fibonacciInput = meter
                                .histogramBuilder("app.fibonacci.input")
                                .setDescription("Distribution of requested Fibonacci input numbers")
                                .setUnit("{number}")
                                // Bucket input numbers into discrete, high-dimension buckets
                                .setExplicitBucketBoundariesAdvice(java.util.List.of(
                                                1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0, 89.0))
                                .build();
        }

        public void recordFibonacciInput(int number) {
                fibonacciInput.record(number);
        }
}
