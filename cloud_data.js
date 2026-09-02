/* ===== 云游江苏 · 云端数据优先 =====
 * 【2026-09-02 停用】根因修复：
 *   线上 KV(YUNYOU_DATA_KV data:full) 里残留了拆分前的旧数据(南京仅3条,含合并的
 *   "明城墙·秦淮河")，cloud_data.js 每次用 /api/data 返回的旧 KV 数据覆盖本地
 *   city_data.js 的新版 4 条，导致全站永远显示旧数据。
 *   团队实际工作流 = 后台(server.py) 写回 js 文件 → git push 部署，
 *   线上后台(auth/save) 从未使用，故停用云端覆盖，直接以静态 city_data.js 为准。
 *   如需恢复线上后台保存生效，先清理 KV 的 data:full（wrangler kv delete 或
 *   Dashboard 手动删），再恢复下方代码。
 * 本地 http / file 打开时本就跳过，直接用 city_data.js。
 */
(function () {
  // 停用云端覆盖（历史遗留数据会压过静态新版，见文件头注释）
  if (1) return;
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
