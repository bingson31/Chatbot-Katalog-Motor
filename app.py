# app.py

import streamlit as st
import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from database_tools import text_to_sql, init_database, get_database_info

# --- 1. Page Configuration and Title ---
st.title("🏍️ Bike Catalog Chatbot")
st.caption("Ajukan pertanyaan tentang data katalog sepeda motor bekas sesuai dengan data yang ada di tabel")

# --- 2. Sidebar for Settings ---
with st.sidebar:
    st.subheader("Settings")
    google_api_key = st.text_input("Google AI API Key", type="password")
    reset_button = st.button("Reset Conversation", help="Clear all messages and start fresh")

# --- 3. Initialize Database Automatically ---
DB_PATH = "bike_catalog.db"
if not os.path.exists(DB_PATH):
    with st.spinner("Setting up the database from Excel file..."):
        result = init_database()
        st.toast(result)

# --- 4. API Key and Excel Preview ---
if not google_api_key:
    st.info("Please add your Google AI API key in the sidebar to start chatting.", icon="🗝️")
    st.stop()

# Tampilkan preview file Excel setelah input API key
excel_path = "catalog-bike.xlsx"
if os.path.exists(excel_path):
    st.subheader("📊 Preview: Catalog Bike")
    try:
        df = pd.read_excel(excel_path)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
else:
    st.warning("File 'catalog-bike.xlsx' not found.")

# --- 5. LangChain Tools ---
@tool
def execute_sql(sql_query: str):
    """Execute a SQL query against the bike catalog database."""
    result = text_to_sql(sql_query)
    return result

@tool
def get_schema_info():
    """Get schema and sample data to help build SQL queries."""
    return get_database_info()

# --- 6. Create LangGraph Agent ---
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.2
        )

        st.session_state.agent = create_react_agent(
            model=llm,
            tools=[get_schema_info, execute_sql],
            prompt="""
You are a helpful assistant that can answer questions about a motorcycle catalog using SQL.

Steps:
1. Use get_schema_info tool to understand the database structure.
2. Write SQL query based on user question and database schema.
3. Use execute_sql to get results.
4. Return results in simple explanation (do NOT show SQL query).

Rules:
- Use SQLite syntax
- Don't show SQL to the user
- Don't ask user to write SQL
- Explain any SQL errors if they occur
            """
        )

        st.session_state._last_key = google_api_key
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Invalid API Key or configuration error: {e}")
        st.stop()

# --- 7. Chat History Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("agent", None)
    st.session_state.pop("messages", None)
    st.rerun()

# --- 8. Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 9. Handle Chat Input ---
prompt = st.chat_input("Ask about the motorcycle catalog...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        with st.spinner("Thinking..."):
            response = st.session_state.agent.invoke({"messages": messages})

            answer = "I'm sorry, I couldn't generate a response."

            for msg in reversed(response["messages"]):
                if isinstance(msg, AIMessage):
                    if isinstance(msg.content, str):
                        answer = msg.content
                        break
                    elif isinstance(msg.content, list):
                        try:
                            answer = "\n".join(str(part) for part in msg.content if isinstance(part, str))
                            break
                        except:
                            continue
                elif hasattr(msg, "content") and isinstance(msg.content, str):
                    answer = msg.content
                    break

    except Exception as e:
        answer = f"An error occurred: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


