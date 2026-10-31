---
id: aws-s3-object-store
applies-to: [dev/cajeta/cloud/aws/AwsS3, dev/cajeta/cloud/aws/CredentialChain, dev/cajeta/cloud/aws/AwsConfig]
title: Amazon S3 behind the object-store port through the AWS credential chain
description: Build an S3ObjectStore for an AWS bucket (or an S3-compatible endpoint) with credentials and region from the AWS chain; the store's behaviour is the shared s3-object-store skill's.
---

# S3 through the AWS chain

The S3 client is `dev.cajeta.cloud.s3` (skill `s3-object-store`), shared with
every S3-compatible provider. `cajeta-cloud-aws` adds the AWS way of building
one: credentials and region from the chain.

```cajeta
import dev.cajeta.cloud.aws.AwsS3;
import dev.cajeta.cloud.s3.S3ObjectStore;

// AWS: credentials and region from the chain (AwsConfig, AWS_* env, ~/.aws/credentials)
S3ObjectStore store #= AwsS3.connect("my-bucket", null, false, null);

// An S3-compatible service reached with AWS-style credentials: its base URL, path style
S3ObjectStore local #= AwsS3.connect("my-bucket", "http://localhost:9000", true, config);
```

The chain is `AwsConfig` first, then `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, the optional `AWS_SESSION_TOKEN` and `AWS_REGION`,
then `~/.aws/credentials` under `AWS_PROFILE` or `default`. A missing key or
region throws `AwsConfigurationException` naming every step; `connect` itself
calls nothing. The store carries `S3Profile.aws()`: every capability declared,
parts of any sizes at 5 MiB or more.

Conditional writes, listing, streaming, multipart and the error mapping are
the shared client's; see `s3-object-store`. Against a real bucket the
conformance suite runs when `CAJETA_AWS_TEST_BUCKET` is set (and
`CAJETA_AWS_TEST_S3_ENDPOINT`, `CAJETA_AWS_TEST_S3_PATH_STYLE=1` for an
S3-compatible service).
