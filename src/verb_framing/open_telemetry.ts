import { trace } from "@opentelemetry/api";

export const verbFramingTracer = () => trace.getTracer('verb-framing', '1.0.0');