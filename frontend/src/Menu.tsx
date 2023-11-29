import React, { useEffect, useRef, useState } from "react";
import CloseIcon from "./close.png";
import "./Menu.css";

interface Data {
    input: string;
    output: string;
}

interface CardProps {
    dataList: Data[];
    onClose: () => void;
    showMenuBar: boolean;
}
const Menu: React.FC<CardProps> = ({ dataList, onClose, showMenuBar }) => {
    useEffect(() => {
        console.log("datalist coming from dashboard", dataList);
    }, []);
    return (
        <>
            <div className={`menu_window ${showMenuBar ? "with-menu" : ""}`}>
                <img alt="Close " src={CloseIcon} onClick={onClose} width="30px" height="30px" />
                <div className="menu_content">
                    {dataList.map((data: any, index: number) => (
                        <div key={index} className="menu_bubble">
                            <div className="input_text">{data.input}</div>
                            <div className="output_text">{data.output}</div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
};

export default Menu;
