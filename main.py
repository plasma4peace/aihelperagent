import os
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import uvicorn

app = FastAPI(title="AI Helper Agent 24/7")

# --- Configuration ---
# These should be set in Environment Variables on Koyeb/Railway
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Skills (Tools) ---
@tool
def python_repl(code: str):
    \"\"\"Execute python code to solve math or data problems.\"\"\"
    try:
        # Warning: In production, use a sandboxed environment
        local_vars = {}
        exec(code, {}, local_vars)
        return str(local_vars)
    except Exception as e:
        return f"Error executing code: {str(e)}"

search = TavilySearchResults(api_key=TAVILY_API_KEY)
tools = [search, python_repl]

# --- Agent Setup ---
# We use Groq Llama3 for speed, Gemini for complex tasks
llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", groq_api_key=GROQ_API_KEY)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a 24/7 autonomous agent. You can search the web and write code. Your goal is to be helpful and provide detailed reports."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- State Management ---
reports = []

class TaskRequest(BaseModel):
    task: str

@app.get("/status")
async def get_status():
    return {"status": "online", "last_reports": reports[-5:]}

@app.post("/run")
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    def execute_agent_task(task_text):
        try:
            result = agent_executor.invoke({"input": task_text})
            reports.append({"task": task_text, "result": result["output"]})
        except Exception as e:
            reports.append({"task": task_text, "error": str(e)})

    background_tasks.add_task(execute_agent_task, request.task)
    return {"message": "Task started in background"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
