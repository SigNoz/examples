package io.signoz.springbootdemo;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import java.util.concurrent.ThreadLocalRandom;

@RestController
public class DemoController {
    private static final Logger log = LoggerFactory.getLogger(DemoController.class);
    private static final String HTTPBIN_PATH = "/anything";

    private final FibonacciService fibonacciService;
    private final RestClient restClient;
    private final ObjectMapper objectMapper;

    public DemoController(FibonacciService fibonacciService,
            RestClient restClient,
            ObjectMapper objectMapper) {
        this.fibonacciService = fibonacciService;
        this.restClient = restClient;
        this.objectMapper = objectMapper;
    }

    @GetMapping("/")
    public ResponseEntity<String> index() {
        log.info("Handling GET /");
        return ResponseEntity.ok("Hello, World!");
    }

    // define the input constraints for the fibonacci request
    record FibonacciRequest(
            @NotNull(message = "missing required field: number") @Min(value = 0, message = "number must be between 0 and 92") @Max(value = 92, message = "number must be between 0 and 92") Integer number) {
    }

    record FibonacciResponse(Integer number, Long result) {
    }

    @PostMapping(value = "/fibonacci", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<FibonacciResponse> fibonacci(@Valid @RequestBody FibonacciRequest request) {
        try {
            // simulate business logic (db calls, complex processing logic, etc.)
            long delay = ThreadLocalRandom.current().nextLong(250, 750);
            Thread.sleep(delay);

            long result = fibonacciService.compute(request.number());
            log.info("fibonacci({}) = {}", request.number(), result);

            return ResponseEntity.ok(new FibonacciResponse(request.number(), result));

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            Span.current().setStatus(StatusCode.ERROR, "interrupted");
            throw new IllegalStateException("Interrupted while simulating fibonacci processing delay", e);
        }
    }

    // -------------------------------------------------------------------------
    // GET /external
    //
    // Makes an outbound HTTP GET to httpbin.org/anything.
    // The agent auto-instruments RestClient and injects the W3C traceparent header,
    // so the downstream service receives the correct trace context.
    // We return the httpbin response body so callers can verify the propagated
    // header.
    // -------------------------------------------------------------------------

    @GetMapping("/external")
    public ResponseEntity<JsonNode> external() {
        log.info("calling external httpbin API");

        try {
            // RestClient is auto-instrumented by the Java Agent. It creates a client span
            // and injects `traceparent` + `tracestate` from the current span context
            // into the headers automatically
            String body = restClient.get()
                    .uri(HTTPBIN_PATH)
                    .retrieve()
                    .body(String.class);

            log.info("httpbin response received");

            JsonNode httpbinResponse = objectMapper.readTree(body);
            JsonNode response = objectMapper.createObjectNode()
                    .put("note", "This endpoint calls httpbin. with propagated trace context. "
                            + "Match the echoed Traceparent header in httpbin_response.headers with the trace and span IDs in your OTel Backend.")
                    .set("httpbin_response", httpbinResponse);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            Span.current().setStatus(StatusCode.ERROR, e.getMessage());
            Span.current().setAttribute("error.type", e.getClass().getSimpleName());
            throw new IllegalStateException("httpbin request failed", e);
        }
    }
}
