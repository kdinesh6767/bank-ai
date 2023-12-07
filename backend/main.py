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

import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import class_mapper
from typing import List
from num2words import num2words
from models import Accounts
from pydantic import BaseModel 
from datetime import datetime 
from decimal import Decimal

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
async def create_upload_file(audioFile: UploadFile = File(...), account: str = Form(...)):
    print(account)
    print(audioFile)
    temp_audio = f"input-{get_timestamped_filename('wav')}"
    print("Temp out", temp_audio)
    output_filename = f"output-{get_timestamped_filename('wav')}"
    print("Output file", output_filename)
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
        print("Agen")
        user_query = transcription.get('DisplayText')
        response = agent.get_response(user_query, account)
        print('responset',response)

        tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        print(tUrl)

        t =  AzureTTS(AZURE_SUBSCRIPTION_KEY,tUrl)

        responset = await t.text_to_speech(response.get('output'))
        return StreamingResponse(io.BytesIO(responset), media_type="audio/mpeg")
    except Exception as e:
        raise e
    finally:
        # Cleanup: Delete the temporary files
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(output_filename):
            os.remove(output_filename)



@app.post("/upload_audiov")
async def create_upload_file(
    audioFile: UploadFile = File(...), account: str = Form(...)
):
    print(account)
    print(audioFile)
    temp_audio = f"input-{get_timestamped_filename('wav')}"
    print("Temp out", temp_audio)
    output_filename = f"output-{get_timestamped_filename('wav')}"
    print("Output file", output_filename)

    try:
        # Check if the uploaded audio file is empty
        if audioFile.file.readable():
            with open(temp_audio, "wb") as buffer:
                buffer.write(await audioFile.read())
            convert_webm_to_wav(temp_audio, output_filename)
            lang = detectLang(output_filename, AZURE_SUBSCRIPTION_KEY, AZURE_SERVICE_REGION)
            transcription = await transcribe_audio(output_filename, lang)
        else:
            # Handle the case when the audio file is empty
            lang = "en-US"  
            transcription = {"DisplayText": ""}

        # Check if the transcription is empty or has some content
        if not transcription.get("DisplayText"):
        
            question = "How much amount do you want to deposit?"
            lang = "en-US"  
            response = {"output": question}
        else:
            # Use the LangChainAgent to generate a response
            agent = LangChainAgent()
            user_query = transcription.get("DisplayText")
            response = agent.get_response(user_query, account)

        tUrl = f"https://{AZURE_SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
        t = AzureTTS(AZURE_SUBSCRIPTION_KEY, tUrl)

        responset = await t.text_to_speech(response.get("output"))
        return StreamingResponse(io.BytesIO(responset), media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup: Delete the temporary files
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(output_filename):
            os.remove(output_filename)