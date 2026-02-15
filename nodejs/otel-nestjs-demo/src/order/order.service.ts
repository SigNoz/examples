import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import {
  trace,
  context,
  propagation,
  SpanStatusCode,
} from '@opentelemetry/api';
import { firstValueFrom } from 'rxjs';

export interface CreateOrderDto {
  userId: string;
  items: OrderItem[];
  totalAmount: number;
  paymentMethod: string;
}

export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  totalAmount: number;
  status: string;
  paymentTransactionId: string;
  createdAt: Date;
}

export interface PaymentResult {
  transactionId: string;
  status: string;
  amount: number;
}

@Injectable()
export class OrderService {
  private readonly logger = new Logger(OrderService.name);
  private readonly tracer = trace.getTracer('order-service', '1.0.0');
  private orders: Order[] = [];

  constructor(private readonly httpService: HttpService) {}

  async createOrder(orderData: CreateOrderDto): Promise<Order> {
    return await this.tracer.startActiveSpan('create_order', async (span) => {
      try {
        span.setAttributes({
          'order.user_id': orderData.userId,
          'order.items_count': orderData.items.length,
          'order.total_amount': orderData.totalAmount,
        });

        // Process payment with context propagation
        const paymentResult = await this.processPayment(orderData);

        // Create order record
        const order = await this.saveOrder(orderData, paymentResult);

        span.setStatus({ code: SpanStatusCode.OK });
        return order;
      } catch (error) {
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        throw error;
      } finally {
        span.end();
      }
    });
  }

  private async processPayment(
    orderData: CreateOrderDto,
  ): Promise<PaymentResult> {
    return await this.tracer.startActiveSpan(
      'process_payment',
      async (span) => {
        try {
          // Create headers with trace context for downstream service
          const headers = {};
          propagation.inject(context.active(), headers);

          span.setAttributes({
            'payment.amount': orderData.totalAmount,
            'payment.method': orderData.paymentMethod,
          });

          // Simulate external payment service call
          // In real scenario, this would be: http://payment-service:3003/api/process
          const paymentRequest = {
            userId: orderData.userId,
            amount: orderData.totalAmount,
            paymentMethod: orderData.paymentMethod,
          };

          // Simulate payment processing delay
          await new Promise((resolve) => setTimeout(resolve, 200));

          // Mock successful payment response
          const mockPaymentResponse = {
            transactionId: `txn_${Math.random().toString(36).substring(7)}`,
            status: 'completed',
            amount: orderData.totalAmount,
          };

          span.setAttributes({
            'payment.transaction_id': mockPaymentResponse.transactionId,
            'payment.status': mockPaymentResponse.status,
          });

          span.setStatus({ code: SpanStatusCode.OK });
          return mockPaymentResponse;
        } catch (error) {
          span.recordException(error);
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error.message,
          });
          throw error;
        } finally {
          span.end();
        }
      },
    );
  }

  private async saveOrder(
    orderData: CreateOrderDto,
    paymentResult: PaymentResult,
  ): Promise<Order> {
    return await this.tracer.startActiveSpan('save_order', async (span) => {
      try {
        // Simulate database save operation
        await new Promise((resolve) => setTimeout(resolve, 100));

        const order: Order = {
          id: `order_${Math.random().toString(36).substring(7)}`,
          userId: orderData.userId,
          items: orderData.items,
          totalAmount: orderData.totalAmount,
          status: 'confirmed',
          paymentTransactionId: paymentResult.transactionId,
          createdAt: new Date(),
        };

        this.orders.push(order);

        span.setAttributes({
          'order.id': order.id,
          'order.status': order.status,
        });

        span.setStatus({ code: SpanStatusCode.OK });
        return order;
      } catch (error) {
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        throw error;
      } finally {
        span.end();
      }
    });
  }

  async getOrderById(orderId: string): Promise<Order | null> {
    return await this.tracer.startActiveSpan(
      'get_order_by_id',
      async (span) => {
        try {
          span.setAttributes({
            'order.id': orderId,
          });

          // Simulate database query
          await new Promise((resolve) => setTimeout(resolve, 50));

          const order = this.orders.find((o) => o.id === orderId);

          if (order) {
            span.setAttributes({
              'order.found': true,
              'order.status': order.status,
            });
          } else {
            span.setAttributes({
              'order.found': false,
            });
          }

          span.setStatus({ code: SpanStatusCode.OK });
          return order || null;
        } catch (error) {
          span.recordException(error);
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error.message,
          });
          throw error;
        } finally {
          span.end();
        }
      },
    );
  }

  async getAllOrders(): Promise<Order[]> {
    return await this.tracer.startActiveSpan('get_all_orders', async (span) => {
      try {
        // Simulate database query
        await new Promise((resolve) => setTimeout(resolve, 30));

        span.setAttributes({
          'orders.count': this.orders.length,
        });

        span.setStatus({ code: SpanStatusCode.OK });
        return this.orders;
      } catch (error) {
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        throw error;
      } finally {
        span.end();
      }
    });
  }
}
