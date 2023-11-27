import React, { useRef, useEffect } from 'react';

interface SoundWaveAnimationProps {
  audioUrl: any;
}

const SoundWaveAnimation: React.FC<SoundWaveAnimationProps> = ({ audioUrl }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!audioUrl) return;

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const audioContext = new window.AudioContext;
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 1024;

    fetch(audioUrl)
      .then(response => response.arrayBuffer())
      .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
      .then(audioBuffer => {
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(analyser);
        analyser.connect(audioContext.destination);
        source.start();

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            const WIDTH = canvas.width;
            const HEIGHT = canvas.height;
            const barWidth = 20;
            const spacing = 30;
            const roundedCorners = 10;
  
            ctx.clearRect(0, 0, WIDTH, HEIGHT);
            analyser.getByteFrequencyData(dataArray);
  
            let x = 0;
            for (let i = 0; i < bufferLength; i++) {
              const barHeight = dataArray[i] * (HEIGHT / 256);
              ctx.fillStyle = 'white';
              ctx.beginPath();
              ctx.moveTo(x + roundedCorners, HEIGHT / 2 - barHeight / 2);
              ctx.lineTo(x + barWidth - roundedCorners, HEIGHT / 2 - barHeight / 2);
              ctx.quadraticCurveTo(x + barWidth, HEIGHT / 2 - barHeight / 2, x + barWidth, HEIGHT / 2 - barHeight / 2 + roundedCorners);
              ctx.lineTo(x + barWidth, HEIGHT / 2 + barHeight / 2 - roundedCorners);
              ctx.quadraticCurveTo(x + barWidth, HEIGHT / 2 + barHeight / 2, x + barWidth - roundedCorners, HEIGHT / 2 + barHeight / 2);
              ctx.lineTo(x + roundedCorners, HEIGHT / 2 + barHeight / 2);
              ctx.quadraticCurveTo(x, HEIGHT / 2 + barHeight / 2, x, HEIGHT / 2 + barHeight / 2 - roundedCorners);
              ctx.lineTo(x, HEIGHT / 2 - barHeight / 2 + roundedCorners);
              ctx.quadraticCurveTo(x, HEIGHT / 2 - barHeight / 2, x + roundedCorners, HEIGHT / 2 - barHeight / 2);
              ctx.closePath();
              ctx.fill();
  
              x += barWidth + spacing;
            }
  
            animationRef.current = requestAnimationFrame(draw);
          };

        draw();
      });

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioUrl]);

  return (
    <canvas ref={canvasRef} width={window.innerWidth} height={300} />
  );
};

export default SoundWaveAnimation;
