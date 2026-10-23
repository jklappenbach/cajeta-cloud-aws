---
id: aws-s3-object-store
applies-to: [dev/cajeta/cloud/aws/S3ObjectStore, dev/cajeta/cloud/aws/HttpS3Transport, dev/cajeta/cloud/aws/S3Errors]
title: Amazon S3 behind the object-store port — connecting, conditional writes, streaming and multipart
description: Build an S3ObjectStore for a bucket (AWS or an S3-compatible endpoint), and know how its conditional writes, listing, streaming reads and writes, multipart uploads and errors behave.
---

# S3 as the object store

`dev.cajeta.cloud.aws.S3ObjectStore` implements cajeta-cloud's `ObjectStore`
over S3's REST API. Code written against the port runs unchanged.

## Connect

```cajeta
import dev.cajeta.cloud.aws.S3ObjectStore;

// AWS: credentials and region from the chain (AwsConfig, AWS_* env, ~/.aws/credentials)
S3ObjectStore store #= S3ObjectStore.connect("my-bucket", null, false, null);

// An S3-compatible service (MinIO, R2, ...): its base URL, path-style addressing
S3ObjectStore local #= S3ObjectStore.connect("my-bucket", "http://localhost:9000", true, config);
```

Addressing is virtual-host style (`https://<bucket>.s3.<region>.amazonaws.com/`)
unless `pathStyle`. A missing key or region throws `AwsConfigurationException`
naming every step of the chain; `connect` itself calls nothing.

## Behaviour that matters

- **Conditional writes** are S3's: `putIfAbsent` sends `If-None-Match: *`,
  `putIfMatch` sends `If-Match: <etag>`. A lost condition returns
  `CondResult(won = false, etag = current)`, the current etag read with a HEAD
  (`""` when the key is absent). A 409 `ConditionalRequestConflict` (a racing
  conditional write) is retried three times, then thrown `TRANSIENT`.
- **Etags** are S3's, quotes included (`"9b2cf5..."`). Pass them back unchanged.
- **Listing** is ListObjectsV2, UTF-8 binary order. The page token is S3's
  continuation token; `""` on the last page.
- **Streaming**: `openWrite` holds one part (8 MiB by default) and becomes a
  multipart upload only when a second part starts, so an object of any size
  costs one part of memory; `openRead` pulls one part-sized range at a time.
  At 8 MiB parts the port's writer reaches 78 GiB (10,000 parts).
- **Multipart** through `beginMultipart`: parts in any order, a re-upload
  replaces. S3 requires every part but the last to be at least 5 MiB
  (`EntityTooSmall` otherwise). An aborted upload leaves nothing readable; set
  a bucket lifecycle rule to clean up uploads a crashed process never aborted.
- **delete** issues HEAD then DELETE, because S3 answers 204 either way; the
  port's "true when it existed" needs the HEAD.
- **getRange** clamps at the end of the object; an offset at or past the end
  throws `PROVIDER_ERROR` (S3's 416).
- **copy** is CopyObject: server side, objects up to 5 GiB.

## Errors

S3's `<Error><Code>` maps to `CloudException` kinds: `NoSuchKey`/`NoSuchUpload`
→ `NOT_FOUND`; `AccessDenied`, `InvalidAccessKeyId`, `SignatureDoesNotMatch`,
`ExpiredToken` → `ACCESS_DENIED`; `PreconditionFailed` →
`PRECONDITION_FAILED`; `SlowDown`, `ServiceUnavailable`, `InternalError`,
`RequestTimeout` → `TRANSIENT`; `NoSuchBucket` and the rest →
`PROVIDER_ERROR` (a misconfigured bucket is not a missing object). A HEAD has
no body, so its status alone decides.

## Testing without AWS

`new S3ObjectStore(transport, bucket, partSize)` takes any `S3Transport`;
cloud-aws's suite runs the port's `ObjectStoreContract` against an in-memory
bucket (`FakeS3`). Against a real bucket set `CAJETA_AWS_TEST_BUCKET` (and
`CAJETA_AWS_TEST_S3_ENDPOINT`, `CAJETA_AWS_TEST_S3_PATH_STYLE=1` for an
S3-compatible service).
