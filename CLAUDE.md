# cajeta-cloud-aws

The Cognito adapter and the AWS way into S3 for dev.cajeta.cloud (package
`dev.cajeta.cloud.aws`). The S3 client is `dev.cajeta.cloud.s3` (sibling
`cajeta-cloud-s3`, since 2026-10-30); `AwsS3.connect` builds one from the chain.
Spec and plan: `specs/cajeta-cloud-adapters-spec.md` and
`agents/cajeta-cloud-adapters-plan.md` in the cajeta repository; this repo
carries no specs of its own.

## Build & test

```sh
./run-tests.sh      # resolves dependency archives, builds the .cja, runs @Test discovery
```

No test reaches AWS. Before codec 0.9.0 is on Olla, point `CODEC_CJA` at a
local cajeta-codec build.

## Rules

- Test first: the failing test before the implementation, every change.
- Nothing logs a credential. A missing key fails at configuration time naming
  the chain's steps, never a value.
- Releases ship from the `release` branch; CI's guard refuses a tag not on it.
