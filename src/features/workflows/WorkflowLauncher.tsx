import { ArrowRight, ShieldCheck } from "lucide-react";
import { FormEvent, useState } from "react";

interface Props {
  busy: boolean;
  error: string | null;
  onLaunch: (ticker: string) => Promise<void>;
}

const tickerPattern = /^(?:\d{6}\.(?:SZ|SH|BJ)|\d{5}\.HK|[A-Z][A-Z0-9.-]{0,9})$/;

export default function WorkflowLauncher({ busy, error, onLaunch }: Props) {
  const [ticker, setTicker] = useState("");
  const normalized = ticker.trim().toUpperCase();
  const valid = tickerPattern.test(normalized);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (valid && !busy) await onLaunch(normalized);
  }

  return (
    <section className="launcher">
      <div>
        <p className="eyebrow">今日研究</p>
        <h1>从一个标的开始研究</h1>
        <p>连接本地证据、数据新鲜度与研究记忆，形成一条可复查、可沉淀的研究链。</p>
      </div>
      <form onSubmit={submit}>
        <label htmlFor="ticker">研究标的</label>
        <div className="ticker-entry">
          <input
            id="ticker"
            value={ticker}
            onChange={(event) => setTicker(event.target.value)}
            placeholder="例如 300308.SZ"
            autoComplete="off"
          />
          <button type="submit" disabled={!valid || busy}>
            {busy ? "正在排队" : "开始深挖"}<ArrowRight size={17} />
          </button>
        </div>
        <span className="local-only"><ShieldCheck size={14} /> 本地优先 · 不自动联网 · 不执行交易</span>
        {ticker && !valid ? <p className="field-hint">请输入标准市场代码，如 600519.SH。</p> : null}
        {error ? <p className="launch-error" role="alert">{error}</p> : null}
      </form>
    </section>
  );
}
