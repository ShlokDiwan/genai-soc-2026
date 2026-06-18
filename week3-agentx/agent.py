from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
import os
import datetime,uuid
from dotenv import load_dotenv

load_dotenv()

llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

@tool 
def get_current_date()->str:
    """Use this tool whenever the user refers to time-sensitive expressions such as

    "today", "yesterday", "this week", "last month", "currently", or asks for

    the present date. This tool returns the current system date so that the agent

    can interpret temporal references accurately.

    Examples:

    - What is today's date?

    - What happened this week?

    - Show me events from yesterday.

    - What are the latest updates as of today?

    - How old is someone as of today?

    This tool only provides the current date and time context. It does not search

    the web or provide factual information beyond the present date. Combine this

    tool with DuckDuckGo Search or Wikipedia when the user's question requires

    both temporal awareness and external knowledge.

    """
    return datetime.date.today().isoformat()

search=DuckDuckGoSearchRun(
    description=(
        """Search the web for real-time information. Use for current news, 
        recent events, live data, or anything published after 2024. 
        Do NOT use for background knowledge, history, or definitions."""
    )
)

wiki=WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(top_k_results=3),
    description=(
        """  
          Look up encyclopaedic information. Use for historical facts, 
          scientific concepts, notable people, and background context. 
          Do NOT use for current events or real-time information. 
        """
    )
)


tools=[search,wiki,get_current_date]

TODAY=datetime.date.today().isoformat()
System_prompt= f""" You are AgentX,a passionate research assistant with access to web search and Wikipedia.
Todays date is {TODAY}.

When answering:
1. Always state which tool provided each piece of information.
2. Structure your final answer as: Introduction -> Key Facts -> Recent Developments -> Conclusion -> Future research directions.
3. If a question asks about something after 2025, use DuckDuckGo, not Wikipedia.
4. If a question asks past events/person/figure/history or info before 2025, use wikipedia and if not found something relevant then you can websearch. 
5. If you don't find good information after 2 searches, say so honestly — don't guess.
"""

memory=MemorySaver()
agent= create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt=System_prompt
)

def run_agent_with_trace(user_input:str,session_id:str)-> tuple[str,str]:
    trace_log=[]
    final_ans=""
    config={
        "configurable":{"thread_id":session_id},
        "recursion_limit":12,
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

    trace_str="/n/n".join(trace_log) if trace_log else "NO tools were called"

    return final_ans,trace_str
    