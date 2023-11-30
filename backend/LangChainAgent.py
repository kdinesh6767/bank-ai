import os
from dotenv import load_dotenv
from sqlalchemy.orm import class_mapper
from database import SessionLocal
from models import Transactions
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.prompts import PromptTemplate, Prompt
from langchain.chains import LLMChain
from langchain.globals import set_debug
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

# Set debug mode
set_debug(True)

# Load environment variables from .env file
load_dotenv()

class LangChainAgent:
    def __init__(self):
        # Replace 'your_api_key' with the environment variable or secure key access method
        api_key = os.getenv('LANGCHAIN_API_KEY', 'your_default_langchain_api_key')

        # Initialize ChatOpenAI
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0,
            model_name="gpt-4"
        )

        self.tools = []
        self.account = ""
        self.memory = ConversationBufferMemory(memory_key="chat_history")


        # Define a prompt template
        prompt = PromptTemplate(
            input_variables=["query"],
            template="""Imagine you are an advanced intelligent bank agent, designed to provide assistance in a highly effective, safe, and friendly manner. Your primary goal is to address users' banking queries with expertise, ensuring their financial information remains secure while maintaining a pleasant and supportive interaction. Consider the user's request: {query}. Utilize your advanced capabilities to analyze and respond to this request, offering detailed, accurate, and user-friendly advice or solutions. Remember to prioritize the user's needs and concerns, demonstrating your commitment to exceptional customer service in the banking sector."""
        )

        # Initialize LLMChain
        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)

        # Define a function to convert a SQLAlchemy model to a dictionary
        def convert_to_dict(model):
            columns = [column.key for column in class_mapper(model.__class__).columns]
            return {column: getattr(model, column) for column in columns}

        # Define a function to get transactions from the database
        def get_transaction(account_id):
            db = SessionLocal()
            try:
                transactions = db.query(Transactions) \
                    .filter(Transactions.account_id == account_id) \
                    .order_by(Transactions.transaction_id) \
                    .offset(0) \
                    .limit(10) \
                    .all()
                json_data = [convert_to_dict(transaction) for transaction in transactions]
                return str(json_data)
            except Exception as e:
                return "An error occurred: " + str(e)
            finally:
                db.close()

        # Define a function to get pension information
        def get_pension(account_id):
            return "ammount: 200, data: 23-11-2020, ammount: 2000, data: 23-11-2022, ammount: 500, data: 23-11-2023, ammount: 200, data: 23-11-2021"

        # Add tools to the agent
        self.tools.append(Tool(
            name='Get Transaction',
            func=get_transaction,
            description='Useful for answering questions about transaction queries, deposit, Withdrawal. Function should have the input account_id.'
        ))

        self.tools.append(Tool(
            name='Get Pension',
            func=get_pension,
            description='Useful for answering questions about user pension queries.'
        ))

        # Initialize the zero-shot agent
        self.zero_shot_agent = initialize_agent(
            agent="conversational-react-description",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=3,
            memory=self.memory
        )

    def get_response(self, query, account):
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        try:
            self.account = 1
            response = self.zero_shot_agent(f"{query} for the following account_id is 1")
            return response
        except Exception as e:
            return "An error occurred while processing the request."
    
    def greet_user(self, lang_code, name):
        chain = self.llm
        messages = [
            SystemMessage(
                content="As you are a bank assistance. Write a greeting message with the name and Language"
            ),
            HumanMessage(
                content=f"Name: {name}, Language: {lang_code}"
        ),
        ]
        response = chain(messages)
        greeting_message = response.content
        return greeting_message
