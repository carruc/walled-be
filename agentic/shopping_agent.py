from dotenv import load_dotenv
from agents import Agent, Runner
from agentic.tools import go_to_url, find_and_click_element, summarize_page_content, request_payment_confirmation, \
    client_id_var, send_plan_for_approval
from api.websocket import manager
import json

load_dotenv()


def create_planner_agent():
    return Agent(
        name="Planner Agent",
        instructions=(
            "You are a planner agent. Your goal is to create a step-by-step plan for the user's request. "
            "Once the plan is created, send it for approval using the send_plan_for_approval tool. "
            "Your job is done after calling this tool. The tool's output should be your final response."
        ),
        tools=[send_plan_for_approval],
        model="gpt-4o"
    )


def create_shopping_agent():
    return Agent(
        name="Secure Shopping Agent",
        instructions=(
            "You are a secure, helpful online shopping agent. "
            "Follow the plan provided to you. "
            "Research products based on the user request. "
            "Navigate e-commerce sites, compare, and provide a summary. "
            "IMPORTANT: For this test, after you have visited 3 websites, "
            "assume your research is complete. Make up a realistic product name and price, "
            "and then use the request_payment_confirmation tool to finish the task."
        ),
        tools=[go_to_url, find_and_click_element, summarize_page_content, request_payment_confirmation],
        model="gpt-4o"
    )


async def run_agent(agent: Agent, query: str, client_id: str):
    client_id_var.set(client_id)
    planner_agent = create_planner_agent()
    plan_run = await Runner.run(
        starting_agent=planner_agent,
        input=query,
    )

    approved_plan = None
    for item in plan_run.new_items:
        # The output of the 'send_plan_for_approval' tool is a string that starts with "Plan approved by user: "
        if hasattr(item, 'output') and isinstance(item.output, str) and item.output.startswith("Plan approved by user:"):
            try:
                approved_plan = item.output.split("Plan approved by user: ", 1)[1]
                break
            except IndexError:
                continue

    if not approved_plan:
        await manager.send_personal_message(
            json.dumps({"type": "status", "data": {"message": "Plan not approved or could not be parsed. Halting execution."}}),
            client_id
        )
        return

    await Runner.run(
        starting_agent=agent,
        input=f"Execute the following plan: {approved_plan}. Original user request: {query}",
    )
