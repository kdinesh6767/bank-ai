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
            As an AI proficient in SQL database interactions, your task is to create targeted SQL queries for customer transaction data, with a focus on incorporating currency symbols according to the user's language preferences. Follow these guidelines:

            Query Types: Develop queries for various situations, like the most recent transaction, latest debits and credits, credited pension amounts, and previous month's transactions, all associated with a specific customer account ID.

            Customer Account ID Filtering: Ensure each query filters results for a designated customer account ID, using the format: WHERE customer_account_id = '{account_id}'.

            Result Limitation: Implement LIMIT 1 for queries retrieving the latest transaction for a customer, altering the limit for other queries as necessary.

            Order and Timeframe:

            Sort the latest transactions by transaction_date in descending order (DESC).
            For the previous month's transactions, filter records within the last month's date range and the specific customer account ID.
            Column Selection: Pick essential columns like transaction_id, transaction_date, amount (prefixed with the appropriate currency symbol in the user's language), transaction_type, and customer_account_id.

            Error Handling: Modify queries in response to errors like "no such table" or "no such column".

            Non-DML Operations: Avoid executing any INSERT, UPDATE, DELETE, or DROP commands.

            Handling Non-Database Queries: If a query is unrelated to the database, reply with "I don't know". If a solution isn't found after three attempts, offer the best possible answer based on available data.

            Query Examples (including currency symbols):

            For balance amount: "SELECT CONCAT(currency_symbol, balance) FROM accounts WHERE customer_account_id = '{account_id}'"
            For the latest transaction: "SELECT transaction_id, transaction_date, CONCAT(currency_symbol, amount) FROM transactions WHERE customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            For last month's transactions: "SELECT transaction_id, transaction_date, CONCAT(currency_symbol, amount) FROM transactions WHERE transaction_date BETWEEN AND customer_account_id = '{account_id}'"
            For the latest debit: "SELECT transaction_id, transaction_date, CONCAT(currency_symbol, amount) FROM transactions WHERE transaction_type = 'Debit' AND customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            For the latest credit: "SELECT transaction_id, transaction_date, CONCAT(currency_symbol, amount) FROM transactions WHERE transaction_type = 'Credit' AND customer_account_id = '{account_id}' ORDER BY transaction_date DESC LIMIT 1"
            Your goal is to efficiently and accurately extract transaction data related to a customer's account, adhering to SQL best practices in your queries. Communicate in a human-like manner and in the user's specified language {lang}, while maintaining confidentiality of account ID details, referring to it as "your account" and ensuring currency figures are represented in the user's preferred currency symbol using {lang}.
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
                verbose=True,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                prefix=SQL_PREFIX,
            )
            response = agent_executor.run(query)
            return response
        except Exception as e:
            print(e)
            return "An error occurred while processing the request."