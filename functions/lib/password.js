/* ===== 密码哈希（PBKDF2-SHA256）+ 随机令牌 =====
 * 密码绝不存明文：盐 + 哈希。
 * 会话令牌用 Web Crypto 随机生成，存入 KV。
 */

var enc = new TextEncoder();

function bytesToHex(b) {
  return Array.from(b, function (x) { return x.toString(16).padStart(2, "0"); }).join("");
}

function hexToBytes(hex) {
  var out = new Uint8Array(hex.length / 2);
  for (var i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return out;
}

export async function hashPassword(password, saltHex) {
  var salt = saltHex ? hexToBytes(saltHex) : crypto.getRandomValues(new Uint8Array(16));
  var key = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  var bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: salt, iterations: 60000, hash: "SHA-256" },
    key, 256
  );
  return { saltHex: bytesToHex(salt), hashHex: bytesToHex(new Uint8Array(bits)) };
}

export async function verifyPassword(password, saltHex, hashHex) {
  var r = await hashPassword(password, saltHex);
  return r.hashHex === hashHex;
}

export function randomToken() {
  return bytesToHex(crypto.getRandomValues(new Uint8Array(32)));
}
