/* ===== 云游江苏 · 云端数据优先 =====
 * 部署在 https（Cloudflare Pages）时：从 /api/data 拉取云端最新内容，
 * 成功则覆盖本地 city_data.js 的默认数据（后台在云端保存后全站立刻生效）。
 * 本地 http / file 打开时跳过，直接用 city_data.js。
 */
(function () {
  if (!/^https:/.test(location.protocol)) return;
  fetch("api/data", { headers: { Accept: "application/json" } })
    .then(function (r) { return r.json(); })
    .then(function (obj) {
      if (obj && obj.ok && obj.data && obj.data.length) {
        window.__CITY_DATA__ = obj.data;
      }
    })
    .catch(function () { /* 云端不可用时回退本地默认数据 */ });
})();
