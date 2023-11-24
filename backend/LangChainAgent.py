from sqlalchemy import select
from fastapi import Depends
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal, init_db
from models import Customers
from models import Transactions
from models import Chalan
from num2words import num2words
from models import Accounts
from pydantic import BaseModel 
from datetime import datetime 
from decimal import Decimal
from sqlalchemy.orm import class_mapper
from langchain.globals import set_debug

set_debug(True)





class LangChainAgent:
    def __init__(self):
        # Replace 'your_api_key' with the environment variable or secure key access method
        # api_key = os.getenv('OPENAI_API_KEY', 'your_api_key') 
        api_key = ""

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

        # def getTransaction(accountId):
        #     return "ammount: 200, data: 23-11-2020, ammount: 2000, data: 23-11-2022, ammount: 500, data: 23-11-2023, ammount: 200, data: 23-11-2021"

        class TransactionModel(BaseModel):
            account_id: int
            account_number: str
            balance: Decimal
            customer_id: int
            created_at: datetime
            updated_at: datetime

            class Config:
                orm_mode = True

        # Dependency to get the database session
        def get_db():
            db = SessionLocal()
            print("Hello")
            try:
                yield db
            finally:
                db.close()
          
        def convert_to_dict(model):
            columns = [column.key for column in class_mapper(model.__class__).columns]
            return {column: getattr(model, column) for column in columns}

        def getTransaction(accountId):
            db: Session = Depends(get_db)
            transactions = db.query(Transactions) \
                .filter(Transactions.account_id == 1) \
                .order_by(Transactions.transaction_id) \
                .offset(0) \
                .limit(10) \
                .all()
            print("Get transactions", transactions)
            jsonData = [convert_to_dict(transaction) for transaction in transactions]
            print(jsonData)
            return str(jsonData)
            # print("accountId")
            # return "ammount: 200, data: 23-11-2020, ammount: 2000, data: 23-11-2022, ammount: 500, data: 23-11-2023, ammount: 200, data: 23-11-2021"

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
