# infra — hcl-playground footprint as OpenTofu

The live AWS footprint behind **hcl-playground.com** (plus the **duckoducko**
DNS record) is codified here as OpenTofu. `tofu plan` reports *"No changes. Your
infrastructure matches the configuration."*

## What's managed

- **Compute/storage:** ECR repo, Lambda function (`hcl-playground`, container, 3008 MB, reserved-concurrency 5), S3 engine-cache bucket
- **IAM:** Lambda execution role + basic-execution attachment + the S3 cache inline policy
- **API Gateway (HTTP API):** the API, AWS_PROXY integration, `$default` route, `$default` stage (with the throttle settings), the `apigateway→lambda` invoke permission, the custom domain (`hcl-playground.com`) + API mapping — **all** managed (the original quick-create API was replaced with these explicit resources)
- **Cert + DNS:** ACM cert, the `hcl-playground.com` hosted zone, its apex alias (→ API GW) and the ACM-validation record
- **Guardrail:** the `$20/mo` budget
- **duckoducko:** the `duckoducko.scott-ouellette.com` CNAME record (the `scott-ouellette.com` zone itself is **not** managed here)

## State

State is **remote** in S3 (`hcl-playground-tofu-state`, versioned + private),
locked with OpenTofu's native S3 lockfile (no DynamoDB). The provider lock file
(`.terraform.lock.hcl`) is committed; local state/working files are git-ignored.

## Usage

```bash
tofu init      # configures the S3 backend
tofu plan      # should report no changes
tofu apply
```

`tofu` isn't committed — install OpenTofu (`brew install opentofu`) or drop a
binary here (it's git-ignored). Originally reverse-engineered from a hand-built
footprint via `import`; the import blocks have since been removed.
