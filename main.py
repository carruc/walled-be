import os
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool

# Load environment variables from .env file
load_dotenv()

# The SDK will automatically use the OPENAI_API_KEY from the environment
# No need to manually get it here if it's set for the environment

try:
    # Use WebSearchTool which is suitable for this kind of research task
    shopping_agent = Agent(
        name="Secure Shopping Agent",
        instructions=(
            "You are a secure, helpful online shopping agent. "
            "Research products based on the user request. "
            "Navigate e-commerce sites, compare, and provide a summary."
        ),
        tools=[WebSearchTool()],
        # The model will default to a capable model, or you can specify one
        # For WebSearchTool, a standard model like 'gpt-4o' is sufficient
        model="gpt-4o"
    )
    print("Agent created successfully!")
    print(shopping_agent)

    # Define the user's shopping query
    input_query = "What are the best wireless headphones for under $200 with noise cancellation?"

    # Run the agent to get the result
    result = Runner.run_sync(
        starting_agent=shopping_agent,
        input=input_query,
    )

    # Print the agent's final response
    print("\n--- Agent's Final Response ---")
    print(result.final_output)

except TypeError as e:
    print(f"Failed to create agent: {e}")
except NameError as e:
    print(f"Execution error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

