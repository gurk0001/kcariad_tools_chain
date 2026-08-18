from langchain_core.tools import tool
from tools.tools_engine import get_tools_and_usecases_from_db

@tool
def list_available_tools() -> str:
    """
    Useful when the user asks to see a list of tools, what tools are supported, 
    or wants to know about the use cases associated with different tools in the system.
    Returns a structured dictionary string containing tool IDs, names, versions, and use cases.
    """
    try:
        # Fetch the cached data from the database
        data = get_tools_and_usecases_from_db(force_refresh=False)
        if not data:
            return "No tools data found in the system database."
        
        # Return the data as a clean dictionary representation for the LLM to read
        return str(data)
    except Exception as e:
        return f"Error retrieving tools from the database: {str(e)}"