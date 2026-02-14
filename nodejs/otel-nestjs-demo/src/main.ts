// THIS MUST BE THE FIRST IMPORT
import tracer from '../tracer.production';

// Now import NestJS and other application modules
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');

  try {
    // Start tracer immediately before creating the app
    await tracer.start();

    const app = await NestFactory.create(AppModule);

    app.setGlobalPrefix('api');
    app.enableCors();

    const port = process.env.PORT || 3000;
    await app.listen(port);

    logger.log(`Application running on: http://localhost:${port}/api`);
  } catch (error) {
    logger.error('Error starting application:', error);
    process.exit(1);
  }
}

bootstrap();
