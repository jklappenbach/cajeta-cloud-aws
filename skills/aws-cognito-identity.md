---
id: aws-cognito-identity
applies-to: [dev/cajeta/cloud/aws/CognitoUserPool, dev/cajeta/cloud/aws/CognitoAuthenticator, dev/cajeta/cloud/aws/CognitoAccount, dev/cajeta/cloud/aws/CognitoTokenVerifier, dev/cajeta/cloud/aws/CognitoPoolSettings, dev/cajeta/cloud/aws/CognitoClient]
title: Amazon Cognito behind the identity port — selecting, configuring and using the `cognito` adapter
description: Select the Cognito user-pool adapter with IDENTITY_PROVIDER=cognito, configure its pool, client and credentials, and know how SRP sign-in, challenges, capabilities, attributes and token verification behave.
---

# Cognito as the identity provider

`dev.cajeta.cloud.aws.CognitoUserPool` implements cajeta-cloud's `UserPool`
(with `Authenticator`, `Account` and `TokenVerifier`) over the cognito-idp
JSON API. Code written against the port runs unchanged; only selection and
configuration differ from the memory driver.

## Select and configure

```sh
IDENTITY_PROVIDER=cognito
COGNITO_USER_POOL_ID=us-east-1_AbC123
COGNITO_CLIENT_ID=3n4b5urk1ft4fl3mg5e62d9ado
COGNITO_CLIENT_SECRET=...        # only for an app client with a secret
AWS_REGION=us-east-1             # or AWS_DEFAULT_REGION / an AwsConfig
# AWS credentials (env, ~/.aws/credentials) only for the admin plane
```

```cajeta
IdentitySelector s = IdentitySelector.__cajeta_inject();
UserPool users = s.pool();
users.capabilities().assertAll(required);   // at startup: fails naming what is missing
```

The component reads its configuration on first use, not at construction, so
a build that compiles it in but selects `memory` never touches AWS. A missing
pool or client id throws `AwsConfigurationException` naming the variable.
For code-built pools (tests, several pools) use `CognitoUserPool.over(...)`
or `overSettings(...)` with a `CognitoClient` over any `CognitoTransport`.

## Capabilities follow the pool

With AWS credentials the adapter reads the pool once (GetUserPoolMfaConfig,
DescribeUserPoolClient) and declares exactly what it grants:

- always: `CONFIRMATION`, `CUSTOM_ATTRIBUTES`, `REFRESH`, `JWKS`, `PASSWORD_RESET`;
- `TOTP`, `SMS_OTP`, `EMAIL_OTP` only for factors configured while MFA is not `OFF`;
- `REVOCATION` only when the app client enables token revocation;
- `GROUPS`, `ADMIN` only with credentials (lookup, delete, attributes and
  groups are SigV4-signed admin calls);
- never `INTROSPECTION` or `PASSKEYS`, and not `PASSWORDLESS`.

Without credentials the factors and revocation are declared with a caveat
(the pool could not be read); a factor the pool lacks then fails at use as
`UNSUPPORTED_CAPABILITY`.

## Sign-in

- `signIn` uses `USER_SRP_AUTH`: the password never leaves the process
  (dev.cajeta.crypto's `Srp`). Only if the app client has SRP disabled does it
  fall back to `USER_PASSWORD_AUTH`. Enable `ALLOW_USER_SRP_AUTH` and
  `ALLOW_REFRESH_TOKEN_AUTH` on the app client.
- A challenge comes back as `SignInResult.challenge()`. Pass its `session()`
  back to `respond` unchanged; it carries Cognito's session plus what the
  adapter needs to answer in Cognito's fields. `PASSWORD_VERIFIER` is answered
  internally and never surfaces.
- An unknown user signing in is `INVALID_CREDENTIALS`, never
  `USER_NOT_FOUND`. "Password attempts exceeded" is `LOCKED` with no
  retry-after (Cognito gives none).
- `refresh` keeps the refresh token you passed unless the pool rotates it.
  With an app client secret, `REFRESH_TOKEN_AUTH` needs a SECRET_HASH the port's
  `refresh(token)` cannot compute; prefer a public app client for refresh.
- `signOut` is `RevokeToken`. Access and id tokens already issued stay valid
  offline until `exp`.

## Users and attributes

- Port attribute names are bare. Cognito's standard attributes (`email`,
  `phone_number`, `given_name`, ...) are bare on the wire too; anything else
  is sent as `custom:<name>` and must exist in the pool's schema.
- Lookup by subject uses `ListUsers` filtered on `sub`, which is eventually
  consistent: a user registered a moment ago may read as `USER_NOT_FOUND`.
- `confirm` of an already-confirmed user succeeds.

## Tokens

`verifier().verify(token, TokenUse.ACCESS())` checks offline: key by `kid`,
RS256 signature, issuer `https://cognito-idp.<region>.amazonaws.com/<pool>`,
token use, `client_id` (access) or `aud` (id), expiry. Groups come from
`cognito:groups`. The JWKS is cached for its `Cache-Control` max-age (an hour
if none); an unknown `kid` refetches once, at most once a minute.

## Testing without AWS

`CognitoClient` takes a `CognitoTransport`; script one that returns the API's
documented response shapes. cloud-aws's own suite plays the SRP server side
in `FakeCognito`. The conformance suite against a real pool runs when
`CAJETA_AWS_TEST_POOL` and `CAJETA_AWS_TEST_CLIENT` are set.
