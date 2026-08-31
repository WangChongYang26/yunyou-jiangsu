/* ===== 保存数据（云端）：仅管理员可写，整包写入 KV ===== */

import { getSession } from "../lib/session.js";
import { json } from "../lib/util.js";

export async function onRequestPost(context) {
  var s = await getSession(context.request, context.env);
  if (!s) return json({ ok: false, error: "未登录或登录已过期，请重新登录" }, 401);
  if (s.role !== "admin") return json({ ok: false, error: "无权限：只有管理员可以修改内容" }, 403);

  var body = await context.request.json().catch(function () { return null; });
  if (!body || !Array.isArray(body.data)) return json({ ok: false, error: "数据格式错误" }, 400);

  await context.env.YUNYOU_DATA_KV.put("data:full", JSON.stringify(body.data));
  return json({ ok: true, msg: "已保存到云端，刷新前台即生效" });
}
