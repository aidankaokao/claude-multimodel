import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Check, Loader2, Save, X, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { usePageHeader } from "@/stores/pageHeader";
import { api } from "@/lib/api";

type Provider = {
  id: number;
  name: string;
  provider: "ollama" | "openai";
  base_url: string;
  model: string;
  api_key_masked: string;
  has_api_key: boolean;
  temperature: number;
  is_active: boolean;
};

type FormState = {
  name: string;
  provider: "ollama" | "openai";
  base_url: string;
  model: string;
  api_key: string;
  temperature: number;
};

const EMPTY: FormState = {
  name: "",
  provider: "ollama",
  base_url: "http://localhost:11434",
  model: "",
  api_key: "",
  temperature: 0,
};

// 切 provider 時給合理預設 base_url（僅在使用者尚未自行填時提示）。
const DEFAULT_BASE: Record<string, string> = {
  ollama: "http://localhost:11434",
  openai: "https://api.openai.com/v1",
};

export function SettingsProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null); // null=不在編輯
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    usePageHeader.getState().set("LLM Provider", "註冊多個 Ollama / OpenAI / vLLM，並選一個來用");
    void load();
  }, []);

  async function load() {
    setLoading(true);
    try {
      setProviders(await api.get<Provider[]>("/settings/llm-providers"));
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY);
    setShowForm(true);
  }

  function openEdit(p: Provider) {
    setEditingId(p.id);
    setForm({
      name: p.name,
      provider: p.provider,
      base_url: p.base_url,
      model: p.model,
      api_key: "", // 留空 = 不更動既有金鑰
      temperature: p.temperature,
    });
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(EMPTY);
  }

  async function save() {
    if (!form.name.trim() || !form.base_url.trim() || !form.model.trim()) {
      toast.error("請填寫 名稱 / base_url / 模型");
      return;
    }
    setSaving(true);
    try {
      if (editingId === null) {
        await api.post("/settings/llm-providers", form);
        toast.success("已新增 provider");
      } else {
        await api.put(`/settings/llm-providers/${editingId}`, form);
        toast.success("已更新 provider");
      }
      closeForm();
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(p: Provider) {
    if (!confirm(`確定刪除「${p.name}」？`)) return;
    try {
      await api.del(`/settings/llm-providers/${p.id}`);
      toast.success("已刪除");
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  async function setActive(p: Provider) {
    try {
      await api.put("/settings/llm-active", { provider_id: p.id });
      toast.success(`已選用「${p.name}」`);
      await load();
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-gradient">LLM Provider</span> 設定
          </h1>
          <p className="text-sm text-muted-foreground">
            provider 存後端資料庫，金鑰不回傳明文（只顯示遮罩）。
          </p>
        </div>
        {!showForm && (
          <Button variant="gradient" onClick={openCreate}>
            <Plus strokeWidth={1.75} /> 新增
          </Button>
        )}
      </div>

      {/* 新增 / 編輯表單 */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId === null ? "新增 provider" : "編輯 provider"}</CardTitle>
            <CardDescription>
              vLLM 走 OpenAI 相容 API：provider 選 openai、base_url 指到 vLLM 的 /v1、金鑰可填 EMPTY。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>顯示名稱</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例：本地 Ollama - qwen2.5"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>後端類型</Label>
                <Select
                  value={form.provider}
                  onChange={(e) => {
                    const provider = e.target.value as FormState["provider"];
                    setForm((f) => ({
                      ...f,
                      provider,
                      base_url: f.base_url && f.base_url !== DEFAULT_BASE[f.provider]
                        ? f.base_url
                        : DEFAULT_BASE[provider],
                    }));
                  }}
                >
                  <option value="ollama">ollama（本地 Ollama）</option>
                  <option value="openai">openai（外部 OpenAI / 本地 vLLM）</option>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>temperature</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={form.temperature}
                  onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>base_url</Label>
              <Input
                value={form.base_url}
                onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                placeholder={DEFAULT_BASE[form.provider]}
              />
            </div>

            <div className="space-y-1.5">
              <Label>模型名稱</Label>
              <Input
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder={form.provider === "ollama" ? "例：qwen2.5:7b" : "例：gpt-4o-mini / Qwen/Qwen2.5-7B-Instruct"}
              />
            </div>

            {form.provider === "openai" && (
              <div className="space-y-1.5">
                <Label>api_key {editingId !== null && <span className="text-muted-foreground">(留空 = 不更動)</span>}</Label>
                <Input
                  type="password"
                  value={form.api_key}
                  onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  placeholder={editingId !== null ? "留空保留原金鑰" : "sk-... 或 EMPTY（vLLM）"}
                />
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={closeForm} disabled={saving}>
                <X strokeWidth={1.75} /> 取消
              </Button>
              <Button variant="gradient" onClick={save} disabled={saving}>
                {saving ? <Loader2 className="animate-spin" strokeWidth={1.75} /> : <Save strokeWidth={1.75} />}
                儲存
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 清單 */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.75} /> 載入中…
        </div>
      ) : providers.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            尚未註冊任何 provider。點右上「新增」建立第一個。
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {providers.map((p) => (
            <Card key={p.id} className="transition-transform hover:-translate-y-0.5">
              <CardContent className="flex items-center gap-4 p-5">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-semibold">{p.name}</span>
                    <Badge variant={p.provider === "ollama" ? "teal" : "indigo"}>{p.provider}</Badge>
                    {p.is_active && (
                      <Badge variant="green">
                        <Check className="mr-0.5 h-3 w-3" strokeWidth={2} /> 使用中
                      </Badge>
                    )}
                  </div>
                  <div className="mt-1 truncate text-xs text-muted-foreground">
                    {p.model} · {p.base_url}
                    {p.has_api_key && ` · key ${p.api_key_masked}`}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  {!p.is_active && (
                    <Button variant="secondary" size="sm" onClick={() => setActive(p)}>
                      <CheckCircle2 strokeWidth={1.75} /> 選用
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" onClick={() => openEdit(p)} aria-label="編輯">
                    <Pencil strokeWidth={1.75} />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => remove(p)} aria-label="刪除">
                    <Trash2 className="text-destructive" strokeWidth={1.75} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
