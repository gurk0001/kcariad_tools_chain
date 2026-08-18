### Create and Activate a Virtual Environmentbash

1. Create a local environment folder named 'venv'
```
python3 -m venv venv
```

2. Activate the virtual environment sandbox
```
source venv/bin/activate
```

(Your terminal prompt will change to show (venv) at the beginning of the line, indicating it is safely isolated).

### Install the App Libraries

Now that your sandbox is active, running pip safely targets only this folder and will no longer block your installs:

```
pip install fastapi langgraph langchain langchain-ollama mysql-connector-python sqlalchemy uvicorn 'psycopg[binary]' reportlab langchain-google-genai python-dotenv
```

### Run the Server
With your dependencies cleanly resolved, boot up your API using your local package router:

```
python -m uvicorn main:app --reload --port 8000
```

### Application

#### State Information
The application needs to track four distinct states:
1. `text`: Standard conversational AI response Markdown layouts.
2. `jira_form`: The interactive inputs context pane.
3. `jira_ticket`: A premium Atlassian issue status visual card layout.
4. `pdf_download`: A layout component featuring a clickable file link to download data mapped to a structural PDF grid.

#### Verify States
Verify the Interface Pipeline Action Flow:Chat: You chat normally. 
1. If you say `"file a bug" or "create a jira ticket"`, the form immediately spawns inside the bubble timeline channel.
2. `JIRA Form Filling:` The interactive JiraTicketForm displays entry text boxes securely inline inside your view list panel window.
3. `Display JIRA Ticket:` Clicking save passes parameter values to your backend, updates the tables, and spits out a crisp blue JiraTicketCard showing your confirmation codes.
4. `Display PDF Table Format:` Clicking the green button on the ticket card dynamically spawns the PdfDownloadCard grid table matrix framework directly underneath, exposing a fast click accessor download asset link pointing to your local generated .pdf archive.