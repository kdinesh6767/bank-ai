import React, { useEffect, useRef, useState } from 'react';
let audioChunks: BlobPart[] = [];

const Dashboard: React.FC = () => {
  const accountNumber = localStorage.getItem('accountNumber') || 'Unknown';
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const audioPlayerRef = useRef<HTMLAudioElement>(null);
  useEffect(() => {
    // Cleanup function to stop the media stream when the component is unmounted
    return () => {
      if (mediaRecorder) {
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [mediaRecorder]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      setMediaRecorder(recorder);

      recorder.ondataavailable = (event: BlobEvent) => {
        setAudioChunks((prev) => [...prev, event.data]);
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
      setIsRecording(false);
    }
  };

  const sendAudioToServer = async () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("audioFile", audioBlob);
    formData.append('account', accountNumber)

    try {
      const response = await fetch("http://127.0.0.1:8000/upload_audio", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const serverAudioBlob = await response.blob();

    // Create a URL for the blob and set it as the source for the audio player
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = URL.createObjectURL(serverAudioBlob);
      audioPlayerRef.current.play(); // Optionally, start playing the audio automatically
    }
    } catch (error) {
      console.error("Error sending audio to server:", error);
      setErrorMessage("Failed to send audio to server.");
    }

    setAudioChunks([]);
  };

  const setAudioPlayerSource = (data: any) => {
    if (audioChunks.length > 0) {
      const audioBlob = new Blob(data.body, { type: 'audio/wav' });
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = URL.createObjectURL(audioBlob);
      }
    }
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Account Number: {accountNumber}</p>
      <div>
      {errorMessage && <p>Error: {errorMessage}</p>}
      <button onClick={startRecording} disabled={isRecording}>Start Recording</button>
      <button onClick={stopRecording} disabled={!isRecording}>Stop Recording</button>
      <button onClick={sendAudioToServer} disabled={audioChunks.length === 0}>Send Audio</button>
      <audio ref={audioPlayerRef} controls style={{ marginTop: '10px' }}></audio>
    </div>
    </div>
  );
}

export default Dashboard;
