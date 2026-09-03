/**
 * RescueAI Vercel Function: GET /seismic/feed
 * 与 backend/Qwen 初版/ai_proxy.py 的 /seismic/feed 契约对齐：
 *   - 响应为 USGS GeoJSON FeatureCollection（前端 normSeismic 解析）
 *   - 兜底样例带 offline:true（前端据此标「离线样例数据」，不算实时接入）
 * 线上策略：优先实时拉 USGS all_hour.geojson（7s 超时），失败回落与 ai_proxy.py
 * 完全一致的 OFFLINE_QUAKE 内嵌样例。data/ 下无 USGS 历史快照文件，故采用
 * 「实时 + 内嵌样例」两级结构（与本地代理语义相同）。始终返回 200 + 合法 JSON。
 */

const USGS_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson';
const UPSTREAM_TIMEOUT_MS = 7000;

export const config = { maxDuration: 10 };

// 与 ai_proxy.py OFFLINE_QUAKE 完全一致的离线样例（USGS GeoJSON 格式）
const OFFLINE_QUAKE = {
  type: 'FeatureCollection',
  offline: true,
  metadata: { generated: 0, title: 'USGS Earthquakes (offline sample)', status: 200, count: 4, api: 'offline' },
  features: [
    { type: 'Feature', id: 'sample001', properties: { mag: 4.2, place: 'San Juan Bautista, CA', time: 1672555748370, type: 'earthquake', sig: 271, title: 'M 4.2 - San Juan Bautista, CA' }, geometry: { type: 'Point', coordinates: [-121.199, 36.595, 8.4] } },
    { type: 'Feature', id: 'sample002', properties: { mag: 3.1, place: '10km SW of Idyllwild, CA', time: 1672554912000, type: 'earthquake', sig: 148, title: 'M 3.1 - 10km SW of Idyllwild, CA' }, geometry: { type: 'Point', coordinates: [-116.766, 33.7, 14.2] } },
    { type: 'Feature', id: 'sample003', properties: { mag: 2.7, place: '12km NE of Ridgecrest, CA', time: 1672553500120, type: 'earthquake', sig: 112, title: 'M 2.7 - 12km NE of Ridgecrest, CA' }, geometry: { type: 'Point', coordinates: [-117.59, 35.697, 6.1] } },
    { type: 'Feature', id: 'sample004', properties: { mag: 3.6, place: '8km W of Cobb, CA', time: 1672552870450, type: 'earthquake', sig: 199, title: 'M 3.6 - 8km W of Cobb, CA' }, geometry: { type: 'Point', coordinates: [-122.77, 38.82, 2.9] } },
  ],
};

function sendJson(res, obj) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=300'); // 对应本地代理 300s 内存缓存
  res.status(200).json(obj);
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(404).json({ error: 'not found' });
  }
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), UPSTREAM_TIMEOUT_MS);
    let upstream;
    try {
      upstream = await fetch(USGS_URL, { signal: ctrl.signal, headers: { 'User-Agent': 'RescueAI-VercelProxy/1.0' } });
    } finally {
      clearTimeout(timer);
    }
    if (!upstream.ok) throw new Error('上游 HTTP ' + upstream.status);
    const data = await upstream.json();
    if (!data || !Array.isArray(data.features) || data.features.length === 0) {
      throw new Error('上游返回空 features');
    }
    return sendJson(res, data);
  } catch (e) {
    return sendJson(res, OFFLINE_QUAKE);
  }
}
