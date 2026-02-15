import { trace, context, SpanStatusCode } from '@opentelemetry/api';

export function Traced(spanName?: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const tracer = trace.getTracer('nestjs-app', '1.0.0');

    descriptor.value = async function (...args: any[]) {
      const finalSpanName =
        spanName || `${target.constructor.name}.${propertyKey}`;

      return await tracer.startActiveSpan(finalSpanName, async (span) => {
        try {
          span.setAttributes({
            'method.class': target.constructor.name,
            'method.name': propertyKey,
          });

          const result = await originalMethod.apply(this, args);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
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
    };

    return descriptor;
  };
}
