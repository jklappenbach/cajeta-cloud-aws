---
id: aws-sigv4-credentials
applies-to: [dev/cajeta/cloud/aws/SigV4Signer, dev/cajeta/cloud/aws/CredentialChain, dev/cajeta/cloud/aws/AwsCredentials, dev/cajeta/cloud/aws/AwsConfig]
title: Signing a cajeta-http request for AWS — credentials chain and SigV4
description: Resolve AWS credentials and a region the way the adapters do, and sign a ClientRequest with SigV4, including S3's path and payload rules.
---

# Credentials and SigV4 signing

Two pieces, used together by every AWS adapter in `dev.cajeta.cloud.aws`:
`CredentialChain` finds the key, `SigV4Signer` signs a `ClientRequest` with it.

## Resolve credentials and a region

```cajeta
import dev.cajeta.cloud.aws.AwsConfig;
import dev.cajeta.cloud.aws.AwsCredentials;
import dev.cajeta.cloud.aws.CredentialChain;

AwsCredentials creds #= CredentialChain.resolve(config);   // config may be null
String region #= CredentialChain.region(config);
```

First match wins:

1. the `AwsConfig` passed in (when it has both a key id and a secret);
2. `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`, with `AWS_SESSION_TOKEN` if set;
3. the shared credentials file (`AWS_SHARED_CREDENTIALS_FILE`, else
   `~/.aws/credentials`), section `AWS_PROFILE` or `default`.

An **empty** variable counts as unset. Region: `AwsConfig.region()`, then
`AWS_REGION`, then `AWS_DEFAULT_REGION`. When nothing yields a key or region,
both throw `AwsConfigurationException`, whose message names each step and why
it gave nothing. Call them at startup, not per request, so a misconfigured
deployment fails before serving.

Never log an `AwsCredentials` field. `toString()` shows only the key id.

## Sign a request

```cajeta
import dev.cajeta.cloud.aws.SigV4Signer;
import dev.cajeta.http.ClientRequest;

SigV4Signer signer = heap SigV4Signer(region, "s3");
ClientRequest req #= ClientRequest.get("https://examplebucket.s3.amazonaws.com/test.txt");
req.header("Range", "bytes=0-9");
signer.sign(req, creds, nowEpochSeconds);
```

`sign` sets `Host` (when absent), `X-Amz-Date`, `X-Amz-Content-Sha256`,
`X-Amz-Security-Token` (temporary keys only) and `Authorization`. Rules that
matter:

- **Sign last.** Every header present at `sign` time is signed, except
  `Authorization`, `User-Agent`, `Expect` and `X-Amzn-Trace-Id`. A header added
  after signing is unsigned, and one changed after signing breaks the
  signature.
- **Payload.** A buffered body (`req.body(text)`) is hashed. A streamed body
  (`req.body(#Body)`) is signed as `UNSIGNED-PAYLOAD`, which S3 accepts; other
  services want a buffered body.
- **Path.** For service `"s3"` the path is encoded once and never normalized,
  since a key may contain `//` or `.`. Every other service normalizes dot
  segments and encodes the path again, as SigV4 requires.
- **Time.** Pass the current epoch seconds from the application's clock. AWS
  refuses a signature more than 15 minutes from its own clock.

The canonical request, string to sign and signature are public
(`canonicalRequest`, `stringToSign`, `signature`), so a failing request can be
compared against AWS's `SignatureDoesNotMatch` response, which echoes the
canonical request AWS computed.
