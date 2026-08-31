/* ===== 退出：删除会话并清空 Cookie ===== */

import { parseCookie, json } from "../../lib/util.js";

export async function onRequestPost(context) {
  var cookie = parseCookie(context.request.headers.get("Cookie") || "");
  if (cookie.yb_session) {
    await context.env.YUNYOU_AUTH_KV.delete("session:" + cookie.yb_session);
  }
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Set-Cookie": "yb_session=; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=0"
    }
  });
}
