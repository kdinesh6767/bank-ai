import React, { useEffect, useRef, useState } from "react";
import MicIcon from "./mic";
import "./dashboard.css";
import SoundWaveAnimation from "./soundwave";

let temporaryAudioChunks: Blob[] = [];

const Dashboard: React.FC = () => {
    const accountNumber = localStorage.getItem("accountNumber") || "Unknown";
    const isLogged = localStorage.getItem("isLogged") || false;
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
    const [isRecording, setIsRecording] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string>("");
    const audioPlayerRef = useRef<HTMLAudioElement>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isSuccess, setIsSuccess] = useState<boolean>(false);

    useEffect(() => {
        return () => {
            if (mediaRecorder) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        };
    }, [mediaRecorder]);

    useEffect(() => {
        const postData = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8000/welcome', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ lang: 'en-US', name: 'dinesh' })
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const serverAudioBlob = await response.blob();
                setIsLoading(false)
                if (audioPlayerRef.current) {
                    let url = URL.createObjectURL(serverAudioBlob);
                    audioPlayerRef.current.src = url;
                    audioPlayerRef.current.play();
                }
                localStorage.setItem("isLogged", "true");
            } catch (error) {
                console.error('Fetch error:', error);
            }
        };
        if(isLogged === "false"){
            setIsLoading(true)
            setIsSuccess(true)
            postData();
        }
        
    }, []);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            setMediaRecorder(recorder);

            recorder.ondataavailable = (event: BlobEvent) => {
                setIsRecording(false);
                temporaryAudioChunks.push(event.data);
                setAudioChunks(temporaryAudioChunks);
                sendAudioToServer(temporaryAudioChunks);
            };

            recorder.onerror = (event: any) => {
                console.error("Recorder error:", event.error);
                setErrorMessage("Error during recording.");
                recorder.stop();
            };

            recorder.start();
            setIsRecording(true);
            setErrorMessage("");
        } catch (error) {
            console.error("Error accessing microphone:", error);
            setErrorMessage("Microphone access denied or not available.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorder) {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    };

    function base64ToBlob(base64: string, mimeType: string) {
        var byteCharacters = atob(base64);
        var byteNumbers = new Array(byteCharacters.length);
        for (var i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        var byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], {type: mimeType});
    }

    const sendAudioToServer = async (chunks: Blob[]) => {
        console.log(chunks);
        setIsLoading(true);
        setIsSuccess(false);
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audioFile", audioBlob);
        formData.append("account", accountNumber);
        formData.append("lang", "en-US");
        
        try {
            const response = await fetch("http://127.0.0.1:8000/upload_audio", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const serverAudioBlob = await response.json();

            const audioBase64 = serverAudioBlob.audio;
            const audioBlob = base64ToBlob(audioBase64, 'audio/mpeg');

            console.log(serverAudioBlob.input)
            console.log(serverAudioBlob.output)

            if (audioPlayerRef.current) {
                let url = URL.createObjectURL(audioBlob);
                audioPlayerRef.current.src = url;
                audioPlayerRef.current.play();
            }
            setIsSuccess(true);
        } catch (error) {
            console.error("Error sending audio to server:", error);
            setErrorMessage("Failed to send audio to server.");
        } finally {
            setIsLoading(false);
            setAudioChunks([]);
        }
    };

    const toggleRecording = async () => {
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    };

    const handleEndSoundAnimation = () => {
        setIsSuccess(false)
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-btn-wrapper">
                <button className="mic-action-btn" onClick={toggleRecording} disabled={isLoading}>
                    {(isRecording && !isSuccess) || isLoading ? "Stop" : "Ask"}
                </button>
                {isLoading && <p className="loading-text">Processing <div className="lds-ellipsis"><div></div><div></div><div></div><div></div></div></p>}
                {errorMessage && <p className="error-message">{errorMessage}</p>}
            </div>

            {!isSuccess && <MicIcon isRecording={isRecording} />}
            <audio ref={audioPlayerRef} controls style={{ marginTop: "10px" }} hidden onEnded={handleEndSoundAnimation}></audio>
            {isSuccess && <SoundWaveAnimation audioUrl={audioPlayerRef.current?.src} />}
            
        </div>
    );
};

export default Dashboard;
