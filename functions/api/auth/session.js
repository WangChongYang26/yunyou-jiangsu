/* ===== 查询当前登录状态 ===== */

import { getSession } from "../../lib/session.js";
import { json } from "../../lib/util.js";

export async function onRequestGet(context) {
  var s = await getSession(context.request, context.env);
  if (!s) return json({ ok: false, authed: false });
  return json({ ok: true, authed: true, email: s.email, role: s.role });
}
