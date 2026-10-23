# cajeta-cloud-aws

The AWS adapters for [`dev.cajeta.cloud`](https://github.com/jklappenbach/cajeta-cloud)'s
ports, written in Cajeta:

| Port | Adapter | Selection |
|---|---|---|
| identity (`UserPool`, `Authenticator`, `Account`, `TokenVerifier`) | Amazon Cognito user pools, SRP sign-in, TOTP | `IDENTITY_PROVIDER=cognito` |
| object store | Amazon S3 and S3-compatible endpoints, conditional writes, multipart | `S3ObjectStore.connect(bucket, ...)` |

Requests are signed with AWS Signature Version 4 over
[cajeta-http](https://github.com/jklappenbach/cajeta-http). Credentials resolve
from an `AwsConfig` component, then the `AWS_*` environment variables, then
`~/.aws/credentials` (`AWS_PROFILE` or `default`).

The Cognito adapter reads `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID` and the
optional `COGNITO_CLIENT_SECRET`, and declares the capabilities the pool's own
configuration grants; the skill `aws-cognito-identity` covers its behaviour.

**Status: in development (0.1.0 unreleased).** The plan is
`cajeta-cloud-adapters` in the cajeta repository's `agents/`.

## Build and test

```sh
./run-tests.sh
```

The suite needs no AWS account: SigV4 is proven against AWS's published test
vectors, and the Cognito adapter against scripted responses in the shapes the
cognito-idp API reference documents, with a test double that plays the server
side of SRP and checks the client's claim; the S3 adapter against an in-memory
bucket that answers in S3's documented shapes, with the port's conformance
suite run over it. The identity conformance suite runs
against a real pool when `CAJETA_AWS_TEST_POOL` and `CAJETA_AWS_TEST_CLIENT`
are set, and against a real bucket when `CAJETA_AWS_TEST_BUCKET` is; both are
skipped otherwise. Dependency archives
resolve from `~/.olla` or Olla at the versions `cajeta.json` pins;
`CODEC_CJA=`, `HTTP_CJA=` and the like override one with a local build.

## License

Apache-2.0.
