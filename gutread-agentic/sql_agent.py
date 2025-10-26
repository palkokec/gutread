import os
import logging
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import MCPServerAdapter

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
load_dotenv()

# Configure Ollama 
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "sqlcoder")
sql_tool = "http://127.0.0.1:8001/mcp"

server_params = {
"url": sql_tool,
"transport": "streamable-http"
}

with MCPServerAdapter(server_params) as tools:
  log.debug (f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")

  my_llm = LLM(
      #model="ollama/granite4:micro-h",
      #base_url=ollama_host,
      model="gemini/gemini-2.5-flash",
      streaming=True,
      temperature=0
  )

  agent = Agent(
      role="Guttenberg advisor",
      goal="Retrieve the data from Gutenberg database for user query in natural language",
      backstory="""
      You are a helpful assistant that can query the Gutenberg database. 
      First, you must get the database schema using the get_schema tool. 
      Then, you must use the schema to construct a SQL query to answer the user's question 
      and execute it using the sql_search tool. 
      Finally, you will provide the answer to the user based on the results.""",
      tools=tools,
      verbose=True,
      allow_delegation=False,
      llm=my_llm,
  )
  task1 = Task(
    name="get_schema",
    description="get the database schema using the get_schema tool",
    expected_output="return guttenberg database schema in string format",
    agent=agent,
    tools=[tools["get_schema"]]
    )
  
  task2 = Task(
    name="sql_search",
    description="""
    Use the database schema from task 1 to construct a SQL query that answers this question: 
    '{question}'. 
    Use like clause and case insensitive string comparison rather then strict equal in where clause in sql statement. 
    Then, execute the query using the 'sql_search' tool.
    """,
    expected_output="return array of results from database using the sql_search tool",
    agent=agent,
    context=[task1],
    tools=[tools["sql_search"]]
  )

  task3 = Task(
    name="format_answer",
    description="""
    From the given array of results construct nice list of author, book name and brief summary description maximum 150 charatcers.
    """,
    expected_output="return list of author, book name and brief summary description maximum 150 charatcers",
    agent=agent,
    context=[task2]
  )
  crew = Crew(
      agents=[agent],
      tasks=[task1, task2, task3],
      verbose=True,
      process=Process.sequential,
  )
  result = crew.kickoff(inputs={"question": "Please provide me all the books by author Moody"})
  print(result)