/* ===== 云游江苏 · Cloudflare Functions 通用工具 ===== */

export function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { "Content-Type": "application/json; charset=utf-8" }
  });
}

/* 解析 Cookie 头为对象 */
export function parseCookie(header) {
  var out = {};
  if (!header) return out;
  header.split(";").forEach(function (part) {
    var i = part.indexOf("=");
    if (i < 0) return;
    var k = part.slice(0, i).trim();
    var v = part.slice(i + 1).trim();
    if (k) out[k] = v;
  });
  return out;
}
