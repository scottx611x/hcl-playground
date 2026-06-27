(function () {
  "use strict";

  var VERSIONS = JSON.parse(document.getElementById("versions-data").textContent || "{}");
  var engine = document.body.dataset.defaultEngine || "terraform";
  var frozen = document.body.dataset.frozen === "1";  // no on-demand installs (deploy)

  // Live function catalog for the selected engine+version (fetched from /functions).
  var hclFunctions = [];
  var functionsCache = {};

  var EXAMPLES = [
    {
      name: "subnets across AZs",
      code: [
        "// Everything outside a locals block is piped to `console`.",
        "locals {",
        '  regions            = ["us-east-1", "us-west-2", "eu-central-1"]',
        '  availability_zones = ["a", "b"]',
        "",
        "  region_az_combinations = setproduct(local.regions, local.availability_zones)",
        "}",
        "",
        "[for i, combo in local.region_az_combinations : {",
        '  az   = format("%s%s", combo[0], combo[1])',
        '  cidr = cidrsubnet("10.0.0.0/16", 8, i)',
        "}]",
      ].join("\n"),
    },
    {
      name: "🦉 sightings by spot",
      code: [
        "locals {",
        "  sightings = [",
        '    { bird = "Barred Owl",        spot = "Rea St." },',
        '    { bird = "Great Egret",       spot = "Stevens Pond" },',
        '    { bird = "Northern Cardinal", spot = "Rea St." },',
        '    { bird = "Osprey",            spot = "Stevens Pond" },',
        '    { bird = "Wood Duck",         spot = "Lake Cochichewick" },',
        "  ]",
        "}",
        "",
        "// group sightings by location around North Andover, MA",
        "{ for s in local.sightings : s.spot => s.bird... }",
      ].join("\n"),
    },
    {
      name: "naming convention",
      code: [
        "locals {",
        '  env      = "prod"',
        '  region   = "us-east-1"',
        '  services = ["owl", "egret", "osprey"]',
        "}",
        "",
        "// prod-owl-useast1, ...",
        '{ for s in local.services : s => format("%s-%s-%s", local.env, s, replace(local.region, "-", "")) }',
      ].join("\n"),
    },
    {
      name: "per-env config matrix",
      code: [
        "locals {",
        '  envs      = ["dev", "staging", "prod"]',
        '  base      = { instance_type = "t3.small", min = 1 }',
        '  overrides = { prod = { instance_type = "m6i.large", min = 3 } }',
        "}",
        "",
        "// merge base with any per-env overrides",
        "{ for e in local.envs : e => merge(local.base, try(local.overrides[e], {})) }",
      ].join("\n"),
    },
    {
      name: "CSV → objects",
      code: 'csvdecode("name,role,team\\nscott,engineer,platform\\nada,scientist,research")',
    },
    {
      name: "index a list by key",
      code: [
        "locals {",
        "  users = [",
        '    { id = "u1", name = "Scott", role = "owner" },',
        '    { id = "u2", name = "Ada",   role = "admin" },',
        "  ]",
        "}",
        "",
        "// list -> map keyed by id",
        "{ for u in local.users : u.id => u }",
      ].join("\n"),
    },
    {
      name: "merge tags w/ defaults",
      code: [
        "locals {",
        '  default_tags  = { managed_by = "terraform", env = "dev" }',
        '  resource_tags = { env = "prod", app = "birds" }',
        "}",
        "",
        "merge(local.default_tags, local.resource_tags)",
      ].join("\n"),
    },
    {
      name: "generate an IAM policy",
      code: [
        "jsonencode({",
        '  Version = "2012-10-17"',
        "  Statement = [{",
        '    Effect   = "Allow"',
        '    Action   = ["s3:GetObject", "s3:ListBucket"]',
        '    Resource = "arn:aws:s3:::birds-of-north-andover/*"',
        "  }]",
        "})",
      ].join("\n"),
    },
    {
      name: "regex parsing",
      code: [
        "locals {",
        '  arn = "arn:aws:s3:::my-bucket/path/key"',
        "}",
        "",
        'regex("arn:aws:(?P<service>[^:]+):", local.arn)',
      ].join("\n"),
    },
    {
      name: "try / can (safe lookups)",
      code: [
        "locals {",
        '  cfg = { name = "birds" }',
        "}",
        "",
        '// fall back when a key is missing',
        'try(local.cfg.region, "us-east-1")',
      ].join("\n"),
    },
    {
      name: "dates & durations",
      code: 'formatdate("EEEE, DD MMM YYYY", timeadd(timestamp(), "24h"))',
    },
  ];

  function el(id) {
    return document.getElementById(id);
  }

  function populateVersions() {
    var select = el("versionSelect");
    var list = VERSIONS[engine] || [];
    select.innerHTML = "";
    list.forEach(function (v) {
      var opt = document.createElement("option");
      opt.textContent = v;
      opt.value = v;
      select.appendChild(opt);
    });
    if (!frozen) {
      var more = document.createElement("option");
      more.value = "__install__";
      more.textContent = "+ install another…";
      select.appendChild(more);
    }
  }

  function sortVersionsDesc(arr) {
    return arr.sort(function (a, b) {
      var pa = a.split(".").map(Number), pb = b.split(".").map(Number);
      for (var i = 0; i < 3; i++) { if (pa[i] !== pb[i]) return pb[i] - pa[i]; }
      return 0;
    });
  }

  function promptInstall() {
    var select = el("versionSelect");
    select.selectedIndex = 0;  // move off the placeholder
    var label = engine === "tofu" ? "OpenTofu" : "Terraform";
    var v = (window.prompt("Install a " + label + " version (e.g. 1.10.10):") || "").trim();
    if (!v) { persist(); refreshFunctions(); return; }
    if (!/^\d+\.\d+\.\d+$/.test(v)) { setOutput("Enter a version like 1.10.10", true); return; }
    if ((VERSIONS[engine] || []).indexOf(v) !== -1) { selectVersion(v); refreshFunctions(); return; }
    setOutput("Installing " + label + " " + v + "… (first use can take a moment)");
    fetch("/install", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engine: engine, version: v }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok || res.d.error) { setOutput(res.d.error || "Install failed.", true); return; }
        VERSIONS[engine] = sortVersionsDesc((VERSIONS[engine] || []).concat([v]));
        populateVersions();
        selectVersion(v);
        setOutput("Installed " + label + " " + v + ". Ready.");
        persist(); refreshFunctions();
      })
      .catch(function () { setOutput("Install failed — couldn't reach the server.", true); });
  }

  function setEngine(next) {
    engine = next;
    document.body.classList.toggle("engine-tofu", engine === "tofu");
    Array.prototype.forEach.call(document.querySelectorAll(".engine-btn"), function (btn) {
      btn.classList.toggle("is-active", btn.dataset.engine === engine);
    });
    populateVersions();
  }

  function engineLabel() {
    return engine === "tofu" ? "OpenTofu" : "Terraform";
  }

  function setOutput(text, isError) {
    var out = el("output");
    out.textContent = text;
    out.classList.toggle("is-error", !!isError);
  }

  function setMeta(text, isError) {
    var m = el("outputMeta");
    if (!m) return;
    m.textContent = text || "";
    m.classList.toggle("is-error", !!isError);
    m.hidden = !text;
  }

  function run() {
    if (!window.editor) return;
    var version = el("versionSelect").value;
    if (!version || version === "__install__") {
      setOutput("Pick a version first.", true);
      return;
    }
    var btn = el("runBtn");
    btn.disabled = true;
    btn.textContent = "Running…";
    var label = engineLabel();
    var started = Date.now();
    setMeta("executing on " + label + " " + version + "…");
    setOutput("Evaluating…");

    fetch("/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engine: engine, version: version, code: window.editor.getValue() }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        var secs = ((Date.now() - started) / 1000).toFixed(1) + "s";
        if (!res.ok || res.data.error) {
          setOutput(res.data.error || "Something went wrong.", true);
          setMeta(label + " " + version + " · " + secs + " · error", true);
        } else {
          setOutput(res.data.output || "(no output)");
          setMeta(label + " " + version + " · " + secs);
        }
        persist();
      })
      .catch(function () {
        setOutput("Network error — couldn't reach the server.", true);
        setMeta(label + " " + version + " · failed", true);
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = "▶ Run";
      });
  }

  function buildExamplesMenu() {
    var menu = el("examplesMenu");
    EXAMPLES.forEach(function (ex) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = ex.name;
      b.addEventListener("click", function () {
        if (ex.engine && ex.engine !== engine) { setEngine(ex.engine); }
        if (ex.version) { selectVersion(ex.version); }
        refreshFunctions();
        if (window.editor) window.editor.setValue(ex.code);
        persist();
        menu.hidden = true;
        el("examplesBtn").setAttribute("aria-expanded", "false");
      });
      li.appendChild(b);
      menu.appendChild(li);
    });
  }

  function registerHcl(monaco) {
    if (monaco.languages.getLanguages().some(function (l) { return l.id === "hcl"; })) return;
    monaco.languages.register({ id: "hcl" });
    monaco.languages.setMonarchTokensProvider("hcl", {
      keywords: ["locals", "for", "in", "if", "true", "false", "null"],
      tokenizer: {
        root: [
          [/(#|\/\/).*$/, "comment"],
          [/"/, { token: "string.quote", next: "@string" }],
          [/\b\d+(\.\d+)?\b/, "number"],
          [/[a-zA-Z_]\w*(?=\s*\()/, "type"],
          [/[a-zA-Z_]\w*/, { cases: { "@keywords": "keyword", "@default": "identifier" } }],
          [/[{}()\[\]]/, "@brackets"],
          [/[=:,.]/, "delimiter"],
        ],
        string: [
          [/\$\{/, { token: "delimiter.bracket", next: "@interp" }],
          [/[^"\\$]+/, "string"],
          [/"/, { token: "string.quote", next: "@pop" }],
        ],
        interp: [
          [/\}/, { token: "delimiter.bracket", next: "@pop" }],
          [/[a-zA-Z_]\w*/, "identifier"],
          [/[^}]/, "string"],
        ],
      },
    });
  }

  function refreshFunctions() {
    var version = el("versionSelect").value;
    if (!version || version === "__install__") { hclFunctions = []; return; }
    var key = engine + "|" + version;
    if (functionsCache[key]) { hclFunctions = functionsCache[key]; return; }
    fetch("/functions?engine=" + encodeURIComponent(engine) + "&version=" + encodeURIComponent(version))
      .then(function (r) { return r.json(); })
      .then(function (d) { hclFunctions = d.functions || []; functionsCache[key] = hclFunctions; })
      .catch(function () { hclFunctions = []; });
  }

  function docUrl(name) {
    return engine === "tofu"
      ? "https://opentofu.org/docs/language/functions/" + name + "/"
      : "https://developer.hashicorp.com/terraform/language/functions/" + name;
  }
  function docLink(name) {
    var label = engine === "tofu" ? "OpenTofu" : "Terraform";
    return "[📖 " + label + " docs ↗](" + docUrl(name) + ")";
  }

  function registerProviders(monaco) {
    monaco.languages.registerCompletionItemProvider("hcl", {
      provideCompletionItems: function (model, position) {
        var word = model.getWordUntilPosition(position);
        var range = {
          startLineNumber: position.lineNumber, endLineNumber: position.lineNumber,
          startColumn: word.startColumn, endColumn: word.endColumn,
        };
        return {
          suggestions: hclFunctions.map(function (fn) {
            return {
              label: fn.name,
              kind: monaco.languages.CompletionItemKind.Function,
              detail: fn.sig,
              documentation: { value: (fn.doc ? fn.doc + "\n\n" : "") + docLink(fn.name) },
              insertText: fn.name + "($0)",
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              range: range,
            };
          }),
        };
      },
    });
    monaco.languages.registerHoverProvider("hcl", {
      provideHover: function (model, position) {
        var word = model.getWordAtPosition(position);
        if (!word) return null;
        var fn = hclFunctions.filter(function (f) { return f.name === word.word; })[0];
        if (!fn) return null;
        return {
          contents: [
            { value: "**" + fn.sig + "**" },
            { value: fn.doc },
            { value: docLink(fn.name) },
          ],
        };
      },
    });
    // Cmd/Ctrl-click a function name -> open its engine docs (real, obvious gesture).
    monaco.languages.registerLinkProvider("hcl", {
      provideLinks: function (model) {
        var known = {};
        hclFunctions.forEach(function (f) { known[f.name] = true; });
        var text = model.getValue();
        var re = /\b([a-z][a-z0-9_]*)\s*\(/g;
        var links = [];
        var m;
        while ((m = re.exec(text)) !== null) {
          if (!known[m[1]]) continue;
          var start = model.getPositionAt(m.index);
          var end = model.getPositionAt(m.index + m[1].length);
          links.push({
            range: {
              startLineNumber: start.lineNumber, startColumn: start.column,
              endLineNumber: end.lineNumber, endColumn: end.column,
            },
            url: docUrl(m[1]),
            tooltip: "Open " + m[1] + " docs",
          });
        }
        return { links: links };
      },
    });
  }

  // ---- Shareable state (URL hash) + localStorage persistence ----
  function encodeState(s) { return btoa(unescape(encodeURIComponent(JSON.stringify(s)))); }
  function decodeState(str) {
    try { return JSON.parse(decodeURIComponent(escape(atob(str)))); } catch (e) { return null; }
  }
  var PLACEHOLDER = "Hit Run to evaluate your HCL.";
  function outputForState() {
    var t = (el("output").textContent || "");
    return (t && t !== PLACEHOLDER && t !== "Evaluating…") ? t : "";
  }
  function currentState() {
    return {
      engine: engine,
      version: el("versionSelect").value,
      code: window.editor ? window.editor.getValue() : "",
      output: outputForState(),
      meta: (el("outputMeta").textContent || ""),
    };
  }
  function loadInitialState() {
    var m = location.hash.match(/[#&]s=([^&]+)/);
    if (m) {
      var s = decodeState(m[1]);
      if (s && s.code != null) return { engine: s.engine || engine, version: s.version || "", code: s.code, output: s.output || "", meta: s.meta || "" };
    }
    try {
      var saved = JSON.parse(localStorage.getItem("hclpg") || "null");
      if (saved && saved.code != null) return { engine: saved.engine || engine, version: saved.version || "", code: saved.code, output: saved.output || "", meta: saved.meta || "" };
    } catch (e) { /* ignore */ }
    return { engine: engine, version: "", code: EXAMPLES[0].code, output: "", meta: "" };
  }
  function persist() {
    try { localStorage.setItem("hclpg", JSON.stringify(currentState())); } catch (e) { /* ignore */ }
  }
  function selectVersion(v) {
    var select = el("versionSelect");
    if (v && Array.prototype.some.call(select.options, function (o) { return o.value === v; })) {
      select.value = v;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var initial = loadInitialState();
    setEngine(initial.engine);
    selectVersion(initial.version);
    refreshFunctions();
    buildExamplesMenu();

    el("engineToggle").addEventListener("click", function (e) {
      var btn = e.target.closest(".engine-btn");
      if (btn) { setEngine(btn.dataset.engine); persist(); refreshFunctions(); }
    });
    el("runBtn").addEventListener("click", run);
    el("examplesBtn").addEventListener("click", function () {
      var menu = el("examplesMenu");
      menu.hidden = !menu.hidden;
      this.setAttribute("aria-expanded", String(!menu.hidden));
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".menu")) {
        el("examplesMenu").hidden = true;
        el("examplesBtn").setAttribute("aria-expanded", "false");
      }
    });
    el("copyBtn").addEventListener("click", function () {
      navigator.clipboard && navigator.clipboard.writeText(el("output").textContent || "");
    });
    el("versionSelect").addEventListener("change", function () {
      if (this.value === "__install__") { promptInstall(); return; }
      persist(); refreshFunctions();
    });
    el("shareBtn").addEventListener("click", function () {
      var url = location.origin + location.pathname + "#s=" + encodeState(currentState());
      history.replaceState(null, "", url);
      if (navigator.clipboard) navigator.clipboard.writeText(url);
      var b = this, prev = b.textContent;
      b.textContent = "Copied!";
      setTimeout(function () { b.textContent = prev; }, 1200);
    });

    require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.46.0/min/vs" } });
    require(["vs/editor/editor.main"], function () {
      registerHcl(window.monaco);
      registerProviders(window.monaco);
      window.editor = monaco.editor.create(el("editor"), {
        value: initial.code,
        language: "hcl",
        theme: "vs-dark",
        fontSize: 14,
        fontFamily: "'JetBrains Mono', monospace",
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 14 },
        quickSuggestions: true,
      });
      window.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run);
      window.editor.onDidChangeModelContent(persist);
      // Restore a shared/saved result so the output isn't blank on a share link.
      if (initial.output) { setOutput(initial.output); setMeta(initial.meta || "shared result"); }
    });
  });
})();
