import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { UserModule } from './user/user.module';
import { OrderModule } from './order/order.module';
import { HealthController } from './health/health.controller';

@Module({
  imports: [UserModule, OrderModule],
  controllers: [AppController, HealthController],
  providers: [AppService],
})
export class AppModule {}
