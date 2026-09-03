/**
 * RescueAI Vercel Function: POST /ai/proxy
 * 与 backend/Qwen 初版/ai_proxy.py 的 /ai/proxy 契约完全对齐：
 *   - 请求体：{ model, messages, enable_thinking?, temperature?, response_format? }（白名单外参数丢弃）
 *   - 成功：原样透传 DashScope 兼容模式响应（前端取 data.choices[0].message.content）
 *   - 无 Key / 上游失败 / 超时：200 + { fallback: true, reason }（前端 callAI 据此走预录兜底）
 * 密钥仅从 Vercel 环境变量 DASHSCOPE_API_KEY 读取，严禁硬编码。
 */

const DASHSCOPE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions';
const UPSTREAM_TIMEOUT_MS = 8000; // 上游调用 ~8s，保证函数整体 ≤ Vercel Hobby 10s 限制
const PASS_KEYS = ['enable_thinking', 'temperature', 'response_format'];

// 缺省模型与 ai_proxy.py / 前端 AI_CFG 一致；可经环境变量覆盖
const DEFAULT_TEXT_MODEL = 'qwen3.8-max';
const DEFAULT_VL_MODEL = 'qwen3.7-plus';

export const config = { maxDuration: 10 };

function fallback(res, reason) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ fallback: true, reason: String(reason || 'unknown').slice(0, 200) });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(404).json({ error: 'not found' });
  }
  try {
    const body = typeof req.body === 'object' && req.body !== null ? req.body : {};
    const messages = body.messages;
    if (!Array.isArray(messages) || messages.length === 0) {
      return fallback(res, 'messages 缺失或格式错误');
    }

    // 模型映射：前端请求的默认模型可被环境变量覆盖（其他模型名原样透传）
    const textModel = process.env.DASHSCOPE_TEXT_MODEL || DEFAULT_TEXT_MODEL;
    const vlModel = process.env.DASHSCOPE_VL_MODEL || DEFAULT_VL_MODEL;
    let model = body.model || DEFAULT_TEXT_MODEL;
    if (model === DEFAULT_TEXT_MODEL) model = textModel;
    else if (model === DEFAULT_VL_MODEL) model = vlModel;

    // 白名单参数透传；enable_thinking 默认注入 false（同 ai_proxy.py）
    const extra = {};
    for (const k of PASS_KEYS) if (k in body) extra[k] = body[k];
    if (!('enable_thinking' in extra)) extra.enable_thinking = false;

    const key = process.env.DASHSCOPE_API_KEY;
    if (!key) {
      return fallback(res, '未配置 DASHSCOPE_API_KEY（请在 Vercel 控制台添加环境变量后重新部署）');
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), UPSTREAM_TIMEOUT_MS);
    let upstream;
    try {
      upstream = await fetch(DASHSCOPE_URL, {
        method: 'POST',
        signal: ctrl.signal,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + key,
        },
        body: JSON.stringify({ model, messages, ...extra }),
      });
    } finally {
      clearTimeout(timer);
    }

    if (!upstream.ok) {
      return fallback(res, '上游 HTTP ' + upstream.status);
    }
    const data = await upstream.json();
    if (!data || !data.choices || !data.choices.length) {
      return fallback(res, '上游响应缺少 choices');
    }
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', 'no-store');
    res.status(200).json(data);
  } catch (e) {
    return fallback(res, e && e.name === 'AbortError' ? '上游调用超时' : (e && e.message) || String(e));
  }
}
