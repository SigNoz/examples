package io.signoz.springbootdemo;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

@Component
public class FibonacciMetricsFilter extends OncePerRequestFilter {
    private static final Logger log = LoggerFactory.getLogger(FibonacciMetricsFilter.class);
    private static final String FIBONACCI_PATH = "/fibonacci";

    private final MetricsService metricsService;

    public FibonacciMetricsFilter(MetricsService metricsService) {
        this.metricsService = metricsService;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !"POST".equals(request.getMethod()) || !FIBONACCI_PATH.equals(request.getRequestURI());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        long startNanos = System.nanoTime();
        try {
            filterChain.doFilter(request, response);
        } finally {
            double durationSeconds = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startNanos) / 1000.0;
            log.info("served fibonacci request in {} seconds", durationSeconds);
            metricsService.recordFibonacciDuration(
                    durationSeconds,
                    request.getMethod(),
                    FIBONACCI_PATH,
                    response.getStatus());
        }
    }
}
