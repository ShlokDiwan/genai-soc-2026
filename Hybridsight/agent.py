from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from tools_rag import search_documents
from tools_vision import describe_image


llm=ChatGroq(model="openai/gpt-oss-120b")

tools = [
    DuckDuckGoSearchRun(),
    WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    search_documents,
]

SYSTEM_PROMPT = f"""You are HybridSight, an assistant with four tools:
search_documents, DuckDuckGo, describe_image, and Wikipedia.

ROUTING RULES — follow these in order:
1. If the user asks about uploaded documents, "my notes", or "the file",
   use search_documents.
2.If the conversation already contains an image description,
use it to answer image-related questions.dont use your own knowledge about images, only use the description provided.
3. If the user asks about current events or recent news, use DuckDuckGo —
   not Wikipedia.
4. If the user asks a general knowledge question, use Wikipedia.
5. State which tool was used ONLY if a tool was actually called.
6. If no tool returns useful information, say so honestly — don't guess.
"""

memory=MemorySaver()
agent=create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt=SYSTEM_PROMPT,

)       

def run_agent_with_trace(user_input:str,session_id:str)-> tuple[str,str]:
    trace_log=[]
    final_ans=""
    config={
        "configurable":{"thread_id":session_id},
        "recursion_limit":16,
    }

    
    try:
        for event in agent.stream(
            {"messages":[{"role":"user","content":user_input}]},
            config=config,
            stream_mode="values",
        ):
            last=event["messages"][-1]
            if hasattr(last,"tool_calls") and last.tool_calls:
                for tc in last.tool_calls:
                    trace_log.append(
                        f"→ Tool:{tc['name']}\n Input:{tc['args']}"
                    )
            elif last.type=="ai" and not last.tool_calls:
                final_ans=last.content
    except GraphRecursionError:
        final_ans=(
            "⚠️ I couldn't finish within the step limit. "
            "Try rephrasing or narrowing your question."
        )            
    except Exception as e:
        final_ans=f"An error occured: {e}"

    trace_str="\n\n".join(trace_log) if trace_log else "NO tools were called"

    return final_ans,trace_str