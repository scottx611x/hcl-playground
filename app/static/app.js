(function () {
  "use strict";

  var VERSIONS = JSON.parse(document.getElementById("versions-data").textContent || "{}");
  var engine = document.body.dataset.defaultEngine || "terraform";

  var EXAMPLES = [
    {
      name: "setproduct + for",
      code: [
        "// Everything outside a locals block is piped to `console`.",
        "locals {",
        '  regions            = ["us-east-1", "us-west-2", "eu-central-1"]',
        '  availability_zones = ["a", "b"]',
        "",
        "  region_az_combinations = setproduct(local.regions, local.availability_zones)",
        "",
        "  network_configurations = [",
        "    for combo in local.region_az_combinations : {",
        "      region            = combo[0]",
        '      availability_zone = format("%s%s", combo[0], combo[1])',
        "    }",
        "  ]",
        "}",
        "",
        "local.network_configurations",
      ].join("\n"),
    },
    {
      name: "string functions",
      code: [
        "locals {",
        '  name = "  Birds of North Andover  "',
        "}",
        "",
        'upper(trimspace(local.name))',
      ].join("\n"),
    },
    {
      name: "maps & merge",
      code: [
        "locals {",
        '  base    = { env = "dev", region = "us-east-1" }',
        '  overEx  = { region = "us-west-2", team = "platform" }',
        "}",
        "",
        "merge(local.base, local.overEx)",
      ].join("\n"),
    },
    {
      name: "cidr math",
      code: 'cidrsubnets("10.0.0.0/16", 4, 4, 8, 8)',
    },
  ];

  function el(id) {
    return document.getElementById(id);
  }

  function populateVersions() {
    var select = el("versionSelect");
    var list = VERSIONS[engine] || [];
    select.innerHTML = "";
    if (!list.length) {
      var opt = document.createElement("option");
      opt.textContent = "(none installed)";
      opt.value = "";
      select.appendChild(opt);
      return;
    }
    list.forEach(function (v) {
      var opt = document.createElement("option");
      opt.textContent = v;
      opt.value = v;
      select.appendChild(opt);
    });
  }

  function setEngine(next) {
    engine = next;
    document.body.classList.toggle("engine-tofu", engine === "tofu");
    Array.prototype.forEach.call(document.querySelectorAll(".engine-btn"), function (btn) {
      btn.classList.toggle("is-active", btn.dataset.engine === engine);
    });
    populateVersions();
  }

  function setOutput(text, isError) {
    var out = el("output");
    out.textContent = text;
    out.classList.toggle("is-error", !!isError);
  }

  function run() {
    if (!window.editor) return;
    var version = el("versionSelect").value;
    if (!version) {
      setOutput("No engine version available to evaluate with.", true);
      return;
    }
    var btn = el("runBtn");
    btn.disabled = true;
    btn.textContent = "Running…";
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
        if (!res.ok || res.data.error) {
          setOutput(res.data.error || "Something went wrong.", true);
        } else {
          setOutput(res.data.output || "(no output)");
        }
      })
      .catch(function () {
        setOutput("Network error — couldn't reach the server.", true);
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
        if (window.editor) window.editor.setValue(ex.code);
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

  document.addEventListener("DOMContentLoaded", function () {
    setEngine(engine);
    buildExamplesMenu();

    el("engineToggle").addEventListener("click", function (e) {
      var btn = e.target.closest(".engine-btn");
      if (btn) setEngine(btn.dataset.engine);
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

    require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.46.0/min/vs" } });
    require(["vs/editor/editor.main"], function () {
      registerHcl(window.monaco);
      window.editor = monaco.editor.create(el("editor"), {
        value: EXAMPLES[0].code,
        language: "hcl",
        theme: "vs-dark",
        fontSize: 14,
        fontFamily: "'JetBrains Mono', monospace",
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 14 },
      });
      window.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run);
    });
  });
})();
