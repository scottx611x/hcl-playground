# HCL Playground

Evaluate **HCL** expressions in your browser with **Terraform** or **OpenTofu** —
no install, no project, no `init`/`console` loop. Type an expression, hit Run.

![HCL Playground](docs/screenshot.png)

<!-- TODO: replace the screenshot above with a fresh demo video/GIF -->

## Why

You just want to see how [`setproduct()`](https://developer.hashicorp.com/terraform/language/functions/setproduct)
behaves on your `locals`, or test a gnarly `for` expression. Normally that means
the full [toil](https://github.com/hashicorp/terraform/issues/24094#issuecomment-1825482867):

- Install Terraform
- Set up a new project
- Write some HCL
- `terraform init`
- `terraform console`
- "Oops, a typo" → `Ctrl+C` → edit the `locals` block → `terraform console` → rinse and repeat

If you've ever gone deep cobbling together functions to massage some complex
inputs, you catch my drift. **HCL Playground skips all of it** — type an
expression, hit Run. Works with **Terraform** or **OpenTofu**, any version
(baked in or installed on demand), with autocomplete from the engine itself.

## Getting Started

### Prerequisites

- Docker installed on your local machine
- Git (for cloning the repository)

### Run it (one command)

```bash
make run        # build + run on http://localhost:8080
```

That's it — it's a single stateless container. `/scratch` is an ephemeral
per-request work area inside the container, so there's no volume/DB/cluster to
set up.

Other targets:

```bash
make secure     # run with container hardening (read-only fs, dropped caps, mem/pid limits)
make test       # build with dev deps and run the unit tests in the container
make e2e        # run Cypress against a running instance (start `make run` first)
```

Engine versions are baked in at build time; override with build args:

```bash
docker build --build-arg TF_VERSIONS="1.9.8 1.8.5" \
             --build-arg TOFU_VERSIONS="1.8.5 1.7.3" -t hcl-playground .
```

Other versions are pulled on demand from official, checksum-verified sources (and
cached — in S3 for the hosted deploy).

## Security

User input runs through `<engine> console` in a deliberately locked-down way:

- **No shell.** Commands run as argv lists (`shell=False`); the engine + version
  are validated and never interpolated into a command.
- **Offline, expression-only.** Only `locals` blocks and console expressions are
  accepted — providers, resources, data sources, modules, backends, and
  filesystem functions (`file()`, `templatefile()`, …) are rejected, and `init`
  runs with `-backend=false`. So evaluation makes no network calls and can't read
  the filesystem.
- **Bounded.** Per-run wall-clock timeout + CPU/file/process rlimits; request size
  capped; runs non-root with capabilities dropped.
- **No reflection.** Evaluation is an async JSON API (`POST /evaluate`) — code is
  never echoed into the page (no XSS), and it's JSON-only (CSRF-resistant).

## Authors

- **Scott Ouellette** - *Initial work* - [scottx611x](https://github.com/scottx611x)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
