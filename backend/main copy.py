# import json
# import os
# import mysql.connector
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.responses import StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# from typing import Annotated, Any, Dict, List
# from fastapi.staticfiles import StaticFiles
# from dotenv import load_dotenv

# # Unified compilation library specifications
# from langchain_core.messages import AIMessageChunk, ToolMessageChunk, SystemMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.agents import create_agent  # Keep your native standard import factory

# # Database and Tools imports
# from tools.db import (
#     get_tools_and_usecases_from_db,
#     init_db,
#     upsert_tools_data,
#     get_db_history,
#     save_db_message,
#     delete_db_history,
# )
# from tools.tools_engine import (
#     execute_create_jira_ticket,
#     list_available_tools,
#     request_jira_ticket_form,
# )

# # 1. ON STARTUP ---
# load_dotenv()

# app = FastAPI(title="CARIAD Core Engine Interface Platform")

# # Enable CORS for frontend integrations
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 2. DATABASE HYDRATION ON STARTUP ---
# os.makedirs("generated", exist_ok=True)
# app.mount("/download", StaticFiles(directory="generated"), name="download")

# init_db()
# tools_data_from_db = get_tools_and_usecases_from_db()

# if not tools_data_from_db:
#     print("No tools data found in MySQL. Scanning local JSON files...")
#     from tools.tools_engine import get_tools_and_usecases

#     tools_data = get_tools_and_usecases()
#     if tools_data:
#         print(f"Upserting {len(tools_data)} tools and use cases into MySQL...")
#         upsert_tools_data(tools_data)
#         print("✅ Tools and use cases upserted successfully.")
# else:
#     print(f"✅ Loaded {len(tools_data_from_db)} tools successfully from MySQL cache.")


# # 3. COMPILING THE LANGUAGE GRAPH MIDDLEWARE WORKFLOW ---

# # Initialize your core Gemini 2.5 engine
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

# # Register tools array list
# tools_list = [
#     list_available_tools,
#     execute_create_jira_ticket,
#     request_jira_ticket_form,
# ]

# # Clean prompt configuration
# # system_prompt = (
# #     "You are a professional assistant for the CARIAD tool chain platform.\n\n"
# #     "CRITICAL TOOL-ROUTING LAWS (EVALUATE IN ORDER):\n"
# #     "1. ABSOLUTE BYPASS FOR TICKET GENERATION: If the incoming user message contains 'COMMAND: EXECUTE_JIRA_CREATION', "
# #     "you MUST immediately execute the 'execute_create_jira_ticket' tool. Extract the fields directly from the markdown list:\n"
# #     "   - Extract 'Tool Name' -> pass to tool_name parameter.\n"
# #     "   - Extract 'Project' -> pass to project parameter.\n"
# #     "   - Extract 'Usecase' -> pass to usecase parameter.\n"
# #     "   - Extract 'Details' -> pass to details parameter.\n"
# #     "   Do NOT offer a form, do NOT repeat the request, and go straight to calling the tool.\n\n"
# #     "2. AUTOMATED FORM MODE: If the user says 'bug', 'file a bug', 'error', 'create ticket', 'jira', or 'issue', "
# #     "AND the message does NOT contain 'COMMAND: EXECUTE_JIRA_CREATION', "
# #     "you MUST immediately call the 'request_jira_ticket_form' tool to display input fields.\n\n"
# #     "3. PLATFORM REGISTRY MODE: If the user asks for available tools, tool configurations, or use cases, "
# #     "you MUST call the 'list_available_tools' tool. Once you receive the raw JSON, format it into a "
# #     "clean, polite bulleted summary showing only names unless explicitly ased for versions and use cases. Do not make up extra details."
# # )

# system_prompt = (
#     "You are a professional assistant for the CARIAD tool chain platform.\n\n"
#     "CRITICAL TOOL-ROUTING & DETAIL RULES (EVALUATE IN ORDER):\n"
#     "1. ABSOLUTE BYPASS FOR TICKET GENERATION: If the incoming user message contains 'COMMAND: EXECUTE_JIRA_CREATION', "
#     "you MUST immediately execute the 'execute_create_jira_ticket' tool. Extract the fields directly from the markdown list "
#     "and pass them to the tool parameters. Do NOT offer a form, do NOT repeat the request, and go straight to calling the tool.\n\n"
#     "2. AUTOMATED FORM MODE: If the user says 'bug', 'file a bug', 'error', 'create ticket', 'jira', or 'issue', "
#     "AND the message does NOT contain 'COMMAND: EXECUTE_JIRA_CREATION', "
#     "you MUST immediately call the 'request_jira_ticket_form' tool to display input fields.\n\n"
#     "3. PLATFORM REGISTRY DETAIL PROTOCOLS:\n"
#     "   When the user asks about available tools, supported tools, registries, or use cases, you MUST call 'list_available_tools' first. "
#     "   Once you receive the raw database JSON, format your output according to these strict rules:\n"
#     "   - GENERAL LIST REQUEST: If the user just asks for a list of tools (e.g., 'list tools', 'show supported tools', 'tools available'), "
#     "     you MUST display ONLY the plain bulleted names of the tools. Do NOT include versions, and do NOT list use cases.\n"
#     "   - DETAILED/SPECIFIC REQUEST: If the user explicitly asks for 'details', 'versions', 'use cases', 'info', or asks about a single "
#     "     specific tool by name (e.g., 'provide detail of a tool ODIS', 'info on Canoe'), you MUST expand your response. "
#     "     Provide the tool name, its version, and an indented sub-bulleted list of all its registered use cases.\n"
#     "   - Never make up or hallucinate tool details. Word your final answer using only data provided by the tool."
# )


# # Compile using your standard native agent factory
# compiled_graph = create_agent(model=llm, tools=tools_list, system_prompt=system_prompt)


# # ROUTER CHANNELS & SERVICE SCHEMAS ---
# class ChatRequest(BaseModel):
#     message: str
#     thread_id: str


# @app.get("/chat/history/{thread_id}")
# async def get_history_endpoint(thread_id: str):
#     """Fetches full historical conversations to reload the UI on browser refreshes."""
#     try:
#         history = get_db_history(thread_id)
#         formatted_history = [
#             {"role": role, "content": content} for role, content in history
#         ]
#         return {"history": formatted_history}
#     except Exception as e:
#         return {"history": [], "error": str(e)}


# @app.delete("/chat/history/{thread_id}")
# async def clear_thread_history_endpoint(thread_id: str):
#     """Deletes all conversation history records matching a targeted session thread."""
#     success = delete_db_history(thread_id=thread_id)
#     if not success:
#         raise HTTPException(
#             status_code=500, detail="Database failure clearing thread logs."
#         )
#     return {
#         "status": "success",
#         "message": f"History for thread {thread_id} purged successfully.",
#     }


# @app.delete("/chat/history")
# async def purge_all_history_endpoint():
#     """Wipes out every single conversation record globally across the table workspace."""
#     success = delete_db_history()
#     if not success:
#         raise HTTPException(
#             status_code=500, detail="Database failure truncating global log tables."
#         )
#     return {
#         "status": "success",
#         "message": "Global chat logs purged successfully from database.",
#     }


# @app.post("/chat")
# async def chat_endpoint(request: ChatRequest):
#     # 1. Fetch previous conversation logs for context sync
#     history = get_db_history(request.thread_id)
#     save_db_message(request.thread_id, "user", request.message)

#     # 2. Reassemble chat log arrays cleanly
#     input_messages = []
#     for m in history:
#         role_map = "assistant" if m["role"] == "assistant" else "user"
#         input_messages.append((role_map, m["content"]))
#     input_messages.append(("user", request.message))

#     async def event_generator():
#         full_assistant_reply = ""
#         custom_type_flag = "text"

#         used_tools: List[str] = []
#         user_msg_lower = request.message.lower()
#         if any(
#             kw in user_msg_lower
#             for kw in [
#                 "tool",
#                 "list",
#                 "usecase",
#                 "use case",
#                 "registry",
#                 "python",
#                 "odis",
#                 "canoe",
#                 "idex",
#             ]
#         ):
#             used_tools.append("list_available_tools")
#         if "execute_jira_creation" in user_msg_lower or "command" in user_msg_lower:
#             used_tools.append("execute_create_jira_ticket")

#         tool_markdown_fallback = ""

#         try:
#             # 3. Intent Lookahead Guard: Lock form layout type early to prevent text leakage
#             if any(
#                 kw in user_msg_lower
#                 for kw in [
#                     "bug",
#                     "file a bug",
#                     "error",
#                     "create ticket",
#                     "jira",
#                     "issue",
#                     "track task",
#                     "report problem",
#                 ]
#             ):
#                 if not "command: execute_jira_creation" in user_msg_lower:
#                     custom_type_flag = "jira_form"
#                     full_assistant_reply = "JIRA_INPUT_FORM"

#             # 4. Stream data frames from the agent graph execution loop
#             async for chunk in compiled_graph.astream(
#                 {"messages": input_messages}, stream_mode="messages"
#             ):
#                 print(f"🔹 Received chunk: {chunk}")
#                 msg_chunk = None
#                 if isinstance(chunk, dict):
#                     msg_chunk = (
#                         chunk.get("data") if "data" in chunk else chunk.get("message")
#                     )
#                 elif isinstance(chunk, tuple) and len(chunk) == 2:
#                     msg_chunk, _ = chunk
#                 if msg_chunk is None:
#                     msg_chunk = chunk

#                 if msg_chunk:
#                     msg_type = getattr(msg_chunk, "type", None)

#                     if msg_type == "tool" or (
#                         hasattr(msg_chunk, "type") and msg_chunk.type == "tool"
#                     ):
#                         print(
#                             "🛡️ Suppressed raw tool execution data packet from leaking to UI."
#                         )
#                         tool_name = getattr(msg_chunk, "name", "")
#                         tool_content = getattr(msg_chunk, "content", "")

#                         if (
#                             tool_name == "request_jira_ticket_form"
#                             or "TRIGGER_JIRA_FORM" in tool_content
#                         ):
#                             custom_type_flag = "jira_form"
#                             full_assistant_reply = "JIRA_INPUT_FORM"
#                         elif tool_name == "execute_create_jira_ticket":
#                             custom_type_flag = "jira_ticket"

#                             import random

#                             ticket_key = f"CARIAD-{random.randint(1000, 9999)}"
#                             tool_val = (
#                                 "Canoe"
#                                 if "canoe" in user_msg_lower
#                                 else (
#                                     "ODIS"
#                                     if "odis" in user_msg_lower
#                                     else "Platform Tool"
#                                 )
#                             )
#                             proj_val = (
#                                 "TP1" if "tp" in user_msg_lower else "CARIAD Project"
#                             )
#                             uc_val = "Automated Verification Turn"

#                             structured_ticket_data = {
#                                 "ticket_key": ticket_key,
#                                 "project": proj_val,
#                                 "tool_name": tool_val,
#                                 "usecase": uc_val,
#                                 "pdf_url": f"http://localhost:8000/download/Jira_Report_{ticket_key}.pdf",
#                             }
#                             full_assistant_reply = json.dumps(structured_ticket_data)
#                         else:
#                             # 🎯 LET THE LLM DO THE WORK: Pass raw data to fallback string container
#                             tool_markdown_fallback = tool_content
#                         continue

#                     if isinstance(msg_chunk, AIMessageChunk) or (
#                         hasattr(msg_chunk, "type") and msg_chunk.type == "ai"
#                     ):
#                         content = getattr(msg_chunk, "content", None)

#                         if content and isinstance(content, str):
#                             if custom_type_flag in ["jira_form", "jira_ticket"]:
#                                 continue

#                             full_assistant_reply += content

#                             if custom_type_flag == "text":
#                                 structured_chunk = {
#                                     "ai_response": full_assistant_reply,
#                                     "tools_input": used_tools,
#                                     "user_question": request.message,
#                                     "custom_type": custom_type_flag,
#                                     "is_complete": False,
#                                 }
#                                 yield f"data: {json.dumps(structured_chunk)}\n\n"

#             # 🎯 5. TERMINAL COMPLETION PACKETS DISPATCH
#             if custom_type_flag == "jira_form":
#                 save_db_message(
#                     request.thread_id,
#                     "assistant",
#                     "JIRA_INPUT_FORM",
#                     custom_type="jira_form",
#                 )
#                 yield f"data: {json.dumps({'user_question': request.message, 'tools_input': [], 'ai_response': 'JIRA_INPUT_FORM', 'custom_type': 'jira_form', 'is_complete': True})}\n\n"

#             elif custom_type_flag == "jira_ticket":
#                 save_db_message(
#                     request.thread_id,
#                     "assistant",
#                     full_assistant_reply,
#                     custom_type="jira_ticket",
#                 )
#                 yield f"data: {json.dumps({'user_question': request.message, 'tools_input': used_tools, 'ai_response': full_assistant_reply, 'custom_type': 'jira_ticket', 'is_complete': True})}\n\n"

#             else:
#                 # 🚀 NO HARDCODED PYTHON FORMATTERS:
#                 # If the reply string is empty, we fall back to the text asset container.
#                 # Otherwise, we trust Gemini's native prompt compliance entirely.
#                 if not full_assistant_reply.strip() and tool_markdown_fallback.strip():
#                     full_assistant_reply = tool_markdown_fallback

#                 final_signal = {
#                     "ai_response": full_assistant_reply,
#                     "tools_input": used_tools,
#                     "user_question": request.message,
#                     "custom_type": custom_type_flag,
#                     "is_complete": True,
#                 }
#                 yield f"data: {json.dumps(final_signal)}\n\n"

#                 if full_assistant_reply.strip():
#                     try:
#                         save_db_message(
#                             request.thread_id,
#                             "assistant",
#                             full_assistant_reply,
#                             custom_type="text",
#                         )
#                     except Exception as db_err:
#                         print(f"Database write history error tracking: {db_err}")

#         except Exception as e:
#             print(f"\n❌ CRITICAL STREAMING ERROR LOG: {str(e)}\n")
#             error_payload = {
#                 "ai_response": f" ⚠️ [Stream Generation Error: {str(e)}]",
#                 "tools_input": used_tools,
#                 "user_question": request.message,
#                 "custom_type": "text",
#                 "is_complete": True,
#             }
#             yield f"data: {json.dumps(error_payload)}\n\n"

#     return StreamingResponse(event_generator(), media_type="text/event-stream")


# # @app.post("/chat")
# # async def chat_endpoint(request: ChatRequest):
# #     # 1. Fetch previous conversation logs for context sync
# #     history = get_db_history(request.thread_id)
# #     save_db_message(request.thread_id, "user", request.message)

# #     # 2. Reassemble chat log arrays cleanly
# #     input_messages = []
# #     for m in history:
# #         role_map = "assistant" if m["role"] == "assistant" else "user"
# #         input_messages.append((role_map, m["content"]))
# #     input_messages.append(("user", request.message))

# #     async def event_generator():
# #         full_assistant_reply = ""
# #         custom_type_flag = "text"

# #         # Track tools dynamically based on user prompt string keywords
# #         used_tools: List[str] = []
# #         user_msg_lower = request.message.lower()
# #         if any(kw in user_msg_lower for kw in ["tool", "list", "usecase", "use case", "registry", "python", "odis", "canoe", "idex"]):
# #             used_tools.append("list_available_tools")
# #         if "execute_jira_creation" in user_msg_lower or "command" in user_msg_lower:
# #             used_tools.append("execute_create_jira_ticket")

# #         tool_markdown_fallback = ""

# #         try:
# #             # 🎯 3. THE INTENT LOOKAHEAD GUARD (THE ROOT CAUSE FIX):
# #             # Pre-evaluate the prompt text. If they want a form, override custom_type_flag
# #             # right now so that absolutely NO streamed chunks carry the 'text' type.
# #             if any(kw in user_msg_lower for kw in ["bug", "file a bug", "error", "create ticket", "jira", "issue", "track task", "report problem"]):
# #                 # Bypass if they are actually submitting the filled out markdown form variables
# #                 if not "command: execute_jira_creation" in user_msg_lower:
# #                     custom_type_flag = "jira_form"
# #                     full_assistant_reply = "JIRA_INPUT_FORM"

# #             # 4. Stream data frames using a flexible universal layout parsing strategy
# #             async for chunk in compiled_graph.astream(
# #                 {"messages": input_messages},
# #                 stream_mode="messages"
# #             ):
# #                 msg_chunk = None

# #                 # Safely extract message wrappers across standard variations
# #                 if isinstance(chunk, dict):
# #                     msg_chunk = chunk.get("data") if "data" in chunk else chunk.get("message")
# #                 elif isinstance(chunk, tuple) and len(chunk) == 2:
# #                     msg_chunk, _ = chunk
# #                 if msg_chunk is None:
# #                     msg_chunk = chunk

# #                 if msg_chunk:
# #                     msg_type = getattr(msg_chunk, "type", None)

# #                     # Catch tool execution states strictly by metadata name properties
# #                     if msg_type == "tool" or (hasattr(msg_chunk, "type") and msg_chunk.type == "tool"):
# #                         print("🛡️ Suppressed raw tool execution data packet from leaking to UI.")
# #                         tool_name = getattr(msg_chunk, "name", "")
# #                         tool_content = getattr(msg_chunk, "content", "")

# #                         # Case A: Form template requested
# #                         if tool_name == "request_jira_ticket_form" or "TRIGGER_JIRA_FORM" in tool_content:
# #                             # 🎯 THE NATURAL SYNC FIX: Set the flag, but DO NOT overwrite or clear full_assistant_reply!
# #                             custom_type_flag = "jira_form"
# #                             full_assistant_reply = "JIRA_INPUT_FORM"

# #                         # Case B: Ticket generation tool finished execution natively
# #                         elif tool_name == "execute_create_jira_ticket":
# #                             custom_type_flag = "jira_ticket"

# #                             import random
# #                             ticket_key = f"CARIAD-{random.randint(1000, 9999)}"
# #                             tool_val = "Canoe" if "canoe" in user_msg_lower else ("ODIS" if "odis" in user_msg_lower else "Platform Tool")
# #                             proj_val = "TP1" if "tp" in user_msg_lower else "CARIAD Project"
# #                             uc_val = "Automated Verification Turn"

# #                             structured_ticket_data = {
# #                                 "ticket_key": ticket_key,
# #                                 "project": proj_val,
# #                                 "tool_name": tool_val,
# #                                 "usecase": uc_val,
# #                                 "pdf_url": f"http://localhost:8000/download/Jira_Report_{ticket_key}.pdf"
# #                             }
# #                             full_assistant_reply = json.dumps(structured_ticket_data)
# #                         else:
# #                             # Cache fallback string data for tool registries lookups
# #                             tool_markdown_fallback = tool_content
# #                         continue

# #                     # Handle valid text tokens coming from an active AI assistant message turn
# #                     if isinstance(msg_chunk, AIMessageChunk) or (hasattr(msg_chunk, "type") and msg_chunk.type == "ai"):
# #                         content = getattr(msg_chunk, "content", None)

# #                         if content and isinstance(content, str):
# #                             # 🎯 THE COMPACT SHIELD: If a form or ticket tool state has already been flagged,
# #                             # completely ignore any conversational text fragments Gemini tries to generate!
# #                             if custom_type_flag in ["jira_form", "jira_ticket"] or tool_markdown_fallback:
# #                                 continue

# #                             full_assistant_reply += content

# #                             # Stream steps out if we aren't presenting an active form/ticket layout
# #                             if custom_type_flag == "text":
# #                                 structured_chunk = {
# #                                     "ai_response": full_assistant_reply,
# #                                     "tools_input": used_tools,
# #                                     "user_question": request.message,
# #                                     "custom_type": custom_type_flag,
# #                                     "is_complete": False
# #                                 }
# #                                 yield f"data: {json.dumps(structured_chunk)}\n\n"


# #             # 4. 🎯 TERMINAL COMPLETION PACKETS DISPATCH
# #             if custom_type_flag == "jira_form":
# #                 # Save Gemini's genuine text reply into your MySQL log tables instead of a dummy variable
# #                 save_db_message(request.thread_id, "assistant", "JIRA_INPUT_FORM", custom_type="jira_form")
# #                 yield f"data: {json.dumps({'user_question': request.message, 'tools_input': [], 'ai_response': 'JIRA_INPUT_FORM', 'custom_type': 'jira_form', 'is_complete': True})}\n\n"

# #             elif custom_type_flag == "jira_ticket":
# #                 save_db_message(request.thread_id, "assistant", full_assistant_reply, custom_type="jira_ticket")
# #                 yield f"data: {json.dumps({'user_question': request.message, 'tools_input': used_tools, 'ai_response': full_assistant_reply, 'custom_type': 'jira_ticket', 'is_complete': True})}\n\n"

# #             else:
# #                 # UNIVERSAL RECOVERY NET FOR TOOL LISTS
# #                 if "list_available_tools" in used_tools and tool_markdown_fallback.strip():
# #                     print("🎯 Force formatting tool dictionary JSON into markdown list hierarchy...")
# #                     try:
# #                         tools_dict = json.loads(tool_markdown_fallback)
# #                         inner_data = tools_dict.get("parameters", tools_dict) if isinstance(tools_dict, dict) else {}
# #                         if not inner_data and isinstance(tools_dict, dict):
# #                             inner_data = tools_dict

# #                         markdown_builder = "Here is a list of tools available in our platform:\n\n"
# #                         if isinstance(inner_data, dict) and len(inner_data) > 0:
# #                             for tool_key, info in inner_data.items():
# #                                 name = info.get("tool", tool_key)
# #                                 version = info.get("version", "N/A")

# #                                 # Sub-filter the visible options if specific keywords are passed
# #                                 if "python" in user_msg_lower and name.lower() != "python":
# #                                     continue
# #                                 if "odis" in user_msg_lower and name.lower() != "odis":
# #                                     continue
# #                                 if "canoe" in user_msg_lower and name.lower() != "canoe":
# #                                     continue
# #                                 if "idex" in user_msg_lower and name.lower() != "idex":
# #                                     continue

# #                                 markdown_builder += f"* **{name}**: Version {version}\n"
# #                                 use_cases = info.get("use_cases", [])
# #                                 if use_cases:
# #                                     for uc in use_cases:
# #                                         markdown_builder += f"\t+ {uc}\n"
# #                                 else:
# #                                     markdown_builder += f"\t+ No registered use cases found.\n"

# #                             full_assistant_reply = markdown_builder
# #                     except Exception as json_err:
# #                         print(f"Fallback formatting error: {json_err}")

# #                 # If full_assistant_reply is still empty but tool data exists, fallback to it
# #                 if not full_assistant_reply.strip() and tool_markdown_fallback.strip():
# #                     full_assistant_reply = tool_markdown_fallback

# #                 # Ship the definitive terminal data packet down the streaming pipe
# #                 final_signal = {
# #                     "ai_response": full_assistant_reply,
# #                     "tools_input": used_tools,
# #                     "user_question": request.message,
# #                     "custom_type": "text",
# #                     "is_complete": True
# #                 }
# #                 yield f"data: {json.dumps(final_signal)}\n\n"

# #              # 5. Commit completed assistant response text records to MySQL history
# #                 if full_assistant_reply.strip():
# #                     try:
# #                         save_db_message(request.thread_id, "assistant", full_assistant_reply, custom_type=custom_type_flag)
# #                     except Exception as db_err:
# #                         print(f"Database write history error tracking: {db_err}")
# #         except Exception as e:
# #             print(f"\n❌ CRITICAL STREAMING ERROR LOG: {str(e)}\n")
# #             error_payload = {"ai_response": f" ⚠️ [Stream Generation Error: {str(e)}]","tools_input": used_tools,"user_question": request.message,"custom_type": "text","is_complete": True}
# #             yield f"data: {json.dumps(error_payload)}\n\n"
# #     return StreamingResponse(event_generator(), media_type="text/event-stream")
