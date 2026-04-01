package io.signoz.springbootdemo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestClient;

@SpringBootApplication
public class Application {
    private static final String HTTPBIN_BASE_URL = "https://httpbin.org";

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public RestClient restClient(RestClient.Builder builder) {
        return builder.baseUrl(HTTPBIN_BASE_URL).build();
    }
}
