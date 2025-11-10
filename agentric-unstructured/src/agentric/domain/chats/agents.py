from __future__ import annotations

from logging import getLogger

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TerminationCondition
from autogen_agentchat.conditions import (
    TextMentionTermination,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .tools import (
    approved_payment_decision,
    check_claim_documents,
    create_claim_request,
    generate_approve_email,
    generate_decline_email,
    generate_missing_files_email,
    generate_partial_payment_email,
    get_claim_request_status,
    get_classification,
    get_decision_summary,
    get_decline_reason,
    get_detail_request,
    get_missing_document_list,
    get_request_status,
    get_travel_plan,
    update_request_status,
    upload_claim_document,
)

logger = getLogger()


async def get_agent_team(
    model_client: "OpenAIChatCompletionClient",
    external_termination: "TerminationCondition",
    custom_message: str = "",
) -> SelectorGroupChat:
    def ask_input(prompt: str) -> str:
        logger.info("Skipping user input in non-interactive mode.")
        return "NO INPUT"

        # request agent tools

    get_request_status_tool = FunctionTool(
        get_request_status, description="Get status of the request."
    )
    get_detail_request_tool = FunctionTool(
        get_detail_request,
        description="Get detail of the request such as broker information, claim information, client information etc.",
    )
    update_request_status_tool = FunctionTool(
        update_request_status,
        description="""
        Change the status of the request.
        The new_status that user can choose is APPROVED, DECLINED, PENDING, MISSING, PAID, PARTIAL_PAYMENT.
        """,
    )
    get_decline_reason_tool = FunctionTool(
        get_decline_reason,
        description="Get the decline reason of the request.",
    )
    get_classification_tool = FunctionTool(
        get_classification,
        description="Get the classification result of the request.",
    )
    get_missing_document_list_tool = FunctionTool(
        get_missing_document_list,
        description="Get the missing document list of the request.",
    )
    get_decision_summary_tool = FunctionTool(
        get_decision_summary,
        description="Get the decision summary of the request.",
    )
    approved_payment_decision_tool = FunctionTool(
        approved_payment_decision,
        description="Make an approval or partial approval to the requested amount.",
    )

    generate_approved_email_tool = FunctionTool(
        generate_approve_email,
        description="Generate and send decline emails for insurance requests.",
    )

    generate_partial_payment_email_tool = FunctionTool(
        generate_partial_payment_email,
        description="Generate and send decline emails for insurance requests.",
    )

    generate_decline_email_tool = FunctionTool(
        generate_decline_email,
        description="Generate and send decline emails for insurance requests.",
    )
    get_decision_summary_tool = FunctionTool(
        get_decision_summary,
        description="Generate and retrieve decision summary of the request claim.",
    )
    generate_missing_email_tool = FunctionTool(
        generate_missing_files_email,
        description="Generate and send decline emails for insurance requests.",
    )

    user_agent = UserProxyAgent(
        "user_agent",
        description="A human user. This agent is to be selected if the assistant agents need human action to work",
        input_func=ask_input,
    )
    email_agent = AssistantAgent(
        name="email_preparation_agent",
        description="Generate and send emails for insurance requests",
        model_client=model_client,
        tools=[
            generate_approved_email_tool,
            generate_partial_payment_email_tool,
            generate_decline_email_tool,
            generate_missing_email_tool,
        ],
        reflect_on_tool_use=False,
        system_message=f"""
        You are the Email Agent for Travel Insurance claims. {custom_message}
        - Use the tools to generate and send emails for insurance requests.
        - When user asks to prepare email or generate email template, call the request status tool first, then based on the status, continue to the related email generation tool and generate emai template
        - Never generate emails manually—only return tool output.
        - Always return extracted information in structured JSON format.
        - Do not interpret or validate the data, just extract it.
        - Use markdown to format responses.
        - Use "TERMINATE" after each response.
        """,
    )

    analysis_agent = AssistantAgent(
        name="insurance_analyst_agent",
        description="Assist claim specialists to validate claims",
        model_client=model_client,
        tools=[
            get_classification_tool,
            get_decision_summary_tool,
            get_decline_reason_tool,
            get_missing_document_list_tool,
            approved_payment_decision_tool,
        ],
        reflect_on_tool_use=False,
        system_message=f"""
        You are the Analysis Agent for Travel Insurance claims and must use the provided tools to complete tasks. {custom_message}

        - Use the tools to check whether extracted claims are valid, invalid, incomplete or error.
        - If missing fields are detected, trigger the Missing Fields email processes.
        - If invalid or erroneous, trigger a Request for Valid Information email process.
        - If valid, forward results to the Policy Agent.
        - Never guess or validate manually—only return tool output.
        - Use markdown to format responses.
        - Use "TERMINATE" after each response.
        """,
    )

    insurance_request_agent = AssistantAgent(
        name="insurance_request_agent",
        description="Assist claim specialists to retrieve information about claims",
        model_client=model_client,
        tools=[
            get_request_status_tool,
            get_detail_request_tool,
            update_request_status_tool,
        ],
        reflect_on_tool_use=False,
        system_message=f"""
        You are the Insurance Request Specialist Agent for Travel Insurance claims. {custom_message}

        - Use the tools to retrieve information about requests that are the status of the request, detail of the request, claim and broker information, update the status of the request.
        - Never guess or validate manually—only return tool output.
        - Use markdown to format responses.
        - Use "TERMINATE" after each response.
        """,
    )

    general_agent = AssistantAgent(
        name="zurich_general_agent",
        description="Handles general questions about travel insurance claims and processes.",
        model_client=model_client,
        reflect_on_tool_use=False,
        system_message=f"""
        You are the Zurich Travel Insurance General Agent. {custom_message}
        - Answer any general question about Zurich's travel insurance offerings, coverages, or company policies.
        - If asked about your role, provide a one-sentence summary.
        - Never attempt to fetch claims, validate, or calculate payouts yourself.
        - Use "TERMINATE" after each response.

        Available specialists:

        - {analysis_agent.name} validates claims and return the status of the claim.
        - {insurance_request_agent.name} fetches details about requests, or updates request status and provides decline reasons.
        """,
    )

    agents = [
        user_agent,
        general_agent,
        insurance_request_agent,
        analysis_agent,
        email_agent,
    ]
    logger.info("createing Selector group chat")

    return SelectorGroupChat(
        model_client=model_client,
        participants=agents,  # type: ignore
        termination_condition=external_termination
        | TextMentionTermination("TERMINATE"),
        selector_prompt="""Select an agent to perform task.

        {roles}

        The following are the IMPORTANT rules that you must always follow:
        - For general conversation, always use zurich_general_agent.
        - If the user asks about a request's status or details like client info, or claim detail, use insurance_request_agent.
        - If the user asks about claim analysis like classification, decision summary, decline reason and missing files, use insurance_analyst_agent.
        - If the user asks about email related tasks, use email_preparation_agent.
        - If further input from the user is needed, use user_agent.
        - For all other topics (company policies, coverage definitions, etc.), choose zurich_general_agent.
        - After any tool call, return to the calling agent so they can summarize.
        - If user input requires clarification or human input, hand back to the user instead of selecting an agent.
        - MUST Use "TERMINATE" after each response.

        Current conversation context:
        {history}

        Now, read the last user message and select the best agent from {participants} to continue. Only output the agent's name.
        """,
        allow_repeated_speaker=True,
    )


check_claim_documents_tool = FunctionTool(
    check_claim_documents,
    description="Check if the claim documents are uploaded.",
)

get_claim_status_tool = FunctionTool(
    get_claim_request_status, description="Get status of the claim."
)
get_travel_plan_tool = FunctionTool(
    get_travel_plan, description="Get travel plan based on policy number."
)
create_claim_request_tool = FunctionTool(
    create_claim_request, description="Create claim request."
)

initiate_claim_document_upload_ui_tool = FunctionTool(
    upload_claim_document,
    name="initiate_claim_document_upload_ui",
    description="Show the file upload UI so the user can upload a claim-related document.",
)


async def get_assisant_agent_team(
    model_client: "OpenAIChatCompletionClient",
    external_termination: "TerminationCondition",
    custom_message: str = "",
) -> SelectorGroupChat:
    def ask_input(prompt: str) -> str:
        logger.info("Skipping user input in non-interactive mode.")
        return "NO INPUT"

    user_agent = UserProxyAgent(
        "user_agent",
        description="A human user. This agent is to be selected if the assistant agents need human action to work",
        input_func=ask_input,
    )

    claim_assistant_agent = AssistantAgent(
        name="claim_assistant_agent",
        description="Assist claim specialists to help user create and retrieve status about claims",
        model_client=model_client,
        tools=[
            check_claim_documents_tool,
            get_claim_status_tool,
            get_travel_plan_tool,
            create_claim_request_tool,
            initiate_claim_document_upload_ui_tool,
        ],
        reflect_on_tool_use=False,
        system_message=f"""You are the **Claim Assistant Agent** for Zurich Travel Insurance. Use the tools provided to assist users with travel insurance claims.
{custom_message}

---
### Conversation Style:

- Always respond in a warm, conversational, and professional tone.
- If the user greets (e.g. "Hi", "Hello"), respond with a friendly greeting and **1 emoji**.
- If the user reports an incident (lost luggage, illness, delay, etc.):
  1. Start with empathy (e.g. "Oh no! I'm really sorry to hear about your <issue> 😔 That must be so frustrating.")
  2. Reassure them: "Don't worry — I can help you file a claim and get things sorted quickly."
  3. Then ask for their **policy number**, if not already provided.

---

### Behavioral Rules:
- **Do not ask for the policy number again** if it has already been provided.
- Once the policy number is received:
  1. Use the `get_travel_plan` tool to fetch travel plan details.
  2. Then begin the document upload process using the `initiate_claim_document_upload_ui_tool`.
     - Do not ask users *what* document they want to upload.
     - Instead, **directly trigger** the `initiate_claim_document_upload_ui_tool` so the user can select and upload documents from their device.
  3. After each upload, ask the user:
     - "Would you like to upload another document, or should we proceed with your claim?"
     - If they want to upload more: continue using the upload tool.
     - If they confirm they're ready: check uploaded documents with `check_claim_documents`, then proceed with `create_claim_request`.

---

### After Creating a Claim Request:

Respond with **4 lines**, in this exact structure (DO NOT change the meaning):

1. **🎯** Your claim has been submitted and will be reviewed within 24 hours (or 1 business day).
2. **✈️** If relevant (e.g. baggage case), mention coordination with the airline.
3. **📧** Say the user will receive updates via email.
4. **💰** Say payment goes directly to their bank account if approved.

> ⚠️ Adapt the second line depending on the case (e.g. do not mention airline if irrelevant like for illness or cancellation).

---

### 🔧 Tools You Can Use:

Use these in this order:

1. `get_travel_plan` — once policy number is received
2. `initiate_claim_document_upload_ui_tool` — to provide ui for user to upload claim-related documents
3. `check_claim_documents` — to confirm all uploads are there
4. `create_claim_request` — once confirmed
5. `get_claim_status` — only when asked

---

### Response Formatting Rules:

- Use **markdown** in all messages (e.g. **bold**, emoji).
- Always start complete replies with **1 emoji** to match the tone.
- Always end a complete message with `"TERMINATE"`.
- Never make claim decisions or judge user inputs.
- If asked about your role, say:
  > *"I'm an assistant agent that helps with Zurich Travel Insurance claims and related questions."*
""",  # noqa: S608
    )
    agents = [
        user_agent,
        claim_assistant_agent,
    ]
    logger.info("createing Selector group chat")

    return SelectorGroupChat(
        model_client=model_client,
        participants=agents,  # type: ignore
        termination_condition=external_termination
        | TextMentionTermination("TERMINATE"),
        selector_prompt="""Select the appropriate agent to handle the user's latest message.
{roles}

---

### Routing Rules:

#### Use `claim_assistant_agent` if:
- The user greets or starts a conversation (e.g. "Hi", "Hello", "Hey").
- The user is starting or managing a travel insurance claim.
- They report an incident (e.g. lost luggage, trip cancellation, illness).
- They mention uploading documents or ask about document status.
- They ask about claim status, coverage, policy info, or how to file a claim.
- They provide a policy number or request to proceed with a claim.
- The assistant needs to follow up with a question to continue the flow.

#### Use `user_agent` if:
- The user input is unclear, incomplete, or needs clarification.
- You need to pause and wait for the user's reply (e.g. after asking for their policy number or email).

---

### Agent Behavior:
- After a tool call, return to the same agent to summarize or proceed.
- Do **not** use `"TERMINATE"` until the assistant has responded meaningfully.
- Only output the agent's name to continue — do not include reasoning or extra text.

---

Current conversation context:
{history}

Now, read the last user message and select the best agent from {participants} to continue. Only output the agent's name.
        """,
        allow_repeated_speaker=True,
    )
