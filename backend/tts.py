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
    
        self.language_to_voice = {
            'en-US': 'en-US-JennyNeural',
            'en-IN': 'en-IN-NeerjaNeural',
            'ta-IN': 'ta-IN-PallaviNeural',
            'hi-IN': 'hi-IN-SwaraNeural',
            'kn-IN': 'kn-IN-SapnaNeural',
            'te-IN': 'te-IN-ShrutiNeural'
            # Add more language-to-voice mappings as needed
        }

    async def text_to_speech(self, text, lang):
        print("Ln", lang)
        voice_name = self.language_to_voice.get(lang)
        print('voice name', voice_name)
        body = f"""
        <speak version='1.0' xml:lang="{lang}" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts">
            <voice name="{voice_name}">
                <mstts:express-as style="calm" styledegree="0.1" role="YoungAdultFemale">
                    {text}
                </mstts:express-as>
            </voice>
        </speak>
        """

        print("Body", body)

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