/* ===== 会话读取 ===== */

import { parseCookie } from "./util.js";

/* 从请求 Cookie 中解析有效会话；无效返回 null */
export async function getSession(request, env) {
  var cookie = parseCookie(request.headers.get("Cookie") || "");
  var token = cookie.yb_session;
  if (!token) return null;
  var rec = await env.YUNYOU_AUTH_KV.get("session:" + token);
  if (!rec) return null;
  var s = JSON.parse(rec);
  if (s.exp < Date.now()) {
    await env.YUNYOU_AUTH_KV.delete("session:" + token);
    return null;
  }
  return s;
}
