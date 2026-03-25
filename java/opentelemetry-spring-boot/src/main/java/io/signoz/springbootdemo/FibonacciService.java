package io.signoz.springbootdemo;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class FibonacciService {
    private static final Logger log = LoggerFactory.getLogger(FibonacciService.class);

    private final MetricsService metricsService;

    // inject the metricsService to be used within the computation function
    public FibonacciService(MetricsService metricsService) {
        this.metricsService = metricsService;
    }

    // create a child span for the computation function. this helps capture context
    // around the processing logic, plus helps measure the time taken for the actual
    // computation logic
    @WithSpan("fibonacci.compute")
    public long compute(@SpanAttribute("fibonacci.number") int n) {
        if (n < 0 || n > 92) {
            // n > 92 overflows a signed long
            throw new IllegalArgumentException(
                    "number must be between 0 and 92, got: " + n);
        }

        metricsService.recordFibonacciInput(n);
        long result = fib(n);
        // manually set a span attribute for the result
        Span.current().setAttribute("fibonacci.result", result);
        log.debug("fibonacci({}) = {}", n, result);
        return result;
    }

    private long fib(int n) {
        if (n <= 1) {
            return n;
        }

        long previous = 0;
        long current = 1;
        for (int i = 2; i <= n; i++) {
            long next = previous + current;
            previous = current;
            current = next;
        }
        return current;
    }
}
