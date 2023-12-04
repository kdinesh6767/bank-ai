
import os
from dotenv import load_dotenv

from langchain.globals import set_debug

from langchain.chat_models import ChatOpenAI
from langchain.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType


# Set debug mode
# set_debug(True)

load_dotenv()

class SQLAgent:
    def __init__(self):

        api_key = os.getenv('LANGCHAIN_API_KEY', 'your_default_langchain_api_key')
        DATABASE_USER = os.getenv("DATABASE_USER")
        DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
        DATABASE_DB = os.getenv("DATABASE_DB")
        DATABASE_PORT = os.getenv("DATABASE_PORT")

        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0,
            model_name="gpt-4"
        )

        self.db = SQLDatabase.from_uri(
            f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@localhost:{DATABASE_PORT}/{DATABASE_DB}"
        )

        self.SQL_PREFIX = """
            You are an AI agent tasked with interacting with a SQL database, specifically focusing on customer transaction data. Your role is to create accurate SQL queries based on questions related to transactions for specific customer account IDs. Follow these guidelines:

            Query Types: Construct queries for specific scenarios like the latest transaction, latest debit, credited pension amount, last month's transactions, last credit, and last debit for a given customer account ID.

            Customer Account ID: Include a condition in your queries to filter results based on a specified customer account ID. Use the format: WHERE customer_account_id = '{account_id}'.

            Result Limitation: Use LIMIT 1 for queries fetching the latest transaction for a customer. Adjust the limit as necessary for other queries.

            Order and Timeframe:

            Order results by transaction_date DESC for the latest transactions.
            For last month's transactions, include a WHERE clause filtering records within the previous month's date range and the specific customer account ID.
            Column Selection: Select relevant columns like transaction_id, transaction_date, amount, transaction_type, while ensuring the inclusion of customer_account_id.

            Error Handling: If a "no such table" or "no such column" error occurs, revise the query accordingly.

            Non-DML Operations: Refrain from executing any INSERT, UPDATE, DELETE, or DROP commands.

            Responding to Non-Database Queries: If a question is not database-related, respond with "I don't know". If an answer is not found after three attempts, provide the best possible answer based on the available data.

            Specific Query Examples for Customer Account ID:

            For the latest transaction of a customer: "SELECT transaction_id, transaction_date, amount FROM transactions WHERE customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            For last month's transactions of a customer: "SELECT transaction_id, transaction_date, amount FROM transactions WHERE transaction_date BETWEEN AND customer_account_id = '{account_id}'"
            For the latest debit of a customer: "SELECT transaction_id, transaction_date, amount FROM transactions WHERE transaction_type = 'Debit' AND customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            For the latest credit of a customer: "SELECT transaction_id, transaction_date, amount FROM transactions WHERE transaction_type = 'Credit' AND customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            Your objective is to efficiently and accurately retrieve transaction data specific to a customer's account, adhering to SQL best practices in query construction and execution.
            alway give answer with normal human way and dont add the account id details. Give response in their Language '{lang}'
        """

        

    def get_response(self, query, account, lang):
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        try:
            SQL_PREFIX = self.SQL_PREFIX.format(account_id=2, lang = lang)
            print(SQL_PREFIX)
            agent_executor = create_sql_agent(
                llm=self.llm,
                toolkit=SQLDatabaseToolkit(db=self.db, llm=self.llm),
                top_k = 10,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                prefix=SQL_PREFIX,
            )
            response = agent_executor.run(query)
            return response
        except Exception as e:
            print(e)
            return "An error occurred while processing the request."