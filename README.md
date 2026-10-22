# cajeta-cloud-aws

The AWS adapters for [`dev.cajeta.cloud`](https://github.com/jklappenbach/cajeta-cloud)'s
ports, written in Cajeta:

| Port | Adapter | Selection |
|---|---|---|
| identity (`UserPool`, `Authenticator`, `Account`, `TokenVerifier`) | Amazon Cognito user pools, SRP sign-in, TOTP | `IDENTITY_PROVIDER=cognito` |
| object store | Amazon S3 and S3-compatible endpoints, conditional writes, multipart | — |

Requests are signed with AWS Signature Version 4 over
[cajeta-http](https://github.com/jklappenbach/cajeta-http). Credentials resolve
from an `AwsConfig` component, then the `AWS_*` environment variables, then
`~/.aws/credentials` (`AWS_PROFILE` or `default`).

**Status: in development (0.1.0 unreleased).** The plan is
`cajeta-cloud-adapters` in the cajeta repository's `agents/`.

## Build and test

```sh
./run-tests.sh
```

The suite needs no AWS account: SigV4 is proven against AWS's published test
vectors and the adapters against recorded responses. Dependency archives
resolve from `~/.olla` or Olla at the versions `cajeta.json` pins;
`CODEC_CJA=`, `HTTP_CJA=` and the like override one with a local build.

## License

Apache-2.0.
