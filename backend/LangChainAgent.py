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
from tools.transaction import TransactionTool
from tools.pension import PensionTool

# Set debug mode
set_debug(True)

# Load environment variables from .env file
load_dotenv()

class LangChainAgent:
    def __init__(self):
        api_key = os.getenv('LANGCHAIN_API_KEY', 'your_default_langchain_api_key')

        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0,
            model_name="gpt-4"
        )

        self.tools = [TransactionTool(), PensionTool()]
        self.account = ""
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Define a prompt template
        prompt = PromptTemplate(
            input_variables=["query"],
            template="""Imagine you are an advanced intelligent bank agent, designed to provide assistance in a highly effective, safe, and friendly manner. Your primary goal is to address users' banking queries with expertise, ensuring their financial information remains secure while maintaining a pleasant and supportive interaction. Consider the user's request: {query}. Utilize your advanced capabilities to analyze and respond to this request, offering detailed, accurate, and user-friendly advice or solutions. Remember to prioritize the user's needs and concerns, demonstrating your commitment to exceptional customer service in the banking sector."""
        )

        # Initialize LLMChain
        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)

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
            response = self.zero_shot_agent(f"{query} for the following account_id = 2")
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
