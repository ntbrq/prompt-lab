OPTIMIZATION_PROMPTS = {
    "improve": (
        "You are a prompt engineering expert. Analyze the following prompt for clarity, "
        "specificity, and effectiveness. Rewrite it to produce better results from AI models. "
        "After the rewritten prompt, add a section starting with '## Changes' explaining "
        "what you changed and why."
    ),
    "simplify": (
        "You are a prompt engineering expert. Simplify the following prompt while preserving "
        "its core intent. Remove redundancy and unnecessary complexity. "
        "After the simplified prompt, add a section starting with '## Changes' explaining "
        "what you simplified and why."
    ),
    "rephrase": (
        "You are a prompt engineering expert. Rephrase the following prompt using different "
        "wording but the same intent. Aim for clearer instruction. "
        "After the rephrased prompt, add a section starting with '## Changes' explaining "
        "what you rephrased and why."
    ),
    "translate": (
        "You are a prompt engineering expert. Translate the following prompt to {target_language}. "
        "Preserve technical terms and the prompt's intent. "
        "After the translated prompt, add a section starting with '## Changes' explaining "
        "any translation choices you made."
    ),
    "expand": (
        "You are a prompt engineering expert. Expand the following prompt with more specific "
        "instructions, examples, and constraints to get better results from AI models. "
        "After the expanded prompt, add a section starting with '## Changes' explaining "
        "what you added and why."
    ),
}


class PromptOptimizer:
    def __init__(self, provider):
        self.provider = provider

    def optimize_stream(self, content: str, optimization_type: str = "improve", context: str = None, target_language: str = None):
        system_prompt = OPTIMIZATION_PROMPTS.get(optimization_type, OPTIMIZATION_PROMPTS["improve"])

        if target_language and optimization_type == "translate":
            system_prompt = system_prompt.format(target_language=target_language)

        user_message = content
        if context:
            user_message = f"Context: {context}\n\nPrompt to optimize:\n{content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        yield from self.provider.chat_stream(messages)

    def optimize(self, content: str, optimization_type: str = "improve", context: str = None, target_language: str = None) -> str:
        system_prompt = OPTIMIZATION_PROMPTS.get(optimization_type, OPTIMIZATION_PROMPTS["improve"])

        if target_language and optimization_type == "translate":
            system_prompt = system_prompt.format(target_language=target_language)

        user_message = content
        if context:
            user_message = f"Context: {context}\n\nPrompt to optimize:\n{content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return self.provider.chat(messages)
