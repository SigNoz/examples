package io.signoz.springbootdemo;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class HttpServerActiveRequestsFilter extends OncePerRequestFilter {

    private final MetricsService metricsService;

    public HttpServerActiveRequestsFilter(MetricsService metricsService) {
        this.metricsService = metricsService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String path = request.getRequestURI();
        if (path == null || path.isBlank()) {
            path = "/";
        }

        metricsService.incrementActiveRequests(request.getMethod(), path);
        try {
            filterChain.doFilter(request, response);
        } finally {
            metricsService.decrementActiveRequests(request.getMethod(), path);
        }
    }
}
