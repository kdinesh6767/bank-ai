
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

import os
from dotenv import load_dotenv 

from database import SessionLocal
from models import Transactions , Accounts,Chalan
from sqlalchemy.orm import class_mapper
from langchain.globals import set_debug

from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from datetime import datetime





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

        def getPension(accountnumber):
            db = SessionLocal()
            try:
                # print(self.account)
                pension_info = db.query(Transactions) \
                    .filter(Transactions.account_number == "1234567890") \
                    .filter(Transactions.description.ilike("%pension%")) \
                    .order_by(Transactions.transaction_id) \
                    .first()

                if pension_info:
                    print(f"Pension information: {pension_info.description}")
                    pension_data = convert_to_dict(pension_info)
                    print("pension data", pension_data)
                    return str(pension_data)
                else:
                    print("No pension information found for the account.")
                    return "No pension information found for the account."

            except Exception as e:
                print(f"An error occurred: {e}")
                return "An error occurred: " + str(e)
            finally:
                db.close()
       

        # def generateChalan(accountnumber):
        #     db = SessionLocal()
        #     try:
        #         # Check if the account exists
        #         account = db.query(Accounts).filter(Accounts.account_number == "1234567890" ).first()
        #         if not account:
        #             return "Account not found"

        #         # Fetch recent transactions for the account
        #         transactions = db.query(Transactions) \
        #             .filter(Transactions.account_id == account_id) \
        #             .order_by(Transactions.transaction_id.desc()) \
        #             .limit(10) \
        #             .all()

                
        #         chalan_number = f"CH{datetime.now().strftime('%Y%m%d%H%M%S')}"

        #         # Create chalan data dictionary
        #         chalan_data = {
        #             'account_id': account_id,
        #             'chalan_number': chalan_number,
        #             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        #             'recent_transactions': [convert_to_dict(transaction) for transaction in transactions]
        #         }

                

        #         return str(chalan_data)

        #     except Exception as e:
        #         # Handle exceptions, log errors, etc.
        #         return "An error occurred: " + str(e)
        #     finally:
        #         # Close the session
        #         db.close()



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
        # self.tools.append(Tool(
        # name='Generate Chalan',
        # func=generateChalan,
        # description='Useful for generating a chalan to deposit the specified amount into the account.'
        # ))

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
            print("Provided Account ID:", self.account)
            # self.getTransaction1()
            response = self.zero_shot_agent(query)
            return response 
            
        except Exception as e:
            
            # Here, you would ideally log the exception 'e' for debugging
            return "An error occurred while processing the request."
