package io.signoz.springbootdemo;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Fibonacci computation service.
 *
 * @WithSpan creates a child span automatically (via the agent's annotation
 *           instrumentation).
 * @SpanAttribute maps the method parameter to a span attribute without any
 *                manual code.
 *                Additional result attributes are set manually via
 *                Span.current().
 */
@Service
public class FibonacciService {
    private static final Logger log = LoggerFactory.getLogger(FibonacciService.class);

    /**
     * Computes the Nth Fibonacci number.
     *
     * The span created by @WithSpan will appear as a child of the HTTP server span,
     * giving a clear visual breakdown in the trace waterfall.
     */
    @WithSpan("fibonacci.compute")
    public long compute(@SpanAttribute("fibonacci.number") int n) {
        if (n < 0 || n > 92) {
            // n > 92 overflows a signed long
            throw new IllegalArgumentException(
                    "number must be between 0 and 92, got: " + n);
        }
        long result = fib(n);
        // Set result as a span attribute — @SpanAttribute only covers input params
        Span.current().setAttribute("fibonacci.result", result);
        log.debug("fibonacci({}) = {}", n, result);
        return result;
    }

    private long fib(int n) {
        if (n <= 1)
            return n;
        return fib(n - 1) + fib(n - 2);
    }
}
