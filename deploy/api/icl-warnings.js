/**
 * RescueAI Vercel Function: GET /icl/warnings
 * 与 backend/Qwen 初版/ai_proxy.py 的 /icl/warnings 契约对齐：
 *   - 响应 { code:0, message:"", data:[...], offline?:true }
 *   - 前端取 j.data 数组；j.offline === true 时标签切「离线快照数据」
 * 线上版固定走快照（ICL 上游对海外机房不稳定）：
 *   优先 JSON 模块导入 deploy/data/icl_warnings_snapshot.json（打包时必然内联，与后端同源快照），
 *   导入异常回落内嵌最小样例。始终返回 200 + 合法 JSON，消除前端 console 报错。
 */
import iclSnapshot from '../data/icl_warnings_snapshot.json' with { type: 'json' };

export const config = { maxDuration: 10 };

// 内嵌最小样例（与 ai_proxy.py OFFLINE_ICL 一致），快照文件不可读时的末级兜底
const OFFLINE_ICL = {
  code: 0,
  message: '',
  offline: true,
  data: [
    { eventId: 1784356492, epicenter: '四川宜宾市高县', magnitude: 5.1, depth: 5, epiIntensity: 7, startAt: 1785694905000, updates: 2, sourceType: 1 },
    { eventId: 1784356491, epicenter: '新疆阿克苏地区乌什县', magnitude: 4.6, epiIntensity: 6, startAt: 1785305399100, updates: 3, sourceType: 2 },
    { eventId: 1784343985, epicenter: '新疆克孜勒苏州阿克陶县', magnitude: 4.4, epiIntensity: 5.6, startAt: 1784353639800, updates: 2, sourceType: 2 },
  ],
};

function sendJson(res, obj) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=300'); // 与本地代理 300s 缓存语义一致
  res.status(200).json(obj);
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(404).json({ error: 'not found' });
  }
  try {
    const snap = JSON.parse(JSON.stringify(iclSnapshot));
    if (!Array.isArray(snap.data) || snap.data.length === 0) throw new Error('快照 data 为空');
    snap.offline = true;
    return sendJson(res, snap);
  } catch (e) {
    return sendJson(res, OFFLINE_ICL);
  }
}
