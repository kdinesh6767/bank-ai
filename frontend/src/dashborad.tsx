import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import MicIcon from "./mic";
import "./dashboard.css";
import SoundWaveAnimation from "./soundwave";
import Menu from "./Menu";
import { useNavigate } from "react-router-dom";

let temporaryAudioChunks: Blob[] = [];
interface Data {
    input: string;
    output: string;
}

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
    const [showMenuBar, setShowMenuBar] = useState<boolean>(false);
    const [showMenuIcon, setShowMenuIcon] = useState<boolean>(true);
    let userInfo = JSON.parse(localStorage.getItem("customerInfo") || "");
    const [dataList, setDataList] = useState<Data[]>([]);
    const navigate = useNavigate();
    const [answers, setAnswers] = useState<[user: string, response: any][]>([]);

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
                    body: JSON.stringify({ lang: userInfo.data.customer.language, name: `${userInfo.data.customer.first_name} ${userInfo.data.customer.last_name}` })
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
                // setAudioChunks(prev => [...prev, event.data]);
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

    const sendAudioToServer = async (chunks: Blob[]) => {
        setIsLoading(true);
        setIsSuccess(false);
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audioFile", audioBlob);
        formData.append("account", accountNumber);
        formData.append("lang", userInfo.data.customer.language);

        try {
            const response = await axios.post("http://127.0.0.1:8000/upload_audio", formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            });

            if (response.status !== 200) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const audioDataURL = response.data.audio_file;

            const data = response.data.text;

            // Assuming the API response is an array of objects
            setDataList(prevDataList => [...prevDataList, data]);
            if (audioPlayerRef.current) {
                audioPlayerRef.current.src = audioDataURL;
                audioPlayerRef.current.play();
            }
            setIsSuccess(true);
            mediaRecorder?.stream.getTracks().forEach(track => track.stop());
            temporaryAudioChunks = [];
        } catch (error) {
            console.error("Error sending audio to server:", error);
            setErrorMessage("Failed to send audio to server.");
        } finally {
            setIsLoading(false);
            setAudioChunks([]);
        }
    };

    const onDeposit = async () => { 
        const f = document.getElementById('temp');
        const history: any[] = answers.map(a => ({ user: a[0], bot: a[1].answer }));
       
        try {
            const response = await axios.post('http://127.0.0.1:8000/depositSlip', {
                history: [...history, { user: f != null ? f.innerText : 'hi', bot: "hi" }]
            });
            if (response.status !== 200) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            setAnswers([...answers, [f != null ? f.innerText : 'hi', response.data]]);
            console.log(response)
            if (audioPlayerRef.current) {
                audioPlayerRef.current.src = response.data.audio_file;
                audioPlayerRef.current.play();
            }
        } catch (error) {
            console.error("Error sending audio to server:", error);
            setErrorMessage("Failed to send audio to server.");
        } finally {
            setIsLoading(false);
            setAudioChunks([]);
        }
    }

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

    const handleCloseMenu = () => {
        setShowMenuBar(false);
        setShowMenuIcon(true);
    };
    const handlemenuBar = () => {
        setShowMenuBar(true);
        setShowMenuIcon(false);
    };
    const handleLogout = () => {
        navigate("/");
        localStorage.removeItem("customerInfo");
        localStorage.removeItem("accountNumber");
    };
    return (
        <div className={`dashboard-container ${showMenuBar ? "with-menu" : ""}`}>
            <div className="left-container">
                <div className="user_heading_login_btn">
                    <h2 className="user_heading">
                        Welcome to {userInfo.data.customer.first_name} {""}
                        {userInfo.data.customer.last_name}
                    </h2>
                    <button className="logout_btn" onClick={handleLogout}>
                        Log Out{" "}
                    </button>
                    <button onClick={onDeposit}>Deposit</button>
                    <p id="temp">Hi</p>
                </div>

                <div className="dashboard_content">
                    <div className="dashboard-btn-wrapper">
                        <button className="mic-action-btn" onClick={toggleRecording} disabled={isLoading}>
                            {(isRecording && !isSuccess) || isLoading ? "Stop" : "Ask"}
                        </button>
                        {isLoading && (
                            <p className="loading-text">
                                Processing{" "}
                                <div className="lds-ellipsis">
                                    <div></div>
                                    <div></div>
                                    <div></div>
                                    <div></div>
                                </div>
                            </p>
                        )}
                        {errorMessage && <p className="error-message">{errorMessage}</p>}
                    </div>
                    <div className="mic_action_btn_container">
                        {!isSuccess && <MicIcon isRecording={isRecording} className={showMenuBar ? "with-menu" : ""} />}
                        <audio ref={audioPlayerRef} controls style={{ marginTop: "10px" }} hidden onEnded={handleEndSoundAnimation}></audio>
                        {isSuccess && <SoundWaveAnimation audioUrl={audioPlayerRef.current?.src} />}
                    </div>{" "}
                </div>
            </div>

            {showMenuIcon && <img src="chat-icon.png" alt="menu Icon" onClick={handlemenuBar} className="menu_bar_icon" />}

            {showMenuBar && <Menu dataList={dataList} onClose={handleCloseMenu} showMenuBar={showMenuBar} />}
        </div>
    );
};

export default Dashboard;
