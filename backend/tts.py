from fastapi import FastAPI, Form, HTTPException

import requests

import httpx

class AzureTTS:
    def __init__(self, azure_key, azure_endpoint):
        self.azure_key = azure_key
        self.azure_endpoint = azure_endpoint
        self.headers = {
            'Ocp-Apim-Subscription-Key': azure_key,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
        }

    async def text_to_speech(self, text):
        body = f"""
        <speak version='1.0' xml:lang='en-US'>
            <voice xml:lang='en-US' xml:gender='Female' name='en-US-JennyNeural'>
                {text}
            </voice>
        </speak>
        """

        try:
            # response = requests.post(self.azure_endpoint, headers=self.headers, data=body)
            # response.raise_for_status()
            # print("TTS", response)
            # return response
            async with httpx.AsyncClient() as client:
                response = await client.post(self.azure_endpoint, headers=self.headers, data=body)
                response.raise_for_status()
                return response.content
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))
