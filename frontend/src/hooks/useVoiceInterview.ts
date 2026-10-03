import { useEffect, useRef, useState } from "react";

// Web Speech API type definitions for SpeechRecognition
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

export function useVoiceInterview() {
  const [isVoiceSupported, setIsVoiceSupported] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [micPermission, setMicPermission] = useState<"granted" | "denied" | "prompt" | "unsupported">("prompt");
  const [transcript, setTranscript] = useState<string>("");
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const win = window as IWindow;
    const hasSpeechSynthesis = "speechSynthesis" in window;
    const hasSpeechRecognition = !!(win.SpeechRecognition || win.webkitSpeechRecognition);

    if (hasSpeechSynthesis && hasSpeechRecognition) {
      setIsVoiceSupported(true);
    } else {
      setMicPermission("unsupported");
    }
  }, []);

  // 1. Text-to-Speech (TTS)
  const speakText = (text: string) => {
    if (!("speechSynthesis" in window)) {
      setVoiceError("Text-to-speech is not supported in this browser.");
      return;
    }

    try {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
        setVoiceError(null);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (e) => {
        setIsSpeaking(false);
        setVoiceError("Audio speech synthesis error: " + (e.error || "playback failed"));
      };

      window.speechSynthesis.speak(utterance);
    } catch {
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // 2. Speech-to-Text (STT)
  const startListening = (onTranscriptUpdate?: (text: string) => void) => {
    setVoiceError(null);
    const win = window as IWindow;
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setVoiceError("Speech recognition is not supported in this browser. Please type your response.");
      return;
    }

    // Stop speaking if question audio is playing
    stopSpeaking();

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // Ignore
        }
      }

      const recognition = new SpeechRecognitionClass();
      recognitionRef.current = recognition;

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      let finalSpokenText = "";

      recognition.onstart = () => {
        setIsListening(true);
        setMicPermission("granted");
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimText = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalSpokenText += result[0].transcript + " ";
          } else {
            interimText += result[0].transcript;
          }
        }
        const fullCurrentText = (finalSpokenText + interimText).trim();
        setTranscript(fullCurrentText);
        if (onTranscriptUpdate) {
          onTranscriptUpdate(fullCurrentText);
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        setIsListening(false);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          setMicPermission("denied");
          setVoiceError("Microphone permission denied. Please grant microphone access in your browser or type your answer.");
        } else if (event.error === "no-speech") {
          setVoiceError("No speech was detected. Please speak into your microphone or type your response.");
        } else if (event.error === "network") {
          setVoiceError("Network error during speech recognition. Please check your connection or type your answer.");
        } else if (event.error !== "aborted") {
          setVoiceError(`Speech recognition error: ${event.error}. Please try again or type your answer.`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        if (!finalSpokenText.trim()) {
          // Check if user spoke anything
          setVoiceError("Recording finished. If no text appeared, speak clearly or type your response.");
        }
      };

      recognition.start();
    } catch (err: any) {
      setIsListening(false);
      setVoiceError(err.message || "Failed to initialize microphone.");
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }
      setIsListening(false);
    }
  };

  const cancelVoice = () => {
    stopSpeaking();
    stopListening();
    setTranscript("");
    setVoiceError(null);
  };

  return {
    isVoiceSupported,
    isSpeaking,
    isListening,
    micPermission,
    transcript,
    voiceError,
    setVoiceError,
    speakText,
    stopSpeaking,
    startListening,
    stopListening,
    cancelVoice,
  };
}
