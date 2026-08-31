/* ===== 注册：第一个注册用户自动成为管理员 ===== */

import { hashPassword } from "../../lib/password.js";
import { json } from "../../lib/util.js";

export async function onRequestPost(context) {
  var body = await context.request.json().catch(function () { return null; });
  if (!body) return json({ ok: false, error: "请求格式错误" }, 400);

  var email = String(body.email || "").trim().toLowerCase();
  var password = String(body.password || "");

  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ ok: false, error: "邮箱格式不正确" });
  if (password.length < 6) return json({ ok: false, error: "密码至少 6 位" });

  var existing = await context.env.YUNYOU_AUTH_KV.get("user:" + email);
  if (existing) return json({ ok: false, error: "该邮箱已注册" });

  var users = (await context.env.YUNYOU_AUTH_KV.get("users:list", "json")) || [];
  var role = users.length === 0 ? "admin" : "user";   // 第一位注册者 = 管理员
  users.push(email);
  await context.env.YUNYOU_AUTH_KV.put("users:list", JSON.stringify(users));

  var h = await hashPassword(password);
  await context.env.YUNYOU_AUTH_KV.put(
    "user:" + email,
    JSON.stringify({ hash: h.hashHex, salt: h.saltHex, role: role, created: Date.now() })
  );

  return json({ ok: true, role: role, msg: role === "admin" ? "注册成功：您是第一位用户，已自动成为管理员" : "注册成功" });
}
