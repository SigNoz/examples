import { createOpenAI } from "@ai-sdk/openai";
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const scaleRice = createTool({
  id: "scale-rice",
  description: "Calculate the grams of dry rice needed for a given number of servings.",
  inputSchema: z.object({ servings: z.number().int().positive() }),
  execute: async ({ servings }) => ({ grams: servings * 75 }),
});

const openai = createOpenAI({ baseURL: process.env.OPENAI_BASE_URL });

export const chefAgent = new Agent({
  id: "chef-agent",
  name: "Chef Agent",
  instructions: "Help people cook. Always use the scaleRice tool for rice quantities.",
  model: openai.chat("gpt-4o-mini"),
  tools: { scaleRice },
});
