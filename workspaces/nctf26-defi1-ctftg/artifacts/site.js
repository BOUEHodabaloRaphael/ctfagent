/* National CTF — vitrine ctf.tg : intro 3D, phases, palmarès, effets. */
/* =====================================================================
   NCTF26 — « l'arène » : fond 3D de l'intro cinématique (Three.js r128)
   Chargé seulement quand l'intro joue. Sans WebGL ou si le script ne se
   charge pas, le fond CSS (grille + lignes de scan) reste en place.
   API : NCTFArena.create(host) → { setScene(i), stop() } ou null
   ===================================================================== */
window.NCTFArena = (function () {
  var SRC = "/js/vendor/three.min.js";
  var loading = null;

  function load() {
    if (window.THREE) return Promise.resolve(window.THREE);
    if (loading) return loading;
    loading = new Promise(function (ok, ko) {
      var s = document.createElement("script");
      s.src = SRC; s.async = true;
      s.onload = function () { window.THREE ? ok(window.THREE) : ko(); };
      s.onerror = ko;
      document.head.appendChild(s);
    });
    return loading;
  }

  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  /* une position de caméra (et un point visé) par scène de l'intro */
  var SHOTS = [
    { pos: [0, 1.6, 17], look: [0, 1.4, 0] },    /* boot : au ras du sol */
    { pos: [0, 3.6, 14], look: [0, 2.6, 0] },    /* marque : on se lève doucement */
    { pos: [-3, 4, 13], look: [0, 2.2, -3] },    /* arsenal : léger glissement à gauche */
    { pos: [3, 4.6, 12], look: [0, 1.8, -4] },   /* secteurs : léger glissement à droite */
    { pos: [0, 2.6, 9], look: [0, 2, -12] },     /* calendrier : on avance dans l'arène */
    { pos: [0, 6, 18], look: [0, 1.4, -2] }      /* fin : recul, l'arène se pose */
  ];

  function glyphAtlas(THREE) {
    var c = document.createElement("canvas");
    c.width = 128; c.height = 64;
    var g = c.getContext("2d");
    g.fillStyle = "#fff";
    g.textAlign = "center"; g.textBaseline = "middle";
    g.font = "700 54px 'JetBrains Mono', ui-monospace, monospace";
    g.fillText("0", 32, 34);
    g.fillText("1", 96, 34);
    var t = new THREE.CanvasTexture(c);
    t.minFilter = THREE.LinearFilter;
    return t;
  }

  function build(THREE, host) {
    var canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: "high-performance" });
    } catch (e) { return null; }
    var small = innerWidth < 760;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, small ? 1.5 : 1.75));

    var INK = new THREE.Color(css("--ink") || "#0a0d0b");
    var GREEN = new THREE.Color(css("--green") || "#22a06b");
    var DEEP = new THREE.Color(css("--green-deep") || "#006a4e");
    var YELLOW = new THREE.Color(css("--yellow") || "#ffce00");
    var RED = new THREE.Color(css("--red") || "#d21034");

    renderer.setClearColor(INK, 1);
    var scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(INK, 0.045);
    var camera = new THREE.PerspectiveCamera(55, 1, 0.1, 200);
    camera.position.set(0, 1.4, 17);
    var look = new THREE.Vector3(0, 1.2, 0), lookTo = look.clone();
    var posTo = camera.position.clone();

    /* sol quadrillé qui défile vers la caméra */
    var floorMat = new THREE.ShaderMaterial({
      extensions: { derivatives: true },
      transparent: true, depthWrite: false,
      uniforms: { uT: { value: 0 }, uLine: { value: DEEP }, uHot: { value: GREEN }, uInk: { value: INK } },
      vertexShader:
        "varying vec3 vW; void main(){ vec4 w = modelMatrix*vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix*viewMatrix*w; }",
      fragmentShader: [
        "uniform float uT; uniform vec3 uLine; uniform vec3 uHot; uniform vec3 uInk; varying vec3 vW;",
        "float grid(vec2 p, float s){ vec2 q = p / s; vec2 g = abs(fract(q - 0.5) - 0.5) / fwidth(q); return 1.0 - min(min(g.x, g.y), 1.0); }",
        "void main(){",
        "  vec2 p = vW.xz + vec2(0.0, uT * 1.6);",
        "  float minor = grid(p, 2.0) * 0.35;",
        "  float major = grid(p, 10.0);",
        "  float d = length(vW.xz);",
        "  float fade = exp(-d * 0.035);",
        "  float pulse = 0.5 + 0.5 * sin(d * 0.4 - uT * 1.2);",
        "  vec3 c = mix(uLine, uHot, major * (0.4 + 0.6 * pulse));",
        "  float a = max(minor, major) * fade;",
        "  gl_FragColor = vec4(c, a * 0.9);",
        "}"
      ].join("\n")
    });
    var floor = new THREE.Mesh(new THREE.PlaneGeometry(240, 240, 1, 1), floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    /* l'arène : trois anneaux posés au sol, aux couleurs du liseré */
    var rings = new THREE.Group();
    [[7.5, DEEP, 0.9], [7.9, YELLOW, 0.5], [8.3, RED, 0.45]].forEach(function (r, i) {
      var g = new THREE.RingGeometry(r[0], r[0] + 0.06, 128, 1, 0, Math.PI * 2);
      var m = new THREE.MeshBasicMaterial({ color: r[1], transparent: true, opacity: r[2], side: THREE.DoubleSide, depthWrite: false });
      var mesh = new THREE.Mesh(g, m);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.y = 0.02 + i * 0.01;
      rings.add(mesh);
    });
    /* graduations de l'anneau, comme un cadran */
    var tickPos = [];
    for (var k = 0; k < 96; k++) {
      var a = k / 96 * Math.PI * 2, r0 = 8.6, r1 = k % 8 === 0 ? 9.4 : 8.9;
      tickPos.push(Math.cos(a) * r0, 0.03, Math.sin(a) * r0, Math.cos(a) * r1, 0.03, Math.sin(a) * r1);
    }
    var tg = new THREE.BufferGeometry();
    tg.setAttribute("position", new THREE.Float32BufferAttribute(tickPos, 3));
    rings.add(new THREE.LineSegments(tg, new THREE.LineBasicMaterial({ color: GREEN, transparent: true, opacity: 0.55 })));
    rings.position.z = -4;
    scene.add(rings);

    /* le drapeau : un mât de lumière au centre de l'arène */
    var beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.03, 30, 8, 1, true),
      new THREE.MeshBasicMaterial({ color: GREEN, transparent: true, opacity: 0.5, depthWrite: false })
    );
    beam.position.set(0, 15, -4);
    scene.add(beam);

    /* pluie binaire en volume */
    var N = small ? 380 : 800;
    var pos = new Float32Array(N * 3), glyph = new Float32Array(N), speed = new Float32Array(N), tint = new Float32Array(N * 3);
    for (var i = 0; i < N; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 70;
      pos[i * 3 + 1] = Math.random() * 26;
      pos[i * 3 + 2] = -55 + Math.random() * 70;
      glyph[i] = Math.random() < 0.5 ? 0 : 1;
      speed[i] = 0.6 + Math.random() * 2.2;
      var col = Math.random() < 0.03 ? YELLOW : (Math.random() < 0.5 ? GREEN : DEEP);
      tint[i * 3] = col.r; tint[i * 3 + 1] = col.g; tint[i * 3 + 2] = col.b;
    }
    var pg = new THREE.BufferGeometry();
    pg.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    pg.setAttribute("aGlyph", new THREE.BufferAttribute(glyph, 1));
    pg.setAttribute("aSpeed", new THREE.BufferAttribute(speed, 1));
    pg.setAttribute("aTint", new THREE.BufferAttribute(tint, 3));
    var rainMat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uT: { value: 0 }, uAtlas: { value: glyphAtlas(THREE) }, uScale: { value: renderer.getPixelRatio() * (small ? 220 : 300) } },
      vertexShader: [
        "attribute float aGlyph; attribute float aSpeed; attribute vec3 aTint;",
        "uniform float uT; uniform float uScale;",
        "varying float vG; varying vec3 vC; varying float vA;",
        "void main(){",
        "  vec3 p = position; p.y = mod(p.y - uT * aSpeed, 26.0);",
        "  vec4 mv = modelViewMatrix * vec4(p, 1.0);",
        "  gl_Position = projectionMatrix * mv;",
        "  gl_PointSize = uScale / -mv.z;",
        "  vG = aGlyph; vC = aTint;",
        "  vA = smoothstep(0.0, 3.0, p.y) * smoothstep(26.0, 20.0, p.y) * clamp(1.4 - (-mv.z) / 45.0, 0.0, 1.0);",
        "}"
      ].join("\n"),
      fragmentShader: [
        "uniform sampler2D uAtlas; varying float vG; varying vec3 vC; varying float vA;",
        "void main(){",
        "  vec2 uv = vec2((gl_PointCoord.x + vG) * 0.5, 1.0 - gl_PointCoord.y);",
        "  float m = texture2D(uAtlas, uv).a;",
        "  gl_FragColor = vec4(vC, m * vA * 0.55);",
        "}"
      ].join("\n")
    });
    scene.add(new THREE.Points(pg, rainMat));

    host.insertBefore(canvas, host.firstChild);
    host.classList.add("gl");

    function size() {
      var w = host.clientWidth || innerWidth, h = host.clientHeight || innerHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      /* écran étroit : on recule pour garder l'arène entière */
      camera.fov = w / h < 0.8 ? 72 : 55;
      camera.updateProjectionMatrix();
    }
    size();
    addEventListener("resize", size);

    var mouse = { x: 0, y: 0 };
    function onMove(e) { mouse.x = e.clientX / innerWidth - 0.5; mouse.y = e.clientY / innerHeight - 0.5; }
    addEventListener("pointermove", onMove);

    var raf = 0, t0 = performance.now(), alive = true;
    function frame(now) {
      if (!alive) return;
      var t = (now - t0) / 1000;
      floorMat.uniforms.uT.value = t;
      rainMat.uniforms.uT.value = t;
      rings.rotation.y = t * 0.08;
      beam.material.opacity = 0.28 + 0.08 * Math.sin(t * 1.2);
      camera.position.lerp(posTo, 0.02);
      camera.position.x += mouse.x * 0.015;
      camera.position.y -= mouse.y * 0.01;
      look.lerp(lookTo, 0.05);
      camera.lookAt(look);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);

    return {
      setScene: function (i) {
        var s = SHOTS[Math.max(0, Math.min(SHOTS.length - 1, i))];
        posTo.set(s.pos[0], s.pos[1], s.pos[2]);
        lookTo.set(s.look[0], s.look[1], s.look[2]);
      },
      stop: function () {
        alive = false;
        cancelAnimationFrame(raf);
        removeEventListener("resize", size);
        removeEventListener("pointermove", onMove);
        scene.traverse(function (o) {
          if (o.geometry) o.geometry.dispose();
          if (o.material) { if (o.material.uniforms && o.material.uniforms.uAtlas) o.material.uniforms.uAtlas.value.dispose(); o.material.dispose(); }
        });
        renderer.dispose();
        if (renderer.forceContextLoss) renderer.forceContextLoss();
        canvas.remove();
        host.classList.remove("gl");
      }
    };
  }

  return {
    loadThree: load,
    create: function (host) {
      return load().then(function (THREE) { return build(THREE, host); }).catch(function () { return null; });
    }
  };
})();

(function () {
  var C = window.NCTF;
  var root = document.documentElement;
  root.classList.add("js");
  var ARENA = C.arena;
  function $(s) { return document.querySelector(s); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  /* ------------------------------------------- contenu tiré de la config */
  var nSectors = C.sectors.length;
  function statValue(v) { return v === "auto" ? nSectors : v; }
  var nChallenges = statValue(C.arsenal[0].value);
  document.querySelectorAll("[data-stat=challenges]").forEach(function (d) { if (nChallenges != null) d.textContent = nChallenges; });
  document.querySelectorAll("[data-stat=sectors]").forEach(function (d) { d.textContent = nSectors; });
  document.querySelectorAll(".flagfmt").forEach(function (n) { n.textContent = C.flagFormat; });


  /* ------------------------------------------------------ menu mobile */
  var btn = $(".menu-btn");
  var head = $(".site-head");
  function closeMenu() { head.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }
  btn.addEventListener("click", function () {
    var open = head.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
  document.querySelectorAll(".nav a").forEach(function (a) { a.addEventListener("click", closeMenu); });

  /* ------------------ visuel clé : boucle vidéo en bureau, jamais sous reduced-motion */
  var bg = $(".hero-bg");
  var motionOk = matchMedia("(min-width: 861px) and (prefers-reduced-motion: no-preference)").matches &&
    !(navigator.connection && navigator.connection.saveData);
  if (bg && motionOk) {
    var v = document.createElement("video");
    v.muted = true; v.loop = true; v.autoplay = true; v.playsInline = true;
    v.setAttribute("aria-hidden", "true");
    [["webm", bg.dataset.videoWebm], ["mp4", bg.dataset.videoMp4]].forEach(function (s) {
      var e = document.createElement("source"); e.src = s[1]; e.type = "video/" + s[0]; v.appendChild(e);
    });
    v.addEventListener("playing", function () { v.classList.add("ready"); }, { once: true });
    bg.appendChild(v);
  }

  /* ------------------------------------- phases de l'édition (heure de Lomé = GMT) */
  var K = C.calendar;
  var T = {
    open: Date.parse(K.registration.at),
    quals: Date.parse(K.qualifiers.from),
    qualsEnd: Date.parse(K.qualifiers.to),
    final: Date.parse(K.final.from),
    over: Date.parse(K.final.to)
  };
  var A = {
    register: ["Créer mon équipe", ARENA + "/register"],
    login: ["Se connecter", ARENA + "/login"],
    arena: ["Entrer dans l'arène", ARENA + "/challenges"],
    board: ["Voir le classement", ARENA + "/scoreboard"],
    rules: ["Lire le règlement", ARENA + "/tos"],
    agenda: ["Voir le calendrier", "#deroule"],
    discord: ["Rejoindre le Discord", "https://discord.gg/QU6W794CRx"],
    fame: ["Palmarès", "#palmares"]
  };
  var PHASES = [
    { until: T.open, state: "soon", label: "Inscriptions le 30 octobre",
      detail: "Présélection en ligne du vendredi 6 novembre 19:00 au samedi 7 novembre 23:59 (GMT)",
      link: ["Préparer son équipe →", A.discord[1]], buttons: [A.agenda, A.rules, A.discord],
      cd: [T.open, "Ouverture des inscriptions dans", "— vendredi 30 octobre, 00:00 GMT"] },
    { until: T.quals, state: "open", label: "Inscriptions ouvertes",
      detail: "Présélection en ligne du vendredi 6 novembre 19:00 au samedi 7 novembre 23:59 (GMT)",
      link: ["S'inscrire →", A.register[1]], buttons: [A.register, A.login, A.rules],
      cd: [T.quals, "Présélection dans", "— vendredi 6 novembre, 19:00 GMT"] },
    { until: T.qualsEnd, state: "live", label: "Présélection en cours",
      detail: "Fin samedi 7 novembre à 23:59 (GMT)",
      link: ["Classement en direct →", A.board[1]], buttons: [A.arena, A.board, A.register],
      cd: [T.qualsEnd, "Fin de la présélection dans", "— samedi 7 novembre, 23:59 GMT"] },
    { until: T.over, state: "final", label: "Finale à Lomé, 19–20 novembre",
      detail: "Les équipes qualifiées sont annoncées sur la plateforme et le Discord",
      link: ["Classement →", A.board[1]], buttons: [A.board, A.arena, A.discord],
      cd: [T.final, "Finale dans", "— jeudi 19 novembre, Lomé"] },
    { until: Infinity, state: "over", label: "Édition 2026 terminée",
      detail: "Merci aux équipes. Rendez-vous pour NCTF27.",
      link: ["Palmarès →", "#palmares"], buttons: [A.board, A.fame, A.discord], cd: null }
  ];

  var offset = 0;
  function now() { return Date.now() + offset; }
  var bar = $("#status");
  var cd = $("#countdown");
  var actions = $("#hero-actions");
  var cdTarget = 0, timer = 0;
  function pad(n) { return n < 10 ? "0" + n : "" + n; }

  function tick() {
    clearTimeout(timer);
    if (!cdTarget) return;
    var s = Math.max(0, Math.floor((cdTarget - now()) / 1000));
    if (!s) { render(); return; }
    cd.querySelector("[data-u=d]").textContent = Math.floor(s / 86400);
    cd.querySelector("[data-u=h]").textContent = pad(Math.floor(s % 86400 / 3600));
    cd.querySelector("[data-u=m]").textContent = pad(Math.floor(s % 3600 / 60));
    cd.querySelector("[data-u=s]").textContent = pad(s % 60);
    timer = setTimeout(tick, 1000);
  }

  function render() {
    var t = now();
    var p = PHASES.filter(function (x) { return t < x.until; })[0];
    bar.dataset.state = p.state;
    bar.querySelector(".state").textContent = p.label;
    bar.querySelector(".detail").textContent = p.detail;
    var a = bar.querySelector("a"); a.textContent = p.link[0]; a.href = p.link[1];
    /* trois boutons : le premier est l'action utile à cette date */
    actions.textContent = "";
    p.buttons.forEach(function (b, i) {
      var l = el("a", "btn " + (i ? "btn-ghost" : "btn-primary"), b[0]);
      l.href = b[1];
      if (!i) { var ar = el("span", "arrow", " →"); ar.setAttribute("aria-hidden", "true"); l.appendChild(ar); }
      actions.appendChild(l);
    });
    if (p.cd) {
      cd.hidden = false; cdTarget = p.cd[0];
      cd.querySelector(".cd-what").textContent = p.cd[1];
      cd.querySelector(".cd-when").textContent = p.cd[2];
    } else { cd.hidden = true; cdTarget = 0; }
    document.querySelectorAll(".timeline li").forEach(function (li) {
      li.classList.toggle("done", Date.parse(li.dataset.at) <= t);
    });
    document.querySelectorAll(".hero-dates li").forEach(function (li) {
      var from = Date.parse(li.dataset.from), to = Date.parse(li.dataset.to);
      li.classList.toggle("now", t >= from && t < to);
      li.classList.toggle("done", t >= to);
    });
    tick();
  }
  /* outil d'aperçu (absent du site) : simuler une date */
  var sim = $("#sim-date");
  if (sim) sim.addEventListener("change", function (e) {
    offset = e.target.value ? Date.parse(e.target.value) - Date.now() : 0;
    render();
  });
  render();

  /* --------------------------------------------- palmarès (JSON dans la page) */
  (function () {
    var raw = $("#palmares-data"), host = $("#fame"), section = $("#palmares"), data;
    try { data = JSON.parse(raw.textContent); } catch (e) { return; }
    var labels = { 1: "Champion", 2: "2e place", 3: "3e place" }, shown = 0;
    data
      .filter(function (ed) { return ed && ed.podium && ed.podium.length; })
      .sort(function (a, b) { return b.annee - a.annee; })
      .forEach(function (ed, i) {
        var card = el("article", "edition" + (i === 0 ? " latest" : ""));
        var h = el("div", "edition-head");
        h.appendChild(el("p", "edition-year", ed.annee));
        h.appendChild(el("p", "edition-format", (i === 0 ? "Dernière édition" : "") + (i === 0 && ed.format ? " · " : "") + (ed.format || "")));
        card.appendChild(h);
        var list = el("ol", "podium");
        ed.podium.slice().sort(function (a, b) { return a.rang - b.rang; }).forEach(function (p) {
          var li = el("li", "rank-" + p.rang);
          li.appendChild(el("span", "medal", p.rang));
          var body = el("div", "who");
          body.appendChild(el("span", "rank-label", labels[p.rang] || (p.rang + "e place")));
          body.appendChild(el("strong", null, p.equipe));
          if (p.points) body.appendChild(el("span", "points", p.points.toLocaleString("fr-FR") + " pts"));
          if (p.membres && p.membres.length) body.appendChild(el("span", "members", p.membres.join(" · ")));
          li.appendChild(body);
          list.appendChild(li);
        });
        card.appendChild(list);
        (ed.mentions || []).forEach(function (t) { card.appendChild(el("p", "mention", t)); });
        host.appendChild(card);
        shown++;
      });
    if (shown) section.hidden = false;
  })();

  /* ------------------------------------ décodage 0/1 → texte (motif commun) */
  var GLYPHS = "01#$%&{}<>/\\";
  function decode(node, delay, dur) {
    if (!node) return;
    if (node.nodeType !== 3) node = node.firstChild;
    if (!node || node.nodeType !== 3 || !node.nodeValue.trim()) return;
    var final = node.nodeValue, digits = /^\d+$/.test(final), t0 = 0;
    function frame(ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur), out = "";
      for (var i = 0; i < final.length; i++) {
        out += p >= (i + 1) / final.length ? final[i]
          : digits ? String(Math.floor(Math.random() * 10))
          : GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
      }
      node.nodeValue = out;
      if (p < 1) requestAnimationFrame(frame);
    }
    setTimeout(function () { requestAnimationFrame(frame); }, delay);
    /* onglet en arrière-plan : rAF peut être suspendu, le texte final s'écrit quand même */
    setTimeout(function () { node.nodeValue = final; }, delay + dur + 400);
  }

  /* courte séquence d'ouverture (visiteurs qui ont déjà vu l'intro) */
  function playOpening() {
    root.classList.remove("intro");
    void root.offsetWidth;
    root.classList.add("intro");
    decode($(".hero h1 [data-decode]"), 850, 600);
    document.querySelectorAll(".hero .stats dd[data-decode]").forEach(function (dd, i) {
      decode(dd, 1300 + i * 60, 650);
    });
  }
  if (root.classList.contains("intro")) playOpening();

  /* ===================================================== intro cinématique */
  var cine = $("#cine");
  var scenes = Array.prototype.slice.call(cine.querySelectorAll(".scene"));
  var segs = Array.prototype.slice.call(cine.querySelectorAll(".cine-progress li"));
  var D = C.intro.durations;
  var ORDER = ["boot", "brand", "arsenal", "sectors", "calendar", "end"];

  /* remplissage des scènes depuis la config */
  var bootList = $("#cine-boot");
  C.boot.forEach(function (b) {
    var li = el("li");
    li.appendChild(el("span", "p", ">"));
    li.appendChild(el("span", "t", b.text));
    li.appendChild(el("span", "s" + (b.live ? " live" : ""), "[ " + b.status + " ]"));
    bootList.appendChild(li);
  });
  $("#cine-name").textContent = C.brand.name;
  $("#cine-year").textContent = C.brand.year;
  $("#cine-tagline").textContent = C.brand.tagline;
  var nums = $("#cine-nums");
  C.arsenal.forEach(function (a) {
    var val = statValue(a.value);
    if (val == null) return;
    var d = el("div");
    var dd = el("dd", null, "0"); dd.dataset.to = val;
    d.appendChild(dd);
    d.appendChild(el("dt", null, a.label));
    nums.appendChild(d);
  });
  var secs = $("#cine-secs");
  C.sectors.forEach(function (s, i) {
    var li = el("li", null, s.name);
    li.style.setProperty("--i", i);
    if (s.count != null) li.appendChild(el("b", null, String(s.count)));
    secs.appendChild(li);
  });
  var cal = $("#cine-cal");
  [["présélection", K.qualifiers], ["finale", K.final]].forEach(function (x) {
    var art = el("article");
    art.appendChild(el("span", "k", x[0]));
    art.appendChild(el("span", "d", x[1].label));
    art.appendChild(el("span", "m", x[1].meta));
    cal.appendChild(art);
  });
  var reg = $("#cine-reg");
  reg.appendChild(document.createTextNode("inscriptions ouvertes le "));
  reg.appendChild(el("b", null, K.registration.label));
  reg.appendChild(document.createTextNode(" · arena.ctf.tg/register"));
  var flag = $("#cine-flag");
  var fm = C.flagFormat.match(/^(.*\{)(.*)(\})$/);
  if (fm) { flag.appendChild(document.createTextNode(fm[1])); flag.appendChild(el("i", null, fm[2])); flag.appendChild(document.createTextNode(fm[3])); }
  else flag.textContent = C.flagFormat;

  /* effets propres à chaque scène */
  var subTimers = [];
  function later(fn, ms) { subTimers.push(setTimeout(fn, ms)); }
  function countUp(dd, dur) {
    var to = +dd.dataset.to, t0 = 0;
    if (isNaN(to)) { dd.textContent = dd.dataset.to; return; }
    function f(ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      dd.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(f);
    }
    requestAnimationFrame(f);
    later(function () { dd.textContent = to; }, dur + 300);
  }
  var ENTER = {
    boot: function () {
      var lines = bootList.children, step = (D.boot - 900) / lines.length;
      Array.prototype.forEach.call(lines, function (li, i) {
        li.classList.remove("in");
        later(function () { li.classList.add("in"); }, 200 + i * step);
      });
    },
    brand: function () { decode($("#cine-year"), 700, 500); },
    arsenal: function () {
      nums.querySelectorAll("dd").forEach(function (dd, i) { later(function () { countUp(dd, 1300); }, 150 + i * 150); });
    },
    sectors: function () {}, calendar: function () {}, end: function () {}
  };

  var idx = -1, sceneTimer = 0, sceneStart = 0, remaining = 0, running = false, lastFocus = null;

  /* fond 3D : chargé à la volée, l'intro démarre sans l'attendre */
  var gl = null, glPending = false;
  function startGL() {
    if (gl || glPending || !window.NCTFArena) return;
    glPending = true;
    NCTFArena.create(cine.querySelector(".cine-bg")).then(function (a) {
      glPending = false;
      if (!a) return;
      if (!running) { a.stop(); return; }
      gl = a;
      gl.setScene(Math.max(0, idx));
    });
  }
  function stopGL() { if (gl) { gl.stop(); gl = null; } }

  function show(i) {
    clearTimeout(sceneTimer);
    subTimers.forEach(clearTimeout); subTimers = [];
    idx = i;
    if (i >= scenes.length) { finish(); return; }
    var name = ORDER[i], dur = D[name];
    scenes.forEach(function (s, j) { s.classList.toggle("on", j === i); });
    segs.forEach(function (s, j) {
      s.classList.toggle("done", j < i);
      s.classList.remove("now");
      if (j === i) { void s.offsetWidth; s.style.setProperty("--dur", dur + "ms"); s.classList.add("now"); }
    });
    ENTER[name]();
    if (gl) gl.setScene(i);
    sceneStart = Date.now(); remaining = dur;
    sceneTimer = setTimeout(function () { show(i + 1); }, dur);
  }
  function pause() {
    if (!running || cine.classList.contains("paused")) return;
    clearTimeout(sceneTimer);
    remaining -= Date.now() - sceneStart;
    cine.classList.add("paused");
  }
  function resume() {
    if (!running || !cine.classList.contains("paused")) return;
    cine.classList.remove("paused");
    sceneStart = Date.now();
    sceneTimer = setTimeout(function () { show(idx + 1); }, Math.max(0, remaining));
  }
  function finish() {
    if (!running) return;
    running = false;
    clearTimeout(sceneTimer);
    subTimers.forEach(clearTimeout); subTimers = [];
    try { localStorage.setItem(NCTF.introKey, String(C.intro.version)); } catch (e) {}
    /* sortie en fondu enchaîné : le texte s'efface (0,45 s), l'arène se dissout (1,1 s, après 0,35 s)
       et, pendant ce temps, le hero joue sa courte séquence d'ouverture sous le calque */
    var focusHero = cine.contains(document.activeElement);
    cine.classList.add("out");
    setTimeout(playOpening, 300);
    setTimeout(function () {
      root.classList.remove("cine-on");
      cine.classList.remove("out", "paused");
      scenes.forEach(function (s) { s.classList.remove("on"); });
      stopGL();
      dispatchEvent(new Event("nctf:intro-end"));
      if (focusHero) $(".hero h1").focus({ preventScroll: true });
    }, 1500);
  }
  function start() {
    if (!matchMedia("(prefers-reduced-motion: no-preference)").matches) return;
    root.classList.remove("intro");
    root.classList.add("cine-on");
    window.scrollTo(0, 0);
    running = true;
    lastFocus = document.activeElement;
    $("#cine-skip").focus({ preventScroll: true });
    show(0);
    startGL();
  }

  $("#cine-skip").addEventListener("click", function (e) { e.stopPropagation(); finish(); });
  cine.addEventListener("click", function () { if (running) show(idx + 1); });
  document.addEventListener("keydown", function (e) {
    if (running) {
      if (e.key === "Escape") { e.preventDefault(); finish(); }
      else if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter" && e.target === document.body) { e.preventDefault(); show(idx + 1); }
      else if (e.key === "ArrowLeft" && idx > 0) { e.preventDefault(); show(idx - 1); }
      else if (e.key === "Tab") { e.preventDefault(); $("#cine-skip").focus(); }
      return;
    }
    if (e.key === "Escape") closeMenu();
  });
  document.addEventListener("visibilitychange", function () { document.hidden ? pause() : resume(); });

  $("#replay-intro").addEventListener("click", start);
  /* outils d'aperçu (absents du site) */
  var replay = $("#replay"), resetSeen = $("#reset-seen");
  if (replay) replay.addEventListener("click", start);
  if (resetSeen) resetSeen.addEventListener("click", function () {
    try { localStorage.removeItem(NCTF.introKey); } catch (e) {}
    this.textContent = "Oublié : l'intro rejouera au rechargement";
  });

  if (NCTF.introPlay) {
    if (document.hidden) {
      /* onglet ouvert en arrière-plan : on attend qu'il soit regardé */
      document.addEventListener("visibilitychange", function once() {
        if (!document.hidden) { document.removeEventListener("visibilitychange", once); start(); }
      });
      running = false;
    } else start();
  }

  /* --------------------------------------- section active dans la navigation */
  if (!("IntersectionObserver" in window)) return;
  var links = {};
  document.querySelectorAll('.nav a[href^="#"]').forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var a = links[e.target.id];
      if (a && e.isIntersecting) {
        Object.keys(links).forEach(function (k) { links[k].classList.remove("active"); });
        a.classList.add("active");
      }
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });
})();

/* =====================================================================
   NCTF26 — effets de la vitrine : défilé orchestré (GSAP + ScrollTrigger)
   Optionnel : sans JS ou sous prefers-reduced-motion, la vitrine reste complète.
   ===================================================================== */
(function () {
  var MOTION = matchMedia("(prefers-reduced-motion: no-preference)").matches;
  function $(s, r) { return (r || document).querySelector(s); }
  function loadScript(src) {
    return new Promise(function (ok, ko) {
      var s = document.createElement("script"); s.src = src; s.async = false;
      s.onload = ok; s.onerror = ko; document.head.appendChild(s);
    });
  }

  if (!MOTION) return;

  /* SÉCURITÉ : tout ce que GSAP masque passe par hide() et reste surveillé.
     - chien de garde : un bloc à l'écran depuis 2 s et toujours invisible est réaffiché,
       indépendamment de GSAP (ScrollTrigger en panne, script interrompu…) ;
     - annulation : si la mise en place échoue, restore() rend tous les blocs visibles ;
     - les blocs liés au défilement (scrub) ne descendent jamais sous 15 % d'opacité. */
  var hidden = [];
  var REVEAL_AFTER = 2000;
  function restore(n) {
    n.style.opacity = ""; n.style.transform = ""; n.style.visibility = "";
    n.removeAttribute("data-fx-hidden");
  }
  function isInvisible(n) { return parseFloat(getComputedStyle(n).opacity) < 0.05; }
  var guard = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var n = e.target;
      setTimeout(function () {
        if (n.hasAttribute("data-fx-hidden") && isInvisible(n)) {
          restore(n);
          if (window.console) console.warn("fx : bloc réaffiché par la sécurité", n);
        }
        if (!isInvisible(n)) { n.removeAttribute("data-fx-hidden"); guard.unobserve(n); }
      }, REVEAL_AFTER);
    });
  }) : null;
  function hide(nodes) {
    nodes.forEach(function (n) { n.setAttribute("data-fx-hidden", ""); hidden.push(n); if (guard) guard.observe(n); });
    return nodes;
  }
  function restoreAll() { hidden.forEach(restore); hidden = []; if (guard) guard.disconnect(); }

  var GS = "/js/vendor/";
  loadScript(GS + "gsap.min.js").then(function () { return loadScript(GS + "ScrollTrigger.min.js"); }).then(function () {
    var gsap = window.gsap, ST = window.ScrollTrigger;
    if (!gsap || !ST) return;
    gsap.registerPlugin(ST);
    try { choreograph(gsap, ST); }
    catch (e) {
      restoreAll();
      if (window.console) console.warn("fx : défilé orchestré désactivé", e);
    }
  }).catch(function () { restoreAll(); });

  function choreograph(gsap, ST) {

    /* apparitions en cascade, seulement pour ce qui est encore sous la ligne de flottaison */
    var items = gsap.utils.toArray(".flow li, .grid .card, .rules li, .creators li, .partners figure, .community, .fame .edition")
      .filter(function (n) { return n.getBoundingClientRect().top > innerHeight * 0.92; });
    gsap.set(hide(items), { opacity: 0, y: 28 });
    ST.batch(items, {
      start: "top 90%", once: true,
      onEnter: function (b) { gsap.to(b, { opacity: 1, y: 0, duration: 0.8, ease: "power3.out", stagger: 0.08, overwrite: true }); }
    });

    /* points du palmarès comptés à l'entrée */
    gsap.utils.toArray(".fame .points").forEach(function (p) {
      var n = parseInt(p.textContent.replace(/\D/g, ""), 10);
      if (!n) return;
      var o = { v: 0 };
      ST.create({ trigger: p, start: "top 92%", once: true, onEnter: function () {
        gsap.to(o, { v: n, duration: 1.4, ease: "power2.out", onUpdate: function () { p.textContent = Math.round(o.v).toLocaleString("fr-FR") + " pts"; } });
      } });
    });

    /* déroulé : la frise se remplit, les dates s'allument, les phases arrivent de part et d'autre */
    var sec = $("#deroule");
    var mm = gsap.matchMedia();
    mm.add("(min-width: 961px)", function () {
      var tl = gsap.timeline({ scrollTrigger: { trigger: sec.querySelector(".timeline"), start: "top 80%", end: "bottom+=320 60%", scrub: 0.7 } });
      tl.fromTo(sec.querySelector(".timeline"), { "--p": 0 }, { "--p": 1, ease: "none", duration: 3 }, 0)
        .from(sec.querySelectorAll(".timeline li"), { opacity: 0.2, y: 10, stagger: 1, duration: 0.6 }, 0)
        /* liés au défilement : jamais sous 15 %, lisibles même si la chorégraphie s'arrête */
        .from(sec.querySelector(".phase:first-child"), { x: -70, opacity: 0.15, duration: 1 }, 0.6)
        .from(sec.querySelector(".phase-link"), { scaleX: 0, opacity: 0, duration: 0.6 }, 1.4)
        .from(sec.querySelector(".phase:last-child"), { x: 70, opacity: 0.15, duration: 1 }, 1.8);
    });
    mm.add("(max-width: 960px)", function () {
      gsap.from(hide(gsap.utils.toArray(sec.querySelectorAll(".timeline li, .phase"))), {
        opacity: 0, y: 24, stagger: 0.12, duration: 0.7, ease: "power3.out",
        scrollTrigger: { trigger: sec.querySelector(".timeline"), start: "top 85%", once: true }
      });
    });

    addEventListener("nctf:intro-end", function () { ST.refresh(); });
  }
})();
