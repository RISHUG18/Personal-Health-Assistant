/* AI Chat — stub with demo history + retrieval citations */
"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User as UserIcon, FileText } from "lucide-react";
import { Card, Badge } from "@/components/ui/shared";
import { DEMO_CHAT_HISTORY, ChatMessage } from "@/lib/demo-data";
import { cn } from "@/lib/utils";

const STUB_RESPONSES: Record<string, Omit<ChatMessage, "id" | "role" | "timestamp">> = {
  tired: {
    content:
      "Your fatigue likely has three overlapping causes:\n\n" +
      "1. Iron-deficiency anaemia (Hb\u00a09.8\u00a0g/dL) \u2014 low haemoglobin means less oxygen reaches your muscles, causing persistent tiredness.\n\n" +
      "2. Poor sleep quality \u2014 your wearable shows an average of only 5.6\u00a0h/night over the past week, well below the recommended 7\u20139\u00a0h.\n\n" +
      "3. High AQI exposure \u2014 breathing polluted air (AQI\u00a0168 in Chennai) increases oxidative stress and can worsen fatigue in anaemic patients.",
    citations: [
      "CBC_Report_Jan2026.pdf \u00b7 Hb = 9.8 g/dL",
      "Wearable data \u00b7 7-day avg sleep = 5.6 h",
      "Environment \u00b7 Chennai AQI = 168",
    ],
  },
  hba1c: {
    content:
      "HbA1c measures your average blood glucose over the past 3\u00a0months by looking at how much sugar is bound to your red blood cells.\n\n" +
      "Your result of 7.8% places you in the diabetic range (\u22656.5\u00a0%). A healthy target for most managed diabetics is below 7.0\u00a0%.\n\n" +
      "Your current level suggests blood glucose has been consistently elevated. This raises risk for kidney, nerve, and eye complications if sustained long-term. Discuss medication review with Dr.\u00a0Priya Nair.",
    citations: [
      "HbA1c_Feb2026.pdf \u00b7 HbA1c = 7.8%",
      "Lipid_Panel_Jan2026.pdf \u00b7 Fasting glucose = 148 mg/dL",
    ],
  },
  exercise: {
    content:
      "Today: Caution advised. Chennai AQI is 168 (Unhealthy for all groups) and a heatwave advisory is active.\n\n" +
      "Given your low haemoglobin (9.8\u00a0g/dL), strenuous outdoor exercise could cause dizziness, shortness of breath, or fainting.\n\n" +
      "Safer alternatives: Indoor walking or light yoga, or outdoor activity before 7\u00a0AM when AQI tends to dip below 120.",
    citations: [
      "Environment \u00b7 Chennai AQI = 168 \u00b7 PM2.5 dominant",
      "CBC_Report_Jan2026.pdf \u00b7 Hb = 9.8 g/dL",
    ],
  },
  cholesterol: {
    content:
      "Your LDL cholesterol is 138\u00a0mg/dL \u2014 above the desirable threshold of <100\u00a0mg/dL.\n\n" +
      "LDL (\u2018bad\u2019 cholesterol) contributes to plaque buildup in arteries, raising cardiovascular risk. Your total cholesterol of 215\u00a0mg/dL also exceeds the recommended <200\u00a0mg/dL.\n\n" +
      "Your doctor has likely recommended statin therapy. Additionally, limiting saturated fats, increasing soluble fibre (oats, legumes), and regular exercise can help.",
    citations: [
      "Lipid_Panel_Mar2026.pdf \u00b7 LDL = 138 mg/dL",
      "Lipid_Panel_Mar2026.pdf \u00b7 Total Cholesterol = 215 mg/dL",
    ],
  },
  default: {
    content:
      "I\u2019m your health companion AI. I can help you understand trends in your reports, explain test results in plain language, and suggest lifestyle improvements. I\u2019m not a doctor and cannot diagnose conditions.\n\nTry asking: \u201cWhy am I feeling tired?\u201d, \u201cWhat does my HbA1c mean?\u201d, or \u201cIs it safe to exercise today?\u201d",
  },
};

function matchStub(text: string): keyof typeof STUB_RESPONSES {
  const t = text.toLowerCase();
  if (t.match(/tired|fatigue|energy|exhausted|weak/)) return "tired";
  if (t.match(/hba1c|hb a1c|a1c|diabetes|glucose|sugar/)) return "hba1c";
  if (t.match(/exercise|outdoor|walk|run|gym|sport|activity/)) return "exercise";
  if (t.match(/cholesterol|ldl|hdl|lipid|heart|cardiovascular/)) return "cholesterol";
  return "default";
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(DEMO_CHAT_HISTORY);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    // Simulate latency — stub response (Week 3: keyword-matched canned LLM)
    setTimeout(() => {
      const stub = STUB_RESPONSES[matchStub(text)];
      const aiMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant",
        content: stub.content,
        citations: stub.citations,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
      setLoading(false);
    }, 1200);
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-57px)] md:h-screen max-w-3xl mx-auto">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-3 flex-shrink-0">
        <div className="h-8 w-8 rounded-full bg-blue-900/60 border border-blue-700/50 flex items-center justify-center">
          <Bot size={14} className="text-blue-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">AI Health Companion</p>
          <p className="text-[10px] text-slate-500">Gemini 2.5 Flash · RAG grounded · Non-diagnostic</p>
        </div>
        <Badge variant="success" className="ml-auto">Online</Badge>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-slate-800 flex-shrink-0">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask about your health, reports, or lifestyle…"
            rows={1}
            className="flex-1 resize-none bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-blue-600 placeholder:text-slate-600"
            style={{ maxHeight: "120px" }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="p-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition rounded-xl"
          >
            <Send size={16} className="text-white" />
          </button>
        </div>
        <p className="text-[10px] text-slate-600 mt-1.5 text-center">
          This is not medical advice. Always consult a qualified doctor.
        </p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
          isUser
            ? "bg-blue-900/60 border border-blue-700/50"
            : "bg-slate-700/80 border border-slate-600/50"
        )}
      >
        {isUser ? (
          <UserIcon size={12} className="text-blue-400" />
        ) : (
          <Bot size={12} className="text-slate-300" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn("max-w-[80%] space-y-2", isUser && "items-end")}>
        <div
          className={cn(
            "px-4 py-2.5 rounded-2xl text-sm leading-relaxed",
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-slate-800 border border-slate-700 text-slate-200 rounded-tl-sm"
          )}
        >
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-2" : ""}>{line}</p>
          ))}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="space-y-1 pl-1">
            <p className="text-[10px] text-slate-500 font-medium">Sources</p>
            {message.citations.map((c, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-[10px] text-blue-400 bg-blue-900/20 border border-blue-800/40 rounded-lg px-2 py-1"
              >
                <FileText size={9} />
                {c}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-3">
      <div className="h-7 w-7 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center">
        <Bot size={12} className="text-slate-300" />
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-slate-500 animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
