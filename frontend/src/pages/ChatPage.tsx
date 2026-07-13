import { useEffect, useRef, useState } from "react";
import { Send, Loader2, Sparkles, UploadCloud, X, Volume2, ImagePlus, Wand2, Download } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Markdown } from "@/components/Markdown";
import { usePageHeader } from "@/stores/pageHeader";
import { postStream, postForm, postBlob, api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Msg = {
  role: "user" | "assistant";
  content: string;
  image?: string; // 使用者訊息的圖片預覽 URL
  ocrText?: string; // 助理訊息：原始 OCR 文字（可展開）
  genImage?: string; // 助理訊息：生成的圖片（data URL）
  promptEn?: string; // 助理訊息：LLM 優化後的英文提示詞（可展開）
};

// 朗讀語音（edge-tts 為主）。id 即 edge-tts voice 名。
const VOICES = [
  { id: "zh-TW-HsiaoChenNeural", label: "台灣女聲" },
  { id: "zh-TW-YunJheNeural", label: "台灣男聲" },
  { id: "zh-CN-XiaoxiaoNeural", label: "大陸女聲" },
  { id: "zh-CN-YunxiNeural", label: "大陸男聲" },
];
const VOICE_KEY = "multimodel-tts-voice";

export function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [image, setImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [busyLabel, setBusyLabel] = useState("思考中…"); // pending 泡泡顯示文字（依動作而定）
  const fileRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // ── TTS（朗讀助理回覆）──
  const [ttsLoading, setTtsLoading] = useState<number | null>(null);
  const [ttsPlaying, setTtsPlaying] = useState<number | null>(null);
  const [voice, setVoice] = useState<string>(
    () => localStorage.getItem(VOICE_KEY) || VOICES[0].id
  );
  const [ttsEngine, setTtsEngine] = useState<"edge" | "melo" | null>(null); // 上次朗讀用的引擎
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const ttsCache = useRef<Map<string, string>>(new Map()); // voice+text → objectURL，避免重複合成

  useEffect(() => {
    usePageHeader.getState().set("多模態問答", "文字問答 · 圖片 OCR · 語音朗讀 · 文字生圖");
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function pickImage(f: File | null) {
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      toast.error("請選擇圖片檔");
      return;
    }
    setImage(f);
    setImageUrl(URL.createObjectURL(f));
  }

  function clearImage() {
    setImage(null);
    setImageUrl(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function speak(idx: number, text: string) {
    // 正在播這一則 → 停止
    if (ttsPlaying === idx && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setTtsPlaying(null);
      return;
    }
    // 停掉其他正在播的
    audioRef.current?.pause();
    try {
      const cacheKey = `${voice}::${text}`;
      let url = ttsCache.current.get(cacheKey);
      if (url) {
        // 快取只存線上(edge)結果（見下方），命中即為線上語音
        setTtsEngine("edge");
      } else {
        setTtsLoading(idx);
        const { blob, headers } = await postBlob("/tts", { text, voice });
        const engine = headers.get("X-TTS-Engine") === "melo" ? "melo" : "edge";
        url = URL.createObjectURL(blob);
        // 離線 fallback 不快取：恢復連線後會重新嘗試線上語音
        if (engine === "edge") ttsCache.current.set(cacheKey, url);
        setTtsEngine(engine);
        if (engine === "melo") {
          toast.info("目前無法連線，已改用離線語音（內建中文女聲）");
        }
      }
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setTtsPlaying(null);
      setTtsPlaying(idx);
      await audio.play();
    } catch (e) {
      toast.error((e as Error).message);
      setTtsPlaying(null);
    } finally {
      setTtsLoading(null);
    }
  }

  async function send() {
    if (loading) return;
    if (image) return sendImage();

    const text = input.trim();
    if (!text) return;
    const history = messages;
    setMessages([...history, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    setBusyLabel("思考中…");
    setLoading(true);
    try {
      await postStream("/chat/stream", { message: text, history }, (chunk) => {
        setMessages((m) => {
          const next = [...m];
          next[next.length - 1] = {
            role: "assistant",
            content: next[next.length - 1].content + chunk,
          };
          return next;
        });
      });
    } catch (e) {
      toast.error((e as Error).message);
      setMessages(history);
      setInput(text);
    } finally {
      setLoading(false);
    }
  }

  async function sendImage() {
    if (!image) return;
    const text = input.trim();
    const preview = imageUrl ?? undefined;
    const history = messages;
    setMessages([
      ...history,
      { role: "user", content: text, image: preview },
      { role: "assistant", content: "" },
    ]);
    setInput("");
    clearImage();
    setBusyLabel("辨識並整理中…");
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", image);
      form.append("instruction", text);
      const res = await postForm<{ ocr_text: string; organized: string }>("/ocr", form);
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: res.organized || "（未取得整理結果）",
          ocrText: res.ocr_text,
        };
        return next;
      });
    } catch (e) {
      toast.error((e as Error).message);
      setMessages(history);
      setInput(text);
    } finally {
      setLoading(false);
    }
  }

  async function generateImage() {
    if (loading || image) return;
    const text = input.trim();
    if (!text) return;
    const history = messages;
    setMessages([...history, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    setBusyLabel("生成圖片中…（首次載入模型或用 CPU 會較久）");
    setLoading(true);
    try {
      const res = await api.post<{ prompt_en: string; image: string }>("/image", { prompt: text });
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: "",
          genImage: res.image,
          promptEn: res.prompt_en,
        };
        return next;
      });
    } catch (e) {
      toast.error((e as Error).message);
      setMessages(history);
      setInput(text);
    } finally {
      setLoading(false);
    }
  }

  async function refineImage() {
    if (loading || image) return;
    const text = input.trim();
    if (!text) return;
    // 找最近一張生成圖，當作 img2img 的起點（鏈式：新圖又能被下次微調）
    const last = [...messages].reverse().find((m) => m.genImage);
    if (!last?.genImage) {
      toast.error("目前沒有可微調的圖片，請先生成一張");
      return;
    }
    const history = messages;
    setMessages([...history, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    setBusyLabel("微調圖片中…（img2img，以上一張圖為起點）");
    setLoading(true);
    try {
      const res = await api.post<{ prompt_en: string; image: string }>("/image/refine", {
        edit_instruction: text,
        init_image: last.genImage,
        prev_prompt_en: last.promptEn ?? "",
      });
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: "",
          genImage: res.image,
          promptEn: res.prompt_en,
        };
        return next;
      });
    } catch (e) {
      toast.error((e as Error).message);
      setMessages(history);
      setInput(text);
    } finally {
      setLoading(false);
    }
  }

  const canSend = !loading && (!!input.trim() || !!image);
  const canGenImage = !loading && !image && !!input.trim();
  const hasGenImage = messages.some((m) => !!m.genImage);
  const canRefine = !loading && !image && !!input.trim() && hasGenImage;

  return (
    <div className="animate-fade-up mx-auto flex h-[calc(100vh-8rem)] w-full max-w-5xl flex-col">
      <div className="nice-scroll min-h-0 flex-1 space-y-4 overflow-auto px-2 pb-4">
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center text-center text-muted-foreground">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gradient text-white">
              <Sparkles className="h-6 w-6" strokeWidth={1.75} />
            </div>
            <p className="text-sm">開始對話、上傳圖片做 OCR，或用文字生成圖片。</p>
            <p className="text-xs">記得先到「LLM Provider」註冊並選用一個模型。</p>
          </div>
        )}

        {messages.map((m, i) => {
          const isUser = m.role === "user";
          const isLast = i === messages.length - 1;
          const pending = !isUser && isLast && loading && m.content === "" && !m.genImage;
          return (
            <div key={i} className={cn("flex", isUser ? "justify-end" : "justify-start")}>
              <div
                className={cn(
                  "max-w-[80%] rounded-3xl px-4 py-2.5 text-sm",
                  isUser
                    ? "whitespace-pre-wrap bg-brand-gradient text-white"
                    : "glass-soft text-foreground"
                )}
              >
                {/* 使用者上傳的圖片縮圖 */}
                {isUser && m.image && (
                  <img
                    src={m.image}
                    alt="上傳圖片"
                    className="mb-2 max-h-56 max-w-full rounded-xl"
                  />
                )}

                {pending ? (
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.75} />
                    {busyLabel}
                  </span>
                ) : isUser ? (
                  m.content
                ) : m.genImage ? (
                  // 生成的圖片
                  <div className="space-y-2">
                    <img src={m.genImage} alt="生成圖片" className="max-h-96 max-w-full rounded-xl" />
                    <div className="flex items-center gap-2">
                      <a
                        href={m.genImage}
                        download="generated.png"
                        className="inline-flex h-7 items-center gap-1 rounded-lg px-2 text-xs text-muted-foreground hover:bg-white/50"
                      >
                        <Download className="h-4 w-4" strokeWidth={1.75} /> 下載
                      </a>
                    </div>
                    {m.promptEn && (
                      <details>
                        <summary className="cursor-pointer text-xs text-muted-foreground">
                          英文提示詞
                        </summary>
                        <p className="mt-1 rounded-xl bg-black/5 p-2 text-xs">{m.promptEn}</p>
                      </details>
                    )}
                  </div>
                ) : (
                  <>
                    <Markdown>{m.content}</Markdown>
                    {m.ocrText != null && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs text-muted-foreground">
                          原始 OCR 文字
                        </summary>
                        <pre className="nice-scroll mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded-xl bg-black/5 p-2 text-xs">
                          {m.ocrText || "（無）"}
                        </pre>
                      </details>
                    )}
                    {/* 朗讀鈕：串流完成的助理回覆才顯示 */}
                    {!(isLast && loading) && m.content && (
                      <div className="mt-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground"
                          onClick={() => speak(i, m.content)}
                          disabled={ttsLoading === i}
                          title={ttsPlaying === i ? "停止朗讀" : "朗讀"}
                          aria-label="朗讀"
                        >
                          {ttsLoading === i ? (
                            <Loader2 className="animate-spin" strokeWidth={1.75} />
                          ) : (
                            <Volume2
                              className={ttsPlaying === i ? "text-primary" : ""}
                              strokeWidth={1.75}
                            />
                          )}
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
        {messages.length > 0 && <div ref={bottomRef} />}
      </div>

      {/* 輸入列：玻璃底浮在背景上 */}
      <div className="glass rounded-3xl p-2">
        {/* 朗讀語音選擇（🔊 播放用；線上 edge-tts，離線自動 fallback MeloTTS）*/}
        <div className="mb-2 flex items-center gap-1.5 px-1">
          <Volume2 className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} />
          <Select
            value={voice}
            onChange={(e) => {
              setVoice(e.target.value);
              localStorage.setItem(VOICE_KEY, e.target.value);
            }}
            className="h-8 w-32 text-xs"
          >
            {VOICES.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </Select>
          {/* 離線 fallback 提示：無法連線時所選線上語音不生效，改用內建女聲 */}
          {ttsEngine === "melo" && (
            <Badge variant="amber" title="無法連線，改用離線內建語音（所選線上語音暫不生效）">
              離線語音
            </Badge>
          )}
        </div>

        {/* 已選圖片預覽 chip */}
        {imageUrl && (
          <div className="mb-2 flex items-center gap-2 px-1">
            <img src={imageUrl} alt="預覽" className="h-12 w-12 rounded-lg object-cover" />
            <span className="text-xs text-muted-foreground">{image?.name}</span>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={clearImage} aria-label="移除圖片">
              <X strokeWidth={1.75} />
            </Button>
          </div>
        )}

        <div className="flex items-end gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => pickImage(e.target.files?.[0] ?? null)}
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fileRef.current?.click()}
            disabled={loading}
            aria-label="上傳圖片做 OCR"
            title="上傳圖片做 OCR"
          >
            <UploadCloud strokeWidth={1.75} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={generateImage}
            disabled={!canGenImage}
            aria-label="用文字生成圖片"
            title="用文字生成圖片"
          >
            <ImagePlus strokeWidth={1.75} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={refineImage}
            disabled={!canRefine}
            aria-label="微調上一張生成圖"
            title="微調上一張生成圖（以文字修改，保留原構圖）"
          >
            <Wand2 strokeWidth={1.75} />
          </Button>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={image ? "可補充指示（例：翻成英文）…" : "輸入訊息…（Enter 送出，Shift+Enter 換行）"}
            className="min-h-[48px] flex-1 border-0 bg-transparent focus-visible:ring-0"
            rows={1}
          />
          <Button variant="gradient" size="icon" onClick={send} disabled={!canSend}>
            {loading ? <Loader2 className="animate-spin" strokeWidth={1.75} /> : <Send strokeWidth={1.75} />}
          </Button>
        </div>
      </div>
    </div>
  );
}
