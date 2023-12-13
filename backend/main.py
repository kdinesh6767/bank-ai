import dbm
import io
import json
import os
from shelve import DbfilenameShelf
import subprocess
from datetime import datetime
from fastapi import FastAPI, Depends, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import requests
import azure.cognitiveservices.speech as speechsdk
from tools.SQLAgent import SQLAgent
from database import SessionLocal
from typing import List, Optional

from database_utils import get_db, initialize_database
from LangChainAgent import LangChainAgent
from tts import AzureTTS
from models import Accounts, Chalan, Transactions, Customers
from pydantic import BaseModel
# import librosa
# import soundfile as sf
from sqlalchemy.orm import class_mapper
import base64


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


# Azure credentials
AZURE_SUBSCRIPTION_KEY = os.getenv("AZURE_SUBSCRIPTION_KEY")
AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION")

class AccountRequestModel(BaseModel):
    account_number: str

class CustomerResponseModel(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    age: int
    identity_card_no: str
    language: str
    created_at: datetime
    updated_at: datetime


@app.post("/accounts/validate")
def validate_account(request: AccountRequestModel, db: Session = Depends(get_db)):
    customer = None
    account = db.query(Accounts).filter(Accounts.account_number == request.account_number).first()
    return {"message": "Account valid", 'data': account}

@app.get("/customers/", response_model=List[CustomerResponseModel])
def read_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    customers = db.query(Customers).offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{customer_id}", response_model=CustomerResponseModel)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customers).filter(Customers.customer_id == customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

def get_timestamped_filename(extension):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
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
        print("error")
        raise HTTPException(status_code=500, detail=f"Error converting file: {e}")

# def convert_webm_to_wav(input_file, output_file):
#     try:
#         # Load the audio file with librosa
#         audio, sample_rate = librosa.load(input_file, sr=16000, mono=True)

#         # Write the output file in WAV format with 16-bit PCM
#         sf.write(output_file, audio, sample_rate, subtype='PCM_16')
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error converting file: {e}")

def detect_lang(file_path: str, key: str, region: str) -> str:
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
    
@app.post("/accounts/validate")
def validate_account(request: AccountRequestModel, db: Session = Depends(get_db)):
    account = db.query(Accounts).filter(Accounts.account_number == request.account_number).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account valid"}

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

@app.post("/upload_audio")
async def create_upload_file(audioFile: UploadFile = File(...), account: str = Form(...), lang: str = Form(...)):
    print(account)
    print(audioFile)

    temp_audio = f'input-{get_timestamped_filename("wav")}'
    output_filename = f'output-{get_timestamped_filename("wav")}'
    try:
        with open(temp_audio, "wb") as buffer:
            buffer.write(await audioFile.read())
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"File writing error: {e}")

    try:
        convert_webm_to_wav(temp_audio, output_filename)
        detectLang = detect_lang(output_filename, AZURE_SUBSCRIPTION_KEY, AZURE_SERVICE_REGION)
        transcription = await transcribe_audio(output_filename, detectLang)

    
        # agent = LangChainAgent()
        # response = agent.get_response(transcription.get('DisplayText'), account)
        print("transcription ------------------------>",transcription)
        agent = SQLAgent()
        response = agent.get_response(transcription.get('DisplayText'), account, lang)

        print('response', response)

        tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        print(tUrl)

        t =  AzureTTS(AZURE_SUBSCRIPTION_KEY,tUrl)

        response_tts = await t.text_to_speech(response, lang)

        audio_data = io.BytesIO(response_tts)
        audio_data_url = f"data:audio/mpeg;base64,{base64.b64encode(audio_data.read()).decode()}"
        response_data = {
            "text": {
                'input': transcription.get('DisplayText'),
                'output': response,
            },
            "audio_file": audio_data_url 
        }
        return JSONResponse(content=response_data)
        # return StreamingResponse(io.BytesIO(response_tts), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(output_filename):
            os.remove(output_filename)

class Lang(BaseModel):
    lang: str
    name: str

@app.post("/welcome")
async def welcome_msg(lang: Lang):
    agent = LangChainAgent()
    response = agent.greet_user(lang.lang, lang.name)
    tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

    print(tUrl)

    t =  AzureTTS(AZURE_SUBSCRIPTION_KEY,tUrl)

    response_tts = await t.text_to_speech(response, lang.lang)
    return StreamingResponse(io.BytesIO(response_tts), media_type="audio/mpeg")

class DepositSlipRequest(BaseModel):
    history: list[dict[str, str]]

@app.post("/depositSlip")
async def depositSlip(audioFile: Optional[UploadFile] = File(None), chatHistory: str = Form(...),account_number_from_frontend: str = Form(...),):
    print("account_number_from_frontend:", account_number_from_frontend)
    history = json.loads(chatHistory)
    print(history)

    # print("request", request)

    last_bot_message = next((item for item in reversed(history) if 'bot' in item), None)
    print(last_bot_message)
   
    print( audioFile )
    
    if audioFile and not audioFile.file.read() == b'':
        print("inside")
        audioFile.file.seek(0)
        # If the last bot message is found, check for the user's audio response
        
        temp_audio = f'input-{get_timestamped_filename("wav")}'
        output_filename = f'output-{get_timestamped_filename("wav")}'

            
            
        try:
            with open(temp_audio, "wb") as buffer:
                buffer.write(await audioFile.read())
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"File writing error: {e}")

        try:
        
            print("audio process")
            convert_webm_to_wav(temp_audio, output_filename)
            detectLang = detect_lang(output_filename, AZURE_SUBSCRIPTION_KEY, AZURE_SERVICE_REGION)
            transcription = await transcribe_audio(output_filename, detectLang)

            history[-1]["user"] = transcription.get("DisplayText")

            # The additional condition to check if the audio response is empty
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred during transcription: {e}")
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            if os.path.exists(output_filename):
                os.remove(output_filename)
        
    agent = LangChainAgent()
    print("Final History",history)
    response = agent.deposit_slip(history)

    challan_data = None

    response_data = response
    status = None
    
    if 'message' in response_data:
        try:
            message_data = json.loads(response_data['message'])
            if isinstance(message_data, dict):
                status = message_data.get('status')
            else:
                print("Warning: 'message' is not a JSON object.")
        except json.decoder.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    print("Response data:", response_data)
    print("Response status:", status)
    if status and status.strip() == 'success':

        print("Inside if statement")
        print("Response status is success.")
        account = DbfilenameShelf.query(Accounts).filter(Accounts.account_number == account_number_from_frontend).first()
    
        if account is not None:
            customer_id = account.customer_id
            customer = dbm.query(Customers).filter(Customers.customer_id == customer_id).first()
            print("Customer:", customer)
            
            if customer is not None:
                challan_data = Chalan(
                    account_number=account_number_from_frontend,
                    customer_id=customer.customer_id,
                    first_name=customer.first_name,
                    last_name=customer.last_name,
                )
                print("Challan Data:", challan_data)
            else:
                raise HTTPException(status_code=404, detail="Customer not found")
        else:
            raise HTTPException(status_code=404, detail="Account not found")
    else:
        print("Challan Data is None or status is not success.")
        challan_data = None


       
    print("Fia", response)

    


    tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

    print(tUrl)

    t =  AzureTTS(AZURE_SUBSCRIPTION_KEY,tUrl)

    response_tts = await t.text_to_speech(response.get('message'), "en-IN")
    # return StreamingResponse(io.BytesIO(response_tts), media_type="audio/mpeg")
    audio_data = io.BytesIO(response_tts)
    audio_data_url = f"data:audio/mpeg;base64,{base64.b64encode(audio_data.read()).decode()}"
    
    if challan_data is not None:
        # Include the generated challan data
        response_data = {
            "answer": response.get('message'),
            "audio_file": audio_data_url,
            "challan_data": challan_data,
        }
    else:
        # Return the response without the challan data for other statuses
        response_data = {
            "answer": response.get('message'),
            "audio_file": audio_data_url,  
            "challan_data": None,
        }

    return response_data
    # return "ff"

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

