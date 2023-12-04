from langchain.tools import BaseTool
from math import pi
from typing import Union

from sqlalchemy import func
from database import SessionLocal
from models import Transactions
from sqlalchemy.orm import class_mapper
  

class PensionTool(BaseTool):
    name = "Get Pension"
    description = "Useful for answering questions about user pension queries. Function should have the input account_id."

    # Define a function to convert a SQLAlchemy model to a dictionary
    def convert_to_dict(self, model):
        columns = [column.key for column in class_mapper(model.__class__).columns]
        return {column: getattr(model, column) for column in columns}

    def _run(self, account_id: Union[int, str]):
        db = SessionLocal()
        print("PENSION ----------->", account_id)
        try:
            pension_transactions = db.query(Transactions) \
                    .filter(Transactions.account_id == 2) \
                    .filter(func.lower(Transactions.description).contains('pension'.lower())) \
                    .order_by(Transactions.transaction_id) \
                    .offset(0) \
                    .limit(10) \
                    .all()
            json_data = [self.convert_to_dict(transaction) for transaction in pension_transactions]
            print("PENSION TABLE", json_data)
            return str(json_data)
        except Exception as e:
            return "An error occurred: " + str(e)
        finally:
            db.close()

    def _arun(self, account_id: Union[int, str]):
        raise NotImplementedError("This tool does not support async")