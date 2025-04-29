from smolagents import CodeAgent, OpenAIServerModel, LiteLLMModel

agent = CodeAgent(
    model=LiteLLMModel(
        #model_id="anthropic/claude-3-5-sonnet-20241022",
        #api_key="YOUR_API_KEY" # API key removed for security
        model_id="ollama/phi4:latest",
        api_base="http://127.0.0.1:11434",
        api_key="ollama",
        num_ctx=16384,
        temperature=0.0
    ),
    tools=[],
)

agent.run("CHWRT是测量是Energy还是Fluid?")
