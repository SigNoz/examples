# Spring Boot Logging Demo

A minimal Spring Boot application demonstrating default logging behavior without any custom configuration.

## Prerequisites

Before running this application, make sure you have the following installed:

- **Java 17 or higher** - [Download JDK](https://openjdk.org/install/)
- **Maven 3.6 or higher** - [Download Maven](https://maven.apache.org/install.html)

Verify your installations:

```bash
java -version
mvn -version
```

## Project Structure

```
spring-boot-logging-demo/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/example/demo/
│       │       └── SpringBootLoggingDemoApplication.java
│       └── resources/
│           └── application.properties
├── pom.xml
└── README.md
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/SigNoz/examples.git
cd examples/java/spring-boot-logging/
```

### 2. Build the Project

```bash
mvn clean install
```

This command will:
- Download all required dependencies
- Compile the source code
- Package the application as a JAR file

### 3. Run the Application

You can run the application in two ways:

**Option A: Using Maven**

```bash
mvn spring-boot:run
```

**Option B: Using the JAR file**

```bash
java -jar target/spring-boot-logging-demo-1.0.0.jar
```

## What to Expect

When you run the application, you will see output in the console showing different log levels:

```
========================================
Spring Boot Logging Demo Application
========================================
2026-01-21 16:00:00.123  INFO 12345 --- [main] com.example.demo.DemoRunner : INFO level log - General application information
2026-01-21 16:00:00.124  WARN 12345 --- [main] com.example.demo.DemoRunner : WARN level log - Potential issues or warnings
2026-01-21 16:00:00.125 ERROR 12345 --- [main] com.example.demo.DemoRunner : ERROR level log - Error events
========================================
Check the console output above!
Notice that TRACE and DEBUG logs are not visible by default
========================================
```

## Default Logging Behavior

This application demonstrates Spring Boot's default logging configuration:

- **Logging Framework**: Logback (included by default)
- **Default Log Level**: INFO
- **Output Destination**: Console only (no file logging)
- **Visible Levels**: INFO, WARN, ERROR
- **Hidden Levels**: TRACE, DEBUG (below INFO threshold)

## Understanding the Code

The main class `SpringBootLoggingDemoApplication` contains:

```java
private static final Logger logger = LoggerFactory.getLogger(DemoRunner.class);

logger.trace("TRACE level log");  // Not visible (below INFO)
logger.debug("DEBUG level log");  // Not visible (below INFO)
logger.info("INFO level log");    // Visible
logger.warn("WARN level log");    // Visible
logger.error("ERROR level log");  // Visible
```

## Next Steps

To learn more about Spring Boot logging configuration, you can follow our guide on [Spring Boot Logging](https://signoz.io/guides/spring-boot-logging/).

## Troubleshooting

**Issue: Application doesn't start**
- Verify Java 17+ is installed
- Check that port 8080 is not already in use

**Issue: Maven build fails**
- Ensure Maven is properly installed
- Clear Maven cache: `mvn clean`
- Delete `target/` folder and rebuild

**Issue: No logs appear**
- Check that you're looking at the console output
- Verify the application actually started successfully

## License

This project is for educational purposes.
