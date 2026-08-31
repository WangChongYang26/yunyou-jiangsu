/* ===== 登录：校验密码，签发会话 Cookie（7 天） ===== */

import { verifyPassword, randomToken } from "../../lib/password.js";
import { json } from "../../lib/util.js";

var SESSION_TTL = 7 * 24 * 3600; // 秒

export async function onRequestPost(context) {
  var body = await context.request.json().catch(function () { return null; });
  if (!body) return json({ ok: false, error: "请求格式错误" }, 400);

  var email = String(body.email || "").trim().toLowerCase();
  var password = String(body.password || "");

  var rec = await context.env.YUNYOU_AUTH_KV.get("user:" + email);
  if (!rec) return json({ ok: false, error: "邮箱或密码错误" });

  var u = JSON.parse(rec);
  var ok = await verifyPassword(password, u.salt, u.hash);
  if (!ok) return json({ ok: false, error: "邮箱或密码错误" });

  var token = randomToken();
  var exp = Date.now() + SESSION_TTL * 1000;
  await context.env.YUNYOU_AUTH_KV.put("session:" + token, JSON.stringify({ email: email, role: u.role, exp: exp }), { expirationTtl: SESSION_TTL });

  return new Response(JSON.stringify({ ok: true, email: email, role: u.role }), {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Set-Cookie": "yb_session=" + token + "; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=" + SESSION_TTL
    }
  });
}
