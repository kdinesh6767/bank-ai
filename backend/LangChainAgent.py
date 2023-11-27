
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

import os
from dotenv import load_dotenv 

from database import SessionLocal
from models import Transactions
from sqlalchemy.orm import class_mapper
from langchain.globals import set_debug

set_debug(True)

# Load environment variables from .env file
load_dotenv()




class LangChainAgent:
    def __init__(self):
        # Replace 'your_api_key' with the environment variable or secure key access method
        # api_key = os.getenv('OPENAI_API_KEY', 'your_api_key') 
        api_key = os.getenv('LANGCHAIN_API_KEY', 'your_default_langchain_api_key') 
 

        self.llm = ChatOpenAI(
            openai_api_key=api_key,  
            temperature=0,
            model_name="gpt-4"
        )

        self.tools = []

        self.account = ""

        prompt = PromptTemplate(
            input_variables=["query"],
            template="""As an intelligent agent, your role is to assist the user effectively and safely. ... Now, assess the user's request: {query}"""
        )

        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)

   
          
        def convert_to_dict(model):
            columns = [column.key for column in class_mapper(model.__class__).columns]
            return {column: getattr(model, column) for column in columns}

        def getTransaction(accountId):
            db = SessionLocal()
            try:
                # Perform your database operations here
                transactions = db.query(Transactions) \
                    .filter(Transactions.account_id == accountId) \
                    .order_by(Transactions.transaction_id) \
                    .offset(0) \
                    .limit(10) \
                    .all()

                jsonData = [convert_to_dict(transaction) for transaction in transactions]
                return str(jsonData)
            except Exception as e:
                # Handle exceptions, log errors, etc.
                return "An error occurred: " + str(e)
            finally:
                # Close the session
                db.close()

        def getPension(accountId):
            return "ammount: 200, data: 23-11-2020, ammount: 2000, data: 23-11-2022, ammount: 500, data: 23-11-2023, ammount: 200, data: 23-11-2021"

        # Add tools to the agent
        self.tools.append(Tool(
            name='Get Transaction',
            func=getTransaction,
            description='useful for when you need to answer question about the transaction query. function should have following inputs limit(default value 30).'
        ))

        self.tools.append(Tool(
            name='Get Pension',
            func=getPension,
            description='useful for when you need to answer question about the user pension query'
        ))

        self.zero_shot_agent = initialize_agent(
            agent="zero-shot-react-description",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=3
        )

    def get_response(self, query, account):
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        try:
            self.account = account
            print("-----------------------------------------------")
            # self.getTransaction1()
            response = self.zero_shot_agent(query)
            return response 
        except Exception as e:
            # Here, you would ideally log the exception 'e' for debugging
            return "An error occurred while processing the request."
