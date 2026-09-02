/* ===== 云游江苏 主逻辑 ===== */
(function () {
  "use strict";

  /* ---------- 视图切换（带淡出/淡入过渡） ---------- */
  var FADE_MS = 260;
  var switching = false;
  function showView(id) {
    if (switching) return;                       // 过渡进行中忽略重复点击
    var current = document.querySelector('.view.active');
    var target = document.getElementById(id);
    if (!target || target === current) return;

    // 首次启动无当前视图，直接显示
    if (!current) { target.classList.add('active'); return; }

    switching = true;
    // 1) 当前视图淡出
    current.style.transition = 'opacity ' + FADE_MS + 'ms ease';
    current.style.opacity = '0';
    setTimeout(function () {
      // 2) 切换视图（示意图/详情在此刻完成替换）
      current.classList.remove('active');
      current.style.transition = '';
      current.style.opacity = '';

      target.classList.add('active');
      target.style.opacity = '0';
      target.style.transition = 'opacity ' + FADE_MS + 'ms ease';
      // 3) 新视图淡入
      requestAnimationFrame(function () { target.style.opacity = '1'; });
      setTimeout(function () {
        target.style.transition = '';
        target.style.opacity = '';
        switching = false;
      }, FADE_MS + 40);

      window.scrollTo(0, 0);
      if (id === 'viewMap') buildMap();
    }, FADE_MS);
  }
  document.querySelectorAll('[data-view]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      showView(el.getAttribute('data-view'));
    });
  });
  ['backBtn', 'backBtn2', 'backBtn3'].forEach(function (id) {
    var b = document.getElementById(id);
    if (b) b.addEventListener('click', function () {
      showView(id === 'backBtn2' ? 'viewMap' : 'viewMenu');
    });
  });
  window.__showView = showView;

  /* ---------- 主菜单背景图预加载（加载完成后才淡入，避免边加载边显示） ---------- */
  [
    { id: 'bgSplit', src: 'bg/main_split.jpg' }
  ].forEach(function (item) {
    var img = new Image();
    img.onload = function () {
      var el = document.getElementById(item.id);
      if (el) el.classList.add('loaded');
    };
    img.onerror = function () {
      var el = document.getElementById(item.id);
      if (el) el.classList.add('loaded');   // 加载失败也显示（可能有路径问题，保持页面不空）
    };
    img.src = item.src;
  });

  /* ---------- 站点信息（主标题/副标题/版本行，后台可编辑） ---------- */
  var siteCfg = window.__SITE_CONFIG__ || {};
  function applySiteCfg() {
    if (siteCfg.title) {
      var tEl = document.getElementById('siteTitle');
      if (tEl) tEl.textContent = siteCfg.title;
      var sub = siteCfg.subtitle || '';
      document.title = siteCfg.title + (sub.indexOf('· ') >= 0 ? ' · ' + sub.split('· ').pop() : '');
    }
    if (siteCfg.subtitle) {
      var sEl = document.getElementById('siteSubtitle');
      if (sEl) sEl.textContent = siteCfg.subtitle;
    }
    if (siteCfg.version) {
      var vEl = document.getElementById('versionText');
      if (vEl) vEl.textContent = siteCfg.version;
    }
    if (siteCfg.copyright) {
      var cEl = document.getElementById('copyrightText');
      if (cEl) cEl.textContent = siteCfg.copyright;
    }
  }
  applySiteCfg();

  /* ---------- BGM ---------- */
  var bgm = document.getElementById('bgm');
  var tip = document.getElementById('bgmTip');
  var playing = false;
  // 从 songs.js 读取歌曲列表：默认播放第一首
  var songs = window.__SONGS__ || [];
  var currentSong = songs.length ? songs[0] : null;
  var picker = null;

  function setSongName(name) {
    document.querySelectorAll('.musicName').forEach(function (s) { s.textContent = name; });
  }
  if (currentSong) {
    bgm.src = currentSong.file;
    setSongName(currentSong.name);
  }
  function syncBtn() {
    document.querySelectorAll('#musicBtn').forEach(function (b) {
      b.textContent = playing ? '♪ 关' : '♪ 开';
      b.classList.toggle('off', !playing);
    });
  }
  function playMusic() {
    if (playing) return;
    bgm.volume = 0.7;
    bgm.play().then(function () {
      playing = true;
      if (tip) tip.classList.add('hidden');
      syncBtn();
    }).catch(function () {});
  }
  function stopMusic() { if (!playing) return; bgm.pause(); playing = false; syncBtn(); }

  // ---- 选歌面板 ----
  function switchSong(song) {
    currentSong = song;
    bgm.src = song.file;
    setSongName(song.name);
    playing = false;          // 换歌后重新播放（主动点击，不受自动播放限制）
    bgm.load();
    playMusic();
    hidePicker();
  }
  function buildPicker() {
    if (!songs.length) return;
    picker = document.createElement('div');
    picker.id = 'songPicker';
    picker.style.display = 'none';
    songs.forEach(function (s) {
      var item = document.createElement('button');
      item.type = 'button';
      item.className = 'song-pick-item';
      item.textContent = s.name;
      item.addEventListener('click', function () { switchSong(s); });
      picker.appendChild(item);
    });
    document.body.appendChild(picker);
  }
  function highlightPicker() {
    if (!picker) return;
    var items = picker.querySelectorAll('.song-pick-item');
    items.forEach(function (it) {
      it.classList.toggle('active', it.textContent === (currentSong && currentSong.name));
    });
  }
  function showPicker(anchor) {
    if (!picker) buildPicker();
    if (!picker) return;
    highlightPicker();
    var r = anchor.getBoundingClientRect();
    var w = picker.offsetWidth || 190;
    var left = Math.min(r.left, window.innerWidth - w - 12);
    picker.style.left = Math.max(12, left) + 'px';
    picker.style.top = (r.bottom + 8) + 'px';
    picker.style.display = 'block';
  }
  function hidePicker() { if (picker) picker.style.display = 'none'; }

  // 点击歌名 → 弹出选歌列表（右上角音乐条）
  document.querySelectorAll('.musicName').forEach(function (el) {
    el.style.cursor = 'pointer';
    el.title = '点击切换背景音乐';
    el.addEventListener('click', function (e) {
      e.stopPropagation();
      if (picker && picker.style.display === 'block') { hidePicker(); return; }
      showPicker(el);
    });
  });
  document.addEventListener('click', function (e) {
    if (picker && picker.style.display === 'block' &&
        !e.target.closest('#songPicker') && !e.target.classList.contains('musicName')) {
      hidePicker();
    }
  });
  window.addEventListener('resize', hidePicker);

  // 仅手动点击音乐按钮才播放，不做任何自动触发
  document.querySelectorAll('#musicBtn').forEach(function (b) {
    b.addEventListener('click', function () { playing ? stopMusic() : playMusic(); });
  });
  syncBtn();

  /* ---------- 星空粒子 ---------- */
  var cv = document.getElementById('stars');
  var ctx = cv.getContext('2d');
  var W, H, stars = [];
  function resize() {
    W = cv.width = innerWidth;
    H = cv.height = innerHeight;
    var n = Math.min(160, Math.floor(W * H / 15000));
    stars = Array.from({ length: n }, function () {
      return { x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.5 + 0.3, sp: Math.random() * 0.3 + 0.05, tw: Math.random() * 6.28 };
    });
  }
  function tick() {
    ctx.clearRect(0, 0, W, H);
    stars.forEach(function (s) {
      s.y -= s.sp;
      if (s.y < -4) { s.y = H + 4; s.x = Math.random() * W; }
      s.tw += 0.04;
      var a = 0.3 + 0.5 * Math.abs(Math.sin(s.tw));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, 6.28);
      ctx.fillStyle = 'rgba(190, 225, 255,' + a.toFixed(3) + ')';
      ctx.fill();
    });
    requestAnimationFrame(tick);
  }
  addEventListener('resize', resize);
  resize();
  tick();

  /* ---------- SVG 江苏地图（真实市级边界，DataV GeoAtlas 数据投影） ---------- */
  var mapBuilt = false;
  var NS = 'http://www.w3.org/2000/svg';

  // 城市是否开放云游：由管理后台（admin）每城市的"开放云游"开关控制，
  // 数据存于 city_data.js 的 open 字段（open === false 为锁定，缺省视为开放）
  function isOpen(id) {
    if (!id) return false;
    var data = window.__CITY_DATA__ || [];
    var city = null;
    for (var i = 0; i < data.length; i++) {
      if (data[i].id === id) { city = data[i]; break; }
    }
    if (!city) return false;      // 找不到该城市数据 → 不可进入
    return city.open !== false;
  }

  function cityShort(full) { return full.replace(/市$/, ''); }

  // 13 市配色（青蓝系，相邻市错开）
  var REGION_COLORS = [
    '#123c55', '#0d3650', '#14435f', '#0f3a52',
    '#16465f', '#113a4e', '#12415c', '#0e3450',
    '#14405c', '#0f3a52', '#164760', '#11384e',
    '#12405a'
  ];

  function buildMap() {
    if (mapBuilt) return;
    mapBuilt = true;
    var data = window.__CITY_DATA__ || [];
    var mapData = window.__JIANGSU_MAP__ || [];
    var regions = document.getElementById('cityRegions');
    var listBtns = document.getElementById('cityListBtns');
    if (!regions) return;

    // 标签单独放一个顶层 group，避免被后绘制的相邻市区域遮挡
    var labelsG = document.createElementNS(NS, 'g');
    labelsG.setAttribute('id', 'cityLabels');
    regions.parentNode.insertBefore(labelsG, regions.nextSibling);

    // name -> city 对象（city_data 用 full 全名匹配）
    function findCity(mc) {
      for (var i = 0; i < data.length; i++) {
        if (data[i].full === mc.name) return data[i];
      }
      return null;
    }

    mapData.forEach(function (mc, idx) {
      var city = findCity(mc);
      var g = document.createElementNS(NS, 'g');
      var locked = !isOpen(city && city.id);
      g.setAttribute('class', 'region' + (locked ? ' locked' : ''));
      g.setAttribute('data-city', city ? city.id : ('c' + idx));
      g.setAttribute('role', 'button');
      g.setAttribute('tabindex', '0');
      g.setAttribute('aria-disabled', locked ? 'true' : 'false');
      g.setAttribute('aria-label', locked ? (cityShort(mc.name) + '：前方的道路，以后再来探索') : ('进入' + (city ? city.name : cityShort(mc.name))));

      var fill = REGION_COLORS[idx % REGION_COLORS.length];
      mc.paths.forEach(function (d) {
        var p = document.createElementNS(NS, 'path');
        p.setAttribute('d', d);
        p.setAttribute('fill', fill);
        p.setAttribute('stroke', 'rgba(190,225,255,0.6)');
        p.setAttribute('stroke-width', '1');
        g.appendChild(p);
      });

      g.addEventListener('click', function () { openCity(city ? city.id : null); });
      g.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openCity(city ? city.id : null); }
      });
      regions.appendChild(g);

      // 顶层标签：半透明底板 + 市名
      var short = city ? city.name : cityShort(mc.name);
      var labelG = document.createElementNS(NS, 'g');
      labelG.setAttribute('class', 'region-label-g' + (locked ? ' locked' : ''));
      labelG.setAttribute('data-city', city ? city.id : ('c' + idx));
      labelG.setAttribute('aria-hidden', 'true');

      var textW = short.length * 13 + 8;   // 13px/字 + 间距
      var bg = document.createElementNS(NS, 'rect');
      bg.setAttribute('x', mc.cx - textW / 2);
      bg.setAttribute('y', mc.cy - 13);
      bg.setAttribute('width', textW);
      bg.setAttribute('height', 26);
      bg.setAttribute('rx', 13);
      bg.setAttribute('fill', 'rgba(6, 18, 34, 0.82)');
      bg.setAttribute('stroke', 'rgba(140,200,255,0.4)');
      bg.setAttribute('stroke-width', '0.8');

      var label = document.createElementNS(NS, 'text');
      label.setAttribute('class', 'region-label');
      label.setAttribute('x', mc.cx);
      label.setAttribute('y', mc.cy);
      label.setAttribute('text-anchor', 'middle');
      label.setAttribute('dominant-baseline', 'central');
      label.textContent = short;

      labelG.appendChild(bg);
      labelG.appendChild(label);
      labelG.addEventListener('click', function () { openCity(city ? city.id : null); });
      labelsG.appendChild(labelG);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'city-li' + (locked ? ' locked' : '');
      btn.textContent = short;
      btn.setAttribute('aria-disabled', locked ? 'true' : 'false');
      btn.title = locked ? '前方的道路，以后再来探索吧' : ('进入' + short);
      btn.addEventListener('click', function () { openCity(city ? city.id : null); });
      listBtns.appendChild(btn);
    });
  }

  /* ---------- 城市详情 ---------- */
  var currentCity = null;
  function showToast(msg) {
    var t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.remove('show'); }, 2600);
  }
  function openCity(id) {
    // 未开通城市：仅提示，不进入
    if (!isOpen(id)) {
      showToast('前方的道路，以后再来探索吧 😊');
      return;
    }
    var data = window.__CITY_DATA__ || [];
    var city = data.find(function (c) { return c.id === id; });
    if (!city) return;
    currentCity = city;
    document.getElementById('heroName').textContent = city.full;
    document.getElementById('heroTag').textContent = city.tagline || '';
    document.getElementById('cityTitle').textContent = city.full + ' · 云游';
    switchTab('scenery');
    showView('viewCity');
  }

  var tabToken = 0;
  function preloadImages(srcs) {
    return Promise.all(srcs.map(function (src) {
      return new Promise(function (resolve) {
        var img = new Image();
        img.onload = resolve;
        img.onerror = resolve;   // 失败也 resolve，避免单张失败卡住整屏
        img.src = src;
      });
    }));
  }

  /* ---------- 条目多图画廊（imgs 数组优先，旧 img 单图兼容） ---------- */
  function itemImgs(item) {
    return (item.imgs && item.imgs.length) ? item.imgs : (item.img ? [item.img] : []);
  }
  function galleryHtml(item) {
    var imgs = itemImgs(item);
    if (!imgs.length) return '';
    var safe = item.t ? String(item.t).replace(/"/g, '&quot;') : '';
    var navs = imgs.length > 1
      ? '<button class="g-prev" type="button" aria-label="上一张">‹</button><button class="g-next" type="button" aria-label="下一张">›</button>'
      : '';
    var dots = imgs.length > 1
      ? '<div class="g-dots">' + imgs.map(function (_, k) { return '<span class="dot' + (k === 0 ? ' active' : '') + '"></span>'; }).join('') + '</div>'
      : '';
    return '<div class="card-img gallery" data-imgs="' + encodeURIComponent(JSON.stringify(imgs)) + '">' +
      '<img src="' + imgs[0] + '" alt="' + safe + '">' + navs + dots + '</div>';
  }
  function bindGalleries(box) {
    box.querySelectorAll('.gallery').forEach(function (gal) {
      var imgs = [];
      try { imgs = JSON.parse(decodeURIComponent(gal.getAttribute('data-imgs'))); } catch (e) {}
      if (!imgs.length) return;
      var idx = 0;
      var imgEl = gal.querySelector('img');
      var dots = gal.querySelectorAll('.g-dots .dot');
      function show(i) {
        idx = (i + imgs.length) % imgs.length;
        imgEl.src = imgs[idx];
        dots.forEach(function (d, k) { d.classList.toggle('active', k === idx); });
      }
      var prev = gal.querySelector('.g-prev');
      var next = gal.querySelector('.g-next');
      if (prev) prev.addEventListener('click', function (e) { e.stopPropagation(); show(idx - 1); });
      if (next) next.addEventListener('click', function (e) { e.stopPropagation(); show(idx + 1); });
      var x0 = null;
      gal.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
      gal.addEventListener('touchend', function (e) {
        if (x0 === null) return;
        var dx = e.changedTouches[0].clientX - x0;
        if (Math.abs(dx) > 40) show(idx + (dx < 0 ? 1 : -1));
        x0 = null;
      });
    });
  }

  function switchTab(tab) {
    if (!currentCity) return;
    var token = ++tabToken;   // 竞态保护：快速切 tab 时丢弃过期结果
    document.querySelectorAll('.tab-btn').forEach(function (b) {
      var on = b.getAttribute('data-tab') === tab;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    var box = document.getElementById('tabContent');
    // 板块背景图（admin 中"设置背景图"上传）
    var bgPath = currentCity.bg && currentCity.bg[tab];
    if (bgPath) {
      box.style.backgroundImage = 'linear-gradient(rgba(6,16,30,0.78), rgba(6,16,30,0.88)), url("' + bgPath + '")';
      box.style.backgroundSize = 'cover';
      box.style.backgroundPosition = 'center';
      box.classList.add('has-bg');
    } else {
      box.style.backgroundImage = '';
      box.style.backgroundSize = '';
      box.style.backgroundPosition = '';
      box.classList.remove('has-bg');
    }
    var list = currentCity[tab];
    if (!list || !list.length) {
      box.innerHTML = '<div class="empty-tip">—— 内容筹备中，敬请期待 ——</div>';
      return;
    }
    // 先显示占位，等该板块所有图片加载完成后一次性渲染，避免逐张弹出
    box.innerHTML = '<div class="tab-loading"><span class="spinner"></span>精彩正在赶来…</div>';
    var srcs = [];
    list.forEach(function (item) { srcs = srcs.concat(itemImgs(item)); });
    preloadImages(srcs).then(function () {
      if (token !== tabToken) return;   // 已切换到其他 tab
      box.innerHTML = list.map(function (item, i) {
        var st = storyFor(currentCity.id, item.t);
        var btn = (st && st.length)
          ? '<button class="story-btn" type="button" data-story-i="' + i + '">小故事</button>'
          : '';
        return '<div class="card"><div class="card-head"><h3>' + item.t + '</h3>' + btn + '</div>' +
          galleryHtml(item) + '<p>' + item.d + '</p></div>';
      }).join('');
      bindGalleries(box);
      bindStoryBtns(box, list);
    });
  }

  /* ---------- 南京小故事：名字旁按钮 → 弹窗 ---------- */
  function storyFor(cityId, name) {
    var all = window.__STORY_DATA__ || {};
    var city = all[cityId];
    return (city && city[name]) || null;
  }
  function bindStoryBtns(box, list) {
    box.querySelectorAll('.story-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var item = list[Number(btn.getAttribute('data-story-i'))];
        if (!item) return;
        var stories = storyFor(currentCity.id, item.t);
        if (stories && stories.length) openStory(currentCity.name, item.t, stories);
      });
    });
  }
  var storyMaskEl = null, storyBodyEl = null;
  function ensureStoryModal() {
    if (storyMaskEl) return;
    var mask = document.createElement('div');
    mask.className = 'story-mask';
    mask.innerHTML =
      '<div class="story-modal" role="dialog" aria-modal="true" aria-label="小故事">' +
        '<div class="story-head">' +
          '<span class="story-kicker" id="storyKicker"></span>' +
          '<button class="story-close" type="button" aria-label="关闭">✕</button>' +
        '</div>' +
        '<div class="story-body" id="storyBody"></div>' +
      '</div>';
    document.body.appendChild(mask);
    storyMaskEl = mask;
    storyBodyEl = mask.querySelector('#storyBody');
    mask.addEventListener('click', function (e) { if (e.target === mask) closeStory(); });
    mask.querySelector('.story-close').addEventListener('click', closeStory);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeStory(); });
  }
  function openStory(cityName, itemName, stories) {
    ensureStoryModal();
    var kickerEl = document.getElementById('storyKicker');
    if (kickerEl) kickerEl.textContent = (cityName || '') + ' · ' + (itemName || '');
    var body = stories.map(function (st) {
      var head = st.t ? '<h4>' + st.t + '</h4>' : '';
      var paras = (st.paras || []).map(function (p) { return '<p>' + p + '</p>'; }).join('');
      return '<div class="story-block">' + head + paras + '</div>';
    }).join('');
    storyBodyEl.innerHTML = body;
    storyMaskEl.classList.add('open');
    document.body.classList.add('no-scroll');
  }
  function closeStory() {
    if (!storyMaskEl) return;
    storyMaskEl.classList.remove('open');
    document.body.classList.remove('no-scroll');
  }
  document.querySelectorAll('.tab-btn').forEach(function (b) {
    b.addEventListener('click', function () { switchTab(b.getAttribute('data-tab')); });
  });
  window.__openCity = openCity;
})();
