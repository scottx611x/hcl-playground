# infra — hcl-playground footprint as OpenTofu

The live AWS footprint behind **hcl-playground.com** (plus the **duckoducko**
DNS record) was originally built by hand with the `aws`/`gh` CLIs. This directory
codifies it: the resources were **imported** into OpenTofu state with zero
changes — `tofu plan` reports *"No changes. Your infrastructure matches the
configuration."*

## What's managed (16 resources)

- **Compute/storage:** ECR repo, Lambda function (`hcl-playground`, container, 3008 MB, reserved-concurrency 5), S3 engine-cache bucket
- **IAM:** Lambda execution role + the basic-execution attachment + the S3 cache inline policy
- **API Gateway (HTTP API):** the API, the `apigateway→lambda` invoke permission, the custom domain (`hcl-playground.com`) + API mapping
- **Cert + DNS:** ACM cert, the `hcl-playground.com` hosted zone, its apex alias (→ API GW) and the ACM-validation record
- **Guardrail:** the `$20/mo` budget
- **duckoducko:** the `duckoducko.scott-ouellette.com` CNAME record (the `scott-ouellette.com` zone itself is **not** managed here)

## Not managed (on purpose)

The API Gateway **integration**, `$default` **route**, and `$default` **stage**
(including the throttle settings) were created by API Gateway *quick-create*
(`aws apigatewayv2 create-api --target`). The AWS provider refuses to import
quick-create-managed resources, so they remain implicit. See `imports.tf`.

## Usage

```bash
tofu init
tofu plan      # should report no changes
tofu apply
```

`tofu` isn't committed — install OpenTofu (`brew install opentofu`) or drop a
binary here (it's git-ignored).

## State

State is **local** and git-ignored (`*.tfstate`). For durability/collaboration,
move it to a remote backend (e.g. an S3 bucket + DynamoDB lock) — a recommended
next step. The provider lock file (`.terraform.lock.hcl`) **is** committed.
