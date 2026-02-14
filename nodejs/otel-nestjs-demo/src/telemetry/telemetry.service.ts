import { Injectable, OnModuleDestroy, Logger } from '@nestjs/common';
import { NodeSDK } from '@opentelemetry/sdk-node';

@Injectable()
export class TelemetryService implements OnModuleDestroy {
  private readonly logger = new Logger(TelemetryService.name);
  private sdk: NodeSDK;

  async initializeTelemetry(): Promise<void> {
    try {
      // Import the tracer configuration
      const tracerModule = await import('../../tracer.production');
      this.sdk = tracerModule.default;

      await this.sdk.start();
      this.logger.log('OpenTelemetry SDK initialized successfully');

      // Handle process shutdown gracefully
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());
    } catch (error) {
      this.logger.error('Failed to initialize OpenTelemetry SDK:', error);
      throw error;
    }
  }

  async onModuleDestroy(): Promise<void> {
    await this.shutdown();
  }

  private async shutdown(): Promise<void> {
    try {
      if (this.sdk) {
        this.logger.log('Shutting down OpenTelemetry SDK...');
        await this.sdk.shutdown();
        this.logger.log('OpenTelemetry SDK shutdown complete');
      }
    } catch (error) {
      this.logger.error('Error during OpenTelemetry SDK shutdown:', error);
    }
  }
}
