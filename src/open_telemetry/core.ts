import { Span, SpanStatusCode, Tracer } from "@opentelemetry/api";

export function flattenObject(obj: any) {
  const attributes: any = {};
  for (const key in obj) {
    const value = obj[key];
    attributes[key] = value
  }
  return attributes;
}

export function wrapOTEL<T>(tracer: Tracer, name: string, fn: (span: Span) => Promise<T>): Promise<T> {
  return tracer.startActiveSpan(name, async (span) => {
    return fn(span)
      .then((result) => {
        span.end();
        return result;
      })
      .catch((error) => {
        span.recordException(error);
        span.setStatus({code: SpanStatusCode.ERROR, message: error.message});
        span.end();
        throw error;
      });
  });
}