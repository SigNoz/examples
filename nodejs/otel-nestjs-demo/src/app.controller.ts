import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('info')
  getInfo() {
    return {
      name: 'NestJS OpenTelemetry Demo',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      endpoints: [
        'GET /api - This info endpoint',
        'GET /api/health - Health check (ignored by tracing)',
        'GET /api/users - Get all users',
        'GET /api/users/:id - Get user by ID',
        'POST /api/users - Create new user',
        'GET /api/users/search?email=example - Search users by email',
        'GET /api/orders - Get all orders',
        'GET /api/orders/:id - Get order by ID',
        'POST /api/orders - Create new order',
      ],
    };
  }
}
