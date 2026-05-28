import { SpanStatusCode, trace } from "@opentelemetry/api";
import { describe, expect, it } from "vitest";
import * as helpers from "./helpers.js"
import * as sut from "../core.js"

const testTracer = () => trace.getTracer('test-exporter', '1.0.0');

describe('wrapOTEL', () => {
  it('calls callback', async () => {
    let i = 0;
    await sut.wrapOTEL(testTracer(),"test-span",async () => {
      i=1
    })
    expect(i).toEqual(1)
  })

  it('returns value', async () => {
    const result = await sut.wrapOTEL(testTracer(),"test-span",async () => {
      return 5;
    })
    expect(result).toEqual(5)
  })

  it('creates span', async () => {
    const { exporter } = helpers.memorySDK()
    await sut.wrapOTEL(testTracer(),"test-span",async () => {
      return 5;
    })
    const spans = exporter.getFinishedSpans()
    expect(helpers.spanByName(spans,"test-span")).not.undefined
  })

  it('passes span into callback', async () => {
    const { exporter } = helpers.memorySDK()
    await sut.wrapOTEL(testTracer(),"test-span",async (span) => {
      span.setAttribute('my-attr',5)
    })
    const spans = exporter.getFinishedSpans()
    expect(helpers.spanByName(spans,"test-span")?.attributes['my-attr']).toEqual(5)
  })

  it('throws errors', async () => {
    const errorToThrow = new Error("something bad happened");
    try {
      await sut.wrapOTEL(testTracer(),"test-span",async (span) => {
        throw errorToThrow
      })
      expect(false).true
    } catch (error) {
      expect(error).toBe(errorToThrow)
    }
  })

  it('records errors', async () => {
    const { exporter } = helpers.memorySDK()
    try {
      await sut.wrapOTEL(testTracer(),"test-span",async (span) => {
        throw new Error("uh oh")
      })
      expect(false).true
    } catch {
      const spans = exporter.getFinishedSpans()
      const span = helpers.spanByName(spans,"test-span")
      expect((span?.events[0].attributes as any)["exception.message"]).toEqual("uh oh")
    }
  })

  it('sets error status', async () => {
    const { exporter } = helpers.memorySDK()
    try {
      await sut.wrapOTEL(testTracer(),"test-span",async (span) => {
          throw new Error("uh oh")
      })
      expect(false).true
    } catch {
      const spans = exporter.getFinishedSpans()
      const span = helpers.spanByName(spans,"test-span")
      expect(span?.status).toEqual({code: SpanStatusCode.ERROR, message: "uh oh"})
    }
  })
})