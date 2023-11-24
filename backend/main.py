import io
from fastapi import Depends, FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import azure.cognitiveservices.speech as speechsdk
import requests
import os
import subprocess
from dotenv import load_dotenv
from sqlalchemy import select
from database_utils import get_db, initialize_database 

from LangChainAgent import LangChainAgent
from tts import AzureTTS

from starlette.responses import StreamingResponse
from sqlalchemy.dialects import postgresql

# main.py
import logging

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import class_mapper
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

# Set up logging to print messages to the console
# logging.basicConfig(level=logging.DEBUG)
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database on startup
@app.on_event("startup")
def startup_event():
    initialize_database()
# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Azure credentials
AZURE_SUBSCRIPTION_KEY = os.getenv("AZURE_SUBSCRIPTION_KEY") 
AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION")

class CustomerResponseModel(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    age: int
    identity_card_no: str
    language: str
    created_at: datetime
    updated_at: datetime

@app.get("/customers/", response_model=List[CustomerResponseModel])
def read_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    customers = db.query(Customers).offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{customer_id}", response_model=CustomerResponseModel)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customers).filter(Customers.customer_id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.get("/customers/by_language/{language}", response_model=List[CustomerResponseModel])
def read_customers_by_language(language: str, db: Session = Depends(get_db)):
    customers = db.query(Customers).filter(Customers.language == language).all()
    if not customers:
        raise HTTPException(status_code=404, detail=f"No customers found for language: {language}")
    
    # Print the results to the terminal
    print(f"Customers with language '{language}': {customers}")

# Transaction Controller
class TransactionResponseModel(BaseModel):
    transaction_id: int
    transaction_date: datetime
    amount: Decimal
    transaction_type: str
    account_id: int
    description: str
    balance_after_transaction: Decimal
    created_at: datetime
    updated_at: datetime

@app.get("/transactions", response_model=List[TransactionResponseModel])
def read_transactions(account_id: int = 1, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    transactions = db.query(Transactions) \
        .filter(Transactions.account_id == account_id) \
        .order_by(Transactions.transaction_id) \
        .offset(skip) \
        .limit(limit) \
        .all()
    # print("Get transactions")
    jsonData = [convert_to_dict(transaction) for transaction in transactions]
    print(jsonData)
    return jsonData
    # print(transactions)
    return transactions


class ChalanResponseModel(BaseModel):
    chalan_id: int
    transaction_id: int
    account_id: int
    amount_in_words: str
    created_at: datetime
    updated_at: datetime

def convert_amount_to_words(amount):
    return num2words(amount, lang='en_IN')

@app.get("/generate_chalan/{transaction_id}", response_model=ChalanResponseModel)
def generate_chalan(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transactions).filter(Transactions.transaction_id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction not found for transaction_id: {transaction_id}")

    # You can use a function to convert the amount to words
    amount_in_words = convert_amount_to_words(transaction.amount)

    # Save chalan data to the database
    chalan = Chalan(
        transaction_id=transaction_id,
        account_id=transaction.account_id,
        amount_in_words=amount_in_words,
    )
    db.add(chalan)
    db.commit()

    return chalan
class AccountResponseModel(BaseModel):
    account_id: int
    account_number: str
    balance: Decimal
    customer_id: int
    created_at: datetime
    updated_at: datetime
    customer_name: str
    language: str

# Endpoint to get a list of all accounts
@app.get("/accounts/", response_model=List[AccountResponseModel])
def read_accounts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    accounts = db.query(Accounts).offset(skip).limit(limit).all()
    return accounts

def convert_to_dict(model):
    columns = [column.key for column in class_mapper(model.__class__).columns]
    return {column: getattr(model, column) for column in columns}

# Endpoint to get account details by account ID
@app.get("/accounts/{account_number}", response_model=AccountResponseModel)
def read_account(account_number: str, db: Session = Depends(get_db)):
    account = db.query(Accounts).filter(Accounts.account_number == account_number).options(joinedload(Accounts.customer)).first()

    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    account_info = convert_to_dict(account)
    account_info["customer_name"] = f"{account.customer.first_name} {account.customer.last_name}"
    account_info["language"] = account.customer.language

    return account_info


class AccountRequestModel(BaseModel):
    account_number: str

@app.post("/accounts/validate")
def validate_account(request: AccountRequestModel, db: Session = Depends(get_db)):
    account = db.query(Accounts).filter(Accounts.account_number == request.account_number).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account valid"}


class TransactionModel(BaseModel):
    account_id: int
    account_number: str
    balance: Decimal
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@app.get("/accountsd")
async def getTransaction(account_id: str = 'A1001', skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> List[TransactionModel]:
    print(Transactions)
    result = await db.execute(
        select(Transactions)
        .filter(Transactions.account_id == account_id)
        .order_by(Transactions.transaction_id)
        .offset(skip)
        .limit(limit)
    )
    print(result)
    transactions = result.scalars().all()
    return [TransactionModel.from_orm(tx) for tx in transactions]


def get_timestamped_filename(extension):
    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # Added microseconds for uniqueness
    return f"{timestamp}.{extension}"

def convert_webm_to_wav(input_file, output_file):
    try:
        command = [
            'ffmpeg',
            '-i', input_file,
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            output_file
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error converting file: {e}")

def detectLang(file_path: str, key: str, region: str) -> str:
    try:
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "hi-IN", "ta-IN", "kn-IN" ])
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        audio_input = speechsdk.audio.AudioConfig(filename=file_path)

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
            audio_config=audio_input
        )

        result = speech_recognizer.recognize_once()
        auto_detect_source_language_result = speechsdk.AutoDetectSourceLanguageResult(result)
        detected_language = auto_detect_source_language_result.language
        print("Detected Language:", detected_language)

        return detected_language
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {e}")

@app.post("/upload_audio")
async def create_upload_file(audioFile: UploadFile = File(...), account: str = Form(...)):
    print(account)
    temp_audio = get_timestamped_filename("wav")
    output_filename = get_timestamped_filename("wav")
    try:
        with open(temp_audio, "wb") as buffer:
            buffer.write(await audioFile.read())
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"File writing error: {e}")

    try:
        convert_webm_to_wav(temp_audio, output_filename)
        lang = detectLang(output_filename, AZURE_SUBSCRIPTION_KEY, AZURE_SERVICE_REGION)
        transcription = await transcribe_audio(output_filename, lang)

        agent = LangChainAgent()
        response = agent.get_response(transcription.get('DisplayText'), account)

        print('responset',response)

        tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        print(tUrl)

        t =  AzureTTS(AZURE_SUBSCRIPTION_KEY,tUrl)

        responset = await t.text_to_speech(response)

        # print(StreamingResponse(response.iter_content(chunk_size=8192), media_type="audio/mpeg"))

        # print('responset',responset)
        return StreamingResponse(io.BytesIO(responset), media_type="audio/mpeg")
        # return {"transcription": StreamingResponse(io.BytesIO(responset), media_type="audio/mpeg")}
    except Exception as e:
        raise e
    finally:
        # Cleanup: Delete the temporary files
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(output_filename):
            os.remove(output_filename)

async def transcribe_audio(file_path, lang):
    url = f"https://{AZURE_SERVICE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={lang}&format=detailed"
    
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_SUBSCRIPTION_KEY,
        'Content-type': 'audio/wav; codecs=audio/pcm; samplerate=16000'
    }

    try:
        with open(file_path, 'rb') as audio_file:
            response = requests.post(url, headers=headers, data=audio_file)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Error reading file for transcription: {e}")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error from Azure API: {response.content}")

    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid JSON response from Azure API")

