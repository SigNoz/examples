package com.example.demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class SpringBootLoggingDemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(SpringBootLoggingDemoApplication.class, args);
    }
}

@Component
class DemoRunner implements CommandLineRunner {
    
    private static final Logger logger = LoggerFactory.getLogger(DemoRunner.class);

    @Override
    public void run(String... args) {
        System.out.println("========================================");
        System.out.println("Spring Boot Logging Demo Application");
        System.out.println("========================================");
        
        logger.trace("TRACE level log - Most detailed");
        logger.debug("DEBUG level log - Detailed diagnostic information");
        logger.info("INFO level log - General application information");
        logger.warn("WARN level log - Potential issues or warnings");
        logger.error("ERROR level log - Error events");
        
        System.out.println("========================================");
        System.out.println("Check the console output above!");
        System.out.println("Notice that TRACE and DEBUG logs are not visible by default. They need to be enabled.");
        System.out.println("========================================");
    }
}
