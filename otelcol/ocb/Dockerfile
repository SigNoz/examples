FROM otel/opentelemetry-collector-builder:0.142.0

# install git as root user; git is required for building some components
USER root
RUN apk add --no-cache git

# Return to original user for better security
USER 10001
