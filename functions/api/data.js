/* ===== 读取数据：KV 有云端保存内容则返回云端版，否则回退静态 city_data.js ===== */

import { json } from "../lib/util.js";

export async function onRequestGet(context) {
  var cached = await context.env.YUNYOU_DATA_KV.get("data:full");
  if (cached) {
    try {
      return json({ ok: true, data: JSON.parse(cached), source: "cloud" });
    } catch (e) {
      /* 云端数据损坏时忽略，走回退 */
    }
  }
  // 回退：解析同一次部署里的 city_data.js 静态文件
  try {
    var url = new URL("/city_data.js", context.request.url);
    var res = await context.env.ASSETS.fetch(url);
    var text = await res.text();
    var start = text.indexOf("[");
    var end = text.lastIndexOf("]");
    if (start < 0 || end <= start) return json({ ok: false, error: "city_data.js 解析失败" }, 500);
    var data = JSON.parse(text.slice(start, end + 1));
    return json({ ok: true, data: data, source: "default" });
  } catch (e) {
    return json({ ok: false, error: "数据读取失败: " + e.message }, 500);
  }
}
