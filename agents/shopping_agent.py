import os
from dotenv import load_dotenv
from openai_agents import Agent, Runner
from agents.tools import go_to_url, find_and_click_element, summarize_page_content, request_payment_confirmation

load_dotenv()


def create_shopping_agent():
    return Agent(
        name="Secure Shopping Agent",
        instructions=(
            "You are a secure, helpful online shopping agent. "
            "Research products based on the user request. "
            "Navigate e-commerce sites, compare, and provide a summary. "
            "When you are ready to make a payment, use the request_payment_confirmation tool."
        ),
        tools=[go_to_url, find_and_click_element, summarize_page_content, request_payment_confirmation],
        model="gpt-4o"
    )

async def run_agent(agent: Agent, query: str, client_id: str):
    # This is a bit of a hack to make the client_id available to the tool.
    # A better solution would be to use a stateful tool or context injection.
    from agents.tools import set_client_id
    set_client_id(client_id)
    
    return await Runner.run(
        starting_agent=agent,
        input=query,
    )
