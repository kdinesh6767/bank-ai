import React, { useEffect } from "react";
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
                <img className="close_icon" alt="Close " src="close.png" onClick={onClose} />
                <div className="menu_content">
                    {dataList.map((data: any, index: number) => (
                        <div key={index} className="menu_bubble">
                            <div className="bubble input_text">{data?.input}</div>
                            <div className="bubble output_text">{data?.output}</div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
};

export default Menu;
