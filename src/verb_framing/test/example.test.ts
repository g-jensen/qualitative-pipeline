import { generateText, Output } from "ai";
import { describe, it, expect } from "vitest";
import { resolveModel } from "../model-resolver.js";
import { z } from 'zod';
import { generateKeyPoint, generateSupportingDetail, generateVerbPhrase, QuoteClass } from "../core.js";

const MODEL = {model_id: "gemma3:12b", model_url: "http://localhost:11434"}
// const MODEL = {model_id: "claude-haiku-4-5"}

describe('example tests', { tags: ['example'] }, () => {
    it.skip('structured output', async () => {
        const result = await generateText({
            model: resolveModel(MODEL),
            system: "Give me a list of things with the prompted category",
            prompt: "Food",
            output: Output.object({
            schema: z.array(z.string()).min(1).max(5)
            })
        });
        expect(result.output).toEqual(["Feces"])
    })

    it.skip('emotional generation', async () => {
        const verbs = await generateVerbPhrase(
            {text: "I hated the disgusting burger", class: QuoteClass.EMOTIONAL_REACTION, documentId: "100"},
            MODEL
        )
        expect(verbs).toEqual([])
    })

    it.skip('verb generation', async () => {
        const verbs = await generateVerbPhrase(
            {text: "I ate the burger", class: QuoteClass.INNER_THINKING, documentId: "100"},
            MODEL
        )
        expect(verbs).toEqual([])
    })

    it.skip('key point generation', async () => {
        expect([
            await generateKeyPoint(
                "Follow",
                {text: "So, I knew, right, we kind of follow what performances they put on. So I think I probably either got an email or I", class: QuoteClass.EMOTIONAL_REACTION, documentId: "100"},
                MODEL
            ),
            await generateKeyPoint(
                "Rely",
                {text: "I really like the 930 and the Black Cat. ... I really like the 930, because they have the history of breaking bands. It's nice to see people on the way up before they get really big, because the next time they come around, they are probably playing at Verizon center or a stadium..", class: QuoteClass.PERSONAL_RULE, documentId: "100"},
                MODEL
            ),
            await generateKeyPoint(
                "Feel lonely",
                {text: "The people decided to ignore me.", class: QuoteClass.EMOTIONAL_REACTION, documentId: "100"},
                MODEL
            ),
            await generateKeyPoint(
                "Decide",
                {text: "I finally decided to tell the truth.", class: QuoteClass.INNER_THINKING, documentId: "100"},
                MODEL
            ),
            await generateKeyPoint(
                "Decide",
                {text: "[Tell me about the experience of Wolf Trap.] ... We usually look at the schedule when it comes out and say like, \"Oh, this would be great to go see.\" This year we looked at it but didn't bother to buy tickets to anything.", class: QuoteClass.INNER_THINKING, documentId: "100"},
                MODEL
            )
        ]).toEqual("")
    })

    it('supporting detail generation', async () => {
        expect([
            await generateSupportingDetail(
                "Feel curious",
                "about an upcoming performance of SpogeBob SquarePants",
                {text: " just saw a postcard or, you know, something about the SpongeBob SquarePants performance that they were putting on. And so I was curious.", class: QuoteClass.EMOTIONAL_REACTION, documentId: "100"},
                MODEL
            ),
            await generateSupportingDetail(
                "Feel lonely",
                "that people ignore me",
                {text: "The people decided to ignore me.", class: QuoteClass.EMOTIONAL_REACTION, documentId: "100"},
                MODEL
            ),
            await generateSupportingDetail(
                "Decide",
                "to finally tell the truth",
                {text: "I finally decided to tell the truth.", class: QuoteClass.INNER_THINKING, documentId: "100"},
                MODEL
            ),
            await generateSupportingDetail(
                "Accept",
                "my wife's decision to see the musical SpongeBob SquarePants",
                {text: "So we went out to a performance at the high school, the local high school of SpongeBob SquarePants, the musical. And it was something my wife chose, but we had talked about going to see a musical, a high school musical at the high school because our kids had gone there", class: QuoteClass.INNER_THINKING, documentId: "100"},
                MODEL
            )
        ]).toEqual("")
    })
})
