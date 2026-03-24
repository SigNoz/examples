package io.signoz.springbootdemo;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
@ConditionalOnProperty(
        name = "demo.metrics.manual-http-server-active-requests.enabled",
        havingValue = "true")
public class ManualHttpServerActiveRequestsFilter extends OncePerRequestFilter {

    private final ManualHttpServerActiveRequestsMetrics metrics;

    public ManualHttpServerActiveRequestsFilter(ManualHttpServerActiveRequestsMetrics metrics) {
        this.metrics = metrics;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String path = request.getRequestURI();
        if (path == null || path.isBlank()) {
            path = "/";
        }

        metrics.increment(request.getMethod(), path);
        try {
            filterChain.doFilter(request, response);
        } finally {
            metrics.decrement(request.getMethod(), path);
        }
    }
}
