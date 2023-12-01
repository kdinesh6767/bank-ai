import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import MicIcon from "./mic";
import "./dashboard.css";
import SoundWaveAnimation from "./soundwave";
import Menu from "./Menu";
import menuIcon from "./notes.png";
import { useNavigate } from "react-router-dom";

let temporaryAudioChunks: Blob[] = [];
interface Data {
    input: string;
    output: string;
}

const Dashboard: React.FC = () => {
    const accountNumber = localStorage.getItem("accountNumber") || "Unknown";
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
    const [isRecording, setIsRecording] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string>("");
    const audioPlayerRef = useRef<HTMLAudioElement>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isSuccess, setIsSuccess] = useState<boolean>(false);
    const [soundWaveAnimationCompleted, setSoundWaveAnimationCompleted] = useState<boolean>(false);
    const [showMenuBar, setShowMenuBar] = useState<boolean>(false);
    const [showMenuIcon, setShowMenuIcon] = useState<boolean>(true);
    let userInfo = JSON.parse(localStorage.getItem("customerInfo") || "");
    const [dataList, setDataList] = useState<Data[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
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
        console.log(chunks);
        setIsLoading(true);
        setIsSuccess(false);
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audioFile", audioBlob);
        formData.append("account", accountNumber);

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
            console.log(data);

            // Assuming the API response is an array of objects
            setDataList(prevDataList => [...prevDataList, data]);
            if (audioPlayerRef.current) {
                audioPlayerRef.current.src = audioDataURL;
                audioPlayerRef.current.play();
            }
            setIsSuccess(true);
            mediaRecorder?.stream.getTracks().forEach(track => track.stop());
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
        setSoundWaveAnimationCompleted(true);
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
            <div className="user_heading_login_btn">
                <h2 className="user_heading">
                    Welcome to {userInfo.data.customer.first_name} {""}
                    {userInfo.data.customer.last_name}
                </h2>
                <button className="logout_btn" onClick={handleLogout}>
                    Log Out{" "}
                </button>
            </div>

            {showMenuIcon && <img src={menuIcon} alt="menu Icon" onClick={handlemenuBar} className="menu_bar_icon" />}

            {showMenuBar && <Menu dataList={dataList} onClose={handleCloseMenu} showMenuBar={showMenuBar} />}
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
                <div className="mic_action_btn_container">{!isSuccess && <MicIcon isRecording={isRecording} className={showMenuBar ? "with-menu" : ""} />}</div>{" "}
                <audio ref={audioPlayerRef} controls style={{ marginTop: "10px" }} hidden onEnded={handleEndSoundAnimation}></audio>
                {isSuccess && <SoundWaveAnimation audioUrl={audioPlayerRef.current?.src} />}
                {soundWaveAnimationCompleted && <MicIcon isRecording={isRecording} />}
            </div>
        </div>
    );
};

export default Dashboard;
