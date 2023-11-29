import React, { useEffect, useRef, useState } from "react";
import MicIcon from "./mic";
import "./dashboard.css";
import SoundWaveAnimation from "./soundwave";
import MenuIcon from "./menu.png";
import Menu from "./Menu";

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
            const response = await fetch("http://127.0.0.1:8000/upload_audio", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const serverAudioBlob = await response.blob();
            //TO DO: replace the dummy input and output data inside handleMenu Function with original data once it starts working
            // const data = await response.json();
            // const data = {
            //     input: "Give me latest Transactions",
            //     output: "Your latest transaction sare 2300 rs , 7600"
            // };

            // // Assuming the API response is an array of objects
            // // setDataList(prevDataList => [...prevDataList, data]);
            if (audioPlayerRef.current) {
                let url = URL.createObjectURL(serverAudioBlob);
                audioPlayerRef.current.src = url;
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
        // since BE API is not working, sending dummy data on menuBar open
        const data = {
            input: "Give me latest Transactions ",
            output: "Your latest transaction sare 2300 rs , 7600"
        };

        setDataList(prevDataList => [...prevDataList, data]);
    };
    return (
        <div className={`dashboard-container ${showMenuBar ? "with-menu" : ""}`}>
            <h2
                style={{
                    display: "flex",
                    alignItems: "center",
                    position: "relative",
                    right: "37%",
                    color: "white"
                }}
            >
                Welcome to {userInfo.data.customer.first_name}
                {userInfo.data.customer.last_name}
            </h2>
            {showMenuIcon && (
                <img
                    src={MenuIcon}
                    alt="menu"
                    width="40px"
                    height="40px"
                    style={{
                        position: "relative",
                        left: "48%",
                        backgroundColor: "transparent"
                    }}
                    onClick={handlemenuBar}
                />
            )}

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
