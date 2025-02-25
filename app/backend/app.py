from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageTextContent
from azure.ai.projects.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv
from typing import List
import uuid
import json
import asyncio
import os
import time
import sys
sys.path.append(os.path.dirname(__file__))
from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()

# In-memory storage (for demo purposes)
threads = {}     # Maps thread_id to a list of messages
processes = {}   # Maps process_id to its status

# Models for request/response payloads
class ThreadResponse(BaseModel):
    thread_id: str
    messages: List[str] = []

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class Process(BaseModel):
    process_id: str
    status: str

# initialize AIProjectClient
project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.getenv("project_connection_string"))
    
   
def start_long_running_process(feature_spec: str, background_tasks: BackgroundTasks):
    """
    Simulates a long running process (e.g., waiting for email approval).
    After a delay, updates the process status to 'completed'.
    :param feature_spec (str): The feature specification to be processed in dictionary format.
    :return: process_id
    :rtype: str
    """
    process_id = str(uuid.uuid4())
        
    # Start the long running process in the background
    print(f"Starting long running process {process_id}")
    background_tasks.add_task(simulate_long_process, process_id)
    processes[process_id] = "running"
    
    return process_id

agent_functions = FunctionTool([start_long_running_process])
# Check if agent exists, if not, create it
agent_id = os.getenv("agent_id")

def create_agent():
    """
    Creates a new agent with the specified model and instructions.
    """
    project_client.agents.create_agent(
        model=os.getenv("model_deployment"),
        name=os.getenv("agent_name"),
        instructions=SYSTEM_PROMPT,
        tools=agent_functions.definitions,
        headers={"x-ms-enable-preview": "true"}
    )

if agent_id and agent_id !="":
    try:
        agent = project_client.agents.get_agent(agent_id)
        print(f"Agent found, ID: {agent.id}")
    except Exception as e:
        print(f"Error: {e}")
        if isinstance(e, ResourceNotFoundError):
            print('No assistant found, creating one')
            agent = create_agent()
        else:
            raise e
else:
    print('No assistant found, creating one')
    agent = create_agent()

@app.post("/threads", response_model=ThreadResponse)
async def create_thread():
    """
    Creates a new conversation thread.
    """
    #create a new thread
    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")
    thread_id = thread.id
    message_thread = project_client.agents.list_messages(thread_id=thread_id)
    filtered_messages = [
        {'role': message['role'], 'content': message['content'][0]['text']['value']}
        for message in message_thread['data']
    ]
    return ThreadResponse(thread_id=thread_id, messages=filtered_messages)

@app.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """
    Returns the conversation history for a given thread.
    """

    try:
        thread = project_client.agents.get_thread(thread_id=thread_id)
    except Exception as e:
        if isinstance(e, ResourceNotFoundError):
            raise HTTPException(status_code=404, detail="Thread not found")
    
    message_thread = project_client.agents.list_messages(thread_id=thread_id)
    
    filtered_messages = [
        {'role': message['role'], 'content': message['content'][0]['text']['value']}
        for message in message_thread['data']
    ]
    return ThreadResponse(thread_id=thread_id, messages=filtered_messages)

async def simulate_long_process(process_id: str):
    """
    Simulates a long running process (e.g., waiting for email approval).
    After a delay, updates the process status to 'completed'.
    """
    print(f"Simulating long running process {process_id}")
    # Simulate a long running process
    await asyncio.sleep(10)  # 10 seconds delay for simulation
    processes[process_id] = "completed"

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Accepts a chat message from the user and returns an AI response.
    If the message triggers a long running process, it launches it as a background task.
    """
    thread_id = chat_request.thread_id
    message = chat_request.message
    
    try:
        thread = project_client.agents.get_thread(thread_id=thread_id)
    except Exception as e:
        if isinstance(e, ResourceNotFoundError):
            raise HTTPException(status_code=404, detail="Thread not found")
        else:
            raise e
        
    # If the message contains "long process", we start a long running process.
    if "long process" in message.lower():
        process_id = str(uuid.uuid4())
        processes[process_id] = "running"
        
        # Start the long running process in the background
        background_tasks.add_task(simulate_long_process, process_id)
        # Notify the user about the long running process
        response_content = f"Started long running process {process_id} (Status: running)"
        project_client.agents.create_message(thread_id=thread_id, role="assistant", content=response_content)

        return ChatResponse(
            response=response_content
        )
    
    # Send the message to the AI agent
    project_client.agents.create_message(thread_id=thread_id, role="user", content=message)

    run = project_client.agents.create_run(thread_id=thread_id, assistant_id=agent.id)
    
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            if not tool_calls:
                print("No tool calls provided - cancelling run")
                project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                break

            tool_outputs = []
            for tool_call in tool_calls:
                if isinstance(tool_call, RequiredFunctionToolCall):
                    if tool_call.function.name =='start_long_running_process':
                        # Start the long running process in the background
                        reqs = json.loads(tool_call.function.arguments).get('feature_spec')
                        process_id = start_long_running_process("blabla", background_tasks)
                        # Notify the user about the long running process
                        response_content = f"Started long running process {process_id} (Status: running)"
                        tool_outputs.append(
                                ToolOutput(
                                    tool_call_id=tool_call.id,
                                    output=response_content,
                                )
                            )    
                    else:
                        try:
                            print(f"Executing tool call: {tool_call}")
                            output = agent_functions.execute(tool_call)
                            tool_outputs.append(
                                ToolOutput(
                                    tool_call_id=tool_call.id,
                                    output=output,
                                )
                            )
                        except Exception as e:
                            print(f"Error executing tool_call {tool_call.id}: {e}")

            print(f"Tool outputs: {tool_outputs}")
            if tool_outputs:
                project_client.agents.submit_tool_outputs_to_run(
                    thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                )

        print(f"Current run status: {run.status}")
    
    # Get messages from the thread
    messages = project_client.agents.list_messages(thread_id=thread_id)

    # Get the last message from the sender
    last_msg = messages.get_last_text_message_by_role("assistant")

    # Otherwise, simply echo the message (simulate AI response).
    return ChatResponse(response=last_msg.text.value)

@app.get("/processes", response_model=List[Process])
async def get_processes():
    """
    Returns a list of all processes with their current statuses.
    """
    return [Process(process_id=pid, status=status) for pid, status in processes.items()]


