"""
Apple Foundation Models (on-device LLM, macOS 26+).

Coming soon — will expose:

    from macbook_ai.foundation import LanguageModel

    model = LanguageModel()
    response = await model.respond("Summarise this text: …")

    # Streaming
    async for chunk in model.stream("Write a poem about Swift"):
        print(chunk, end="", flush=True)

Requires macOS 26+ and the FoundationModels framework.
"""
