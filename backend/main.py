import json
import os
import random
import time
from typing import Annotated, Any, Dict, List, Literal, Sequence, TypedDict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from tools.pdf_util import generate_and_save_jira_pdf  # Import your standalone PDF utility node

from pydantic import BaseModel, Field

# Core LangChain & LangGraph Orchestration Imports
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START, add_messages
from langgraph.prebuilt import ToolNode

# Database & Tools Adapters
from tools.db import (
    delete_db_history,
    get_db_history,
    init_db,
    save_db_message,
    get_tools_and_usecases_from_db,
    upsert_tools_data,
)
from tools.tools_engine import (
    execute_create_jira_ticket,
    list_available_tools,
    request_jira_ticket_form,
)

# 1. INITIALIZATION & MIDDLEWARE BOOTSTRAP ---
load_dotenv()
app = FastAPI(title="CARIAD Core Engine Interface Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# 1. UPDATE STATIC FILES MOUNT TO PREVENT ROUTING HIJACKS
# =====================================================================
os.makedirs("generated", exist_ok=True)
# Changed from '/download' to '/static' to clear overlapping routing domains
app.mount("/static", StaticFiles(directory="generated"), name="static_assets")

init_db()

# 2. DEFINING THE NATIVE LANGGRAPH STATE & WORKFLOW ---


class AgentState(TypedDict):
    """The unified internal runtime state of our CARIAD agent workspace graph."""

    # The Annotated wrapper with add_messages tells LangGraph:
    # "Do not overwrite this list. Append new messages to the existing memory."
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Prepare LLM engine and register tool assets
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
tools_list = [
    list_available_tools,
    execute_create_jira_ticket,
    request_jira_ticket_form,
]
llm_with_tools = llm.bind_tools(tools_list)

# Structured Prompt Engineering Framework
system_prompt = (
    "You are a professional assistant for the CARIAD tool chain platform.\n\n"
    "CRITICAL TOOL-ROUTING & DETAIL RULES (EVALUATE IN ORDER):\n"
    "1. ABSOLUTE BYPASS FOR TICKET GENERATION: If the incoming user message contains 'COMMAND: EXECUTE_JIRA_CREATION', "
    "you MUST immediately execute the 'execute_create_jira_ticket' tool. Extract fields directly from the markdown list "
    "and pass them to parameters. Do NOT offer a form, do NOT repeat the request, and go straight to calling the tool.\n\n"
    "2. AUTOMATED FORM MODE: If the user says 'bug', 'file a bug', 'error', 'create ticket', 'jira', or 'issue', "
    "AND the message does NOT contain 'COMMAND: EXECUTE_JIRA_CREATION', "
    "you MUST immediately call the 'request_jira_ticket_form' tool to display input fields.\n\n"
    "3. PLATFORM REGISTRY DETAIL PROTOCOLS:\n"
    "   When the user asks about available tools, supported tools, registries, or use cases, you MUST call 'list_available_tools' first.\n"
    "   Once you receive the raw database JSON, format your output according to these strict rules:\n"
    "   - GENERAL LIST REQUEST: If the user just asks for a list of tools, display ONLY the plain bulleted names of the tools. Do NOT include versions or use cases.\n"
    "   - DETAILED/SPECIFIC REQUEST: If the user explicitly asks for 'details', 'versions', 'use cases', 'info', or asks about a single specific tool by name, "
    "     provide the tool name, its version, and an indented sub-bulleted list of all its registered use cases.\n"
    "   - Never make up or hallucinate tool details. Word your final answer using only data provided by the tool."
    "   - Markup for lists must be clean and consistent. Use '-' for top-level bullets and '  -' for sub-bullets.\n\n"
)

def print_llm_invoke_message_for_debugging(full_messages):
    # 🟩 CLEAN & TIDY LOG PRINTING START ---
    print(f"\n==================== 🤖 LLM INVOKE INTERCEPT [{len(full_messages)} Messages] ====================")
    for i, msg in enumerate(full_messages):
        msg_type = msg.__class__.__name__  # Extracts "SystemMessage", "HumanMessage", etc.
        
        # Pull text and slice it if it is a massive JSON payload
        raw_content = str(msg.content).strip()
        truncated_content = (raw_content[:90] + " ... [TRUNCATED JSON]") if len(raw_content) > 100 else raw_content
        truncated_content = truncated_content.replace('\n', ' ') # Flatten multi-line logs
        
        # Extract operational identifiers if they exist
        tool_info = ""
        if msg_type == "AIMessage" and getattr(msg, "tool_calls", None):
            tool_calls_summary = [tc['name'] for tc in msg.tool_calls]
            tool_info = f" | 🎯 Calls Tools: {tool_calls_summary}"
        elif msg_type == "ToolMessage":
            tool_info = f" | 🔧 From Tool: '{getattr(msg, 'name', 'unknown')}'"

        print(f"  [{i}] {msg_type:<15} -> \"{truncated_content}\"{tool_info}")
    print("=================================================================================\n")
    # 🟩 CLEAN & TIDY LOG PRINTING END ---


# CORE GRAPH NODE ---
def call_model(state: AgentState) -> Dict[str, Any]:
    """
    Node responsible for running inference against incoming conversation arrays.
    Injects the system prompt cleanly without mutating historical message states.
    """
    # 1. Fetch ALL current messages accumulated by LangGraph in the active run state
    current_messages = state.get("messages", [])

    # Prepend the System Prompt at the beginning of the chain array.
    # We pass it as a clean reference list instead of looping or cloning objects,
    # which preserves the exact schema structure of tool-calling messages.
    # We are Building a clean payload list starting with the core System operational instructions
    # We do NOT slice, clean, or modify the items to protect tool call definitions.
    full_messages = [SystemMessage(content=system_prompt)] + list(current_messages)
    print_llm_invoke_message_for_debugging(full_messages)

    # Execute inference
    response = llm_with_tools.invoke(full_messages)

    # Return a list so LangGraph natively handles state updates
    # LangGraph's message channel state manager will automatically append it to the session history.
    return {"messages": [response]}


def router_edge(state: AgentState) -> Literal["tools", "__end__"]:
    """Conditional edge routine deciding whether to split execution path into parallel tools."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# Build the Graph Blueprint Engine
workflow = StateGraph(AgentState)

# Append Graph Nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools_list))

# Map Graph Transitions
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", router_edge, {"tools": "tools", "__end__": END})
workflow.add_edge("tools", "agent")

# Compile with transactional memory checkpointers
compiled_graph = workflow.compile(checkpointer=MemorySaver())


# 3. SCHEMA FRAMEWORKS & DATAMODELS ---
class ChatRequest(BaseModel):
    message: str
    thread_id: str


# 4. STREAMING ENGINE ENDPOINT INTERFACES ---
# UPDATED STREAMING ROUTE USING NATIVE GRAPH STATE WORKSPACES ---
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Sync current incoming user message down to database log cache
    save_db_message(request.thread_id, "user", request.message)

    # 2. Re-instantiate pristine LangGraph runtime config
    # MemorySaver uses this thread_id to automatically stitch together
    # AIMessage(tool_calls=...) pairs with matching ToolMessages!
    config = {"configurable": {"thread_id": request.thread_id}}

    async def event_generator():
        full_assistant_reply = ""
        custom_type_flag = "text"
        used_tools: List[str] = []

        try:
            # 3. Securely pass ONLY the latest active Human message slice.
            # LangGraph checkpointer will auto-hydrate the full context sequence safely.
            user_input_msg = HumanMessage(
                content=request.message if request.message.strip() else " "
            )

            async for event in compiled_graph.astream_events(
                {"messages": [user_input_msg]}, config=config, version="v2"
            ):
                kind = event["event"]

                # A. Intercept Tool Invocation Hooks for UI Metadata population
                if kind == "on_tool_start":
                    tool_name = event["name"]
                    if tool_name not in used_tools:
                        used_tools.append(tool_name)

                    if tool_name == "request_jira_ticket_form":
                        custom_type_flag = "jira_form"
                        full_assistant_reply = "JIRA_INPUT_FORM"
                    elif tool_name == "execute_create_jira_ticket":
                        custom_type_flag = "jira_ticket"

                # B. Suppress raw JSON objects from leaking to UI streams
                elif kind == "on_tool_end":
                    if custom_type_flag == "jira_ticket":
                        import random

                        ticket_key = f"CARIAD-{random.randint(1000, 9999)}"
                        structured_ticket_data = {
                            "ticket_key": ticket_key,
                            "project": "CARIAD Project Team",
                            "tool_name": "Integrated Platform Engine",
                            "usecase": "Automated Verification Flow",
                            "pdf_url": f"http://localhost:8000/download/Jira_Report_{ticket_key}.pdf",
                        }
                        full_assistant_reply = json.dumps(structured_ticket_data)

                # C. Yield structured streaming token packets cleanly
                elif kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and isinstance(chunk, AIMessageChunk) and chunk.content:
                        # Prevent text leakage if UI visual form elements override text
                        if custom_type_flag in ["jira_form", "jira_ticket"]:
                            continue

                        content_piece = chunk.content

                        # If content is a list (e.g., block format), extract text pieces cleanly
                        if isinstance(content_piece, list):
                            text_extract = ""
                            for block in content_piece:
                                if isinstance(block, dict) and "text" in block:
                                    text_extract += block["text"]
                                elif isinstance(block, str):
                                    text_extract += block
                            content_piece = text_extract
                            
                        # Only proceed if we have a valid string token to concatenate
                        if content_piece and isinstance(content_piece, str):
                            full_assistant_reply += content_piece
                            
                            structured_chunk = {
                                "ai_response": full_assistant_reply,
                                "tools_input": used_tools,
                                "user_question": request.message,
                                "custom_type": custom_type_flag,
                                "is_complete": False,
                            }
                            yield f"data: {json.dumps(structured_chunk)}\n\n"

            # D. Dispatch Terminal Completion Frame
            final_signal = {
                "ai_response": full_assistant_reply,
                "tools_input": used_tools,
                "user_question": request.message,
                "custom_type": custom_type_flag,
                "is_complete": True,
            }
            yield f"data: {json.dumps(final_signal)}\n\n"

            # Write final generation result back to the persistence log layer
            if full_assistant_reply.strip():
                try:
                    save_db_message(
                        request.thread_id,
                        "assistant",
                        full_assistant_reply,
                        custom_type=custom_type_flag,
                    )
                except Exception as db_err:
                    print(f"Database write history error tracking: {db_err}")

        except Exception as e:
            print(f"\n❌ CRITICAL SYSTEM GRAPH STREAM FAILURE: {str(e)}\n")
            error_payload = {
                "ai_response": f" ⚠️ [LangGraph Stream Error: {str(e)}]",
                "tools_input": used_tools,
                "user_question": request.message,
                "custom_type": "text",
                "is_complete": True,
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/history/{thread_id}")
async def get_history_endpoint(thread_id: str):
    """Fetches full historical conversations to reload UI workspaces securely."""
    try:
        history = get_db_history(thread_id)
        formatted_history = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]
        return {"history": formatted_history}
    except Exception as e:
        return {"history": [], "error": str(e)}


@app.delete("/chat/history/{thread_id}")
async def clear_thread_history_endpoint(thread_id: str):
    """Purges chat history records matching a targeted session thread."""
    if not delete_db_history(thread_id=thread_id):
        raise HTTPException(
            status_code=500, detail="Database failure clearing thread logs."
        )
    return {
        "status": "success",
        "message": f"History for thread {thread_id} purged successfully.",
    }


@app.delete("/chat/history")
async def purge_all_history_endpoint():
    """Wipes out every single conversation record globally across the tables."""
    if not delete_db_history():
        raise HTTPException(
            status_code=500, detail="Database failure truncating global logs."
        )
    return {
        "status": "success",
        "message": "Global chat logs purged successfully from database.",
    }


#  Your Dynamic Route for PDF Generation and Download
@app.get("/api/download/{ticket_id}")
async def download_jira_pdf_report(ticket_id: str):
    """
    Checks if a PDF exists locally. If found, returns it instantly.
    If missing, creates it, writes it to disk, and serves it.
    """
    # Clean up input if the browser string sends the file extension or path prefixes
    clean_ticket_id = ticket_id.replace(".pdf", "").replace("Jira_Report_", "")
    
    # Map file locations inside your local cache directory folder
    cache_directory = "generated"
    filename = f"Jira_Report_{clean_ticket_id}.pdf"
    cached_pdf_path = os.path.join(cache_directory, filename)

    # Cache Match Condition: Serve existing file directly from disk
    if os.path.exists(cached_pdf_path):
        print(f"⚡ CACHE HIT: Serving report directly from disk folder: {cached_pdf_path}")
        return FileResponse(
            path=cached_pdf_path, 
            media_type="application/pdf", 
            filename=filename
        )

    # Cache Miss Condition: Trigger PDF layout compiler on the fly
    print(f"⏳ CACHE MISS: Generating report and saving to folder: {cached_pdf_path}")
    
    # Default metadata inputs (can easily be tied to database queries)
    project_info = "CARIAD TP1 Project Infrastructure"
    tool_info = "Integrated Automation Verification Engine Cluster"
    usecase_info = "Automated Diagnostic Flash SW and Macro Verification Run"
    creation_date = "2026-08-16"

    try:
        generate_and_save_jira_pdf(
            target_path=cached_pdf_path,
            ticket_id=clean_ticket_id,
            project_info=project_info,
            tool_info=tool_info,
            usecase_info=usecase_info,
            creation_date=creation_date
        )
    except Exception as pdf_error:
        print(f"❌ PDF Engine Build Failure: {str(pdf_error)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate layout file asset: {str(pdf_error)}")

    # Return the newly generated file
    return FileResponse(
        path=cached_pdf_path, 
        media_type="application/pdf", 
        filename=filename
    )
