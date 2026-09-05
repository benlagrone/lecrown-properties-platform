# LeCrown Sign Prototype Handoff

## Status

As of 2026-09-04, LeCrown Sign has a validated, standalone reference prototype,
but it is **not integrated into `lecrown-platform`, deployed to
`sign.lecrownproperties.com`, or approved for production transactions**.

The prototype is maintained locally at:

```text
/Users/benjaminlagrone/Documents/projects/real-estate/brokerage-ops
```

Reference commit:

```text
f6441b0 feat: add transaction signing rooms
```

This document records what that prototype proves, what it does not prove, and
how its useful behavior maps into the production architecture already specified
in the [LeCrown Properties Back-Office Execution Roadmap](./real-estate-backoffice-execution-roadmap.md).

## What the prototype proves

The standalone React application demonstrates the complete local interaction
path for a basic multi-party brokerage signing room:

1. Create a signing room linked to a transaction.
2. Upload one PDF agreement.
3. Calculate and display a SHA-256 digest for the uploaded source bytes.
4. Add buyer and seller recipients with an explicit routing order.
5. Open the envelope for signatures.
6. Generate a recipient-specific local signing link.
7. Present an electronic-record disclosure and require affirmative consent.
8. Capture a typed signature and signed date.
9. Prevent the second recipient from signing before the first.
10. Record viewed, consented, signed, and completed application events.
11. Mark the envelope complete after all required signers finish.
12. Generate a PDF package containing the source agreement, an appended
    signature page, and a human-readable audit certificate.

The interface includes a broker-facing Signing Rooms workspace, document
preview, recipient and field inspector, delivery limitations, audit timeline,
signer ceremony, completion state, and executed-package download.

## Validation evidence

The reference commit was validated with:

- seven passing Vitest tests across transaction and signing workflows;
- TypeScript validation and a successful Vite production build;
- headless Chrome coverage at 1440 by 1000 and 390 by 844;
- zero application console warnings or errors during the exercised flow;
- PDF upload and new-envelope creation;
- buyer-to-seller sequential signing through a local signing link;
- completion after two required signatures;
- three-page executed-package generation and rendered visual inspection; and
- no page-level overflow at the tested mobile viewport.

The prototype contains synthetic names, addresses, email addresses, dates, and
contract content. It must not be treated as a real transaction record.

## Current limitations

The prototype is a product and workflow reference, not production signing
infrastructure:

- envelope, recipient, token, event, and PDF data are stored in one browser
  profile rather than server-side PostgreSQL and object storage;
- signing links work only where that browser-local state is available;
- invitation tokens are present in browser state rather than hashed and
  redeemed through a short-lived server session;
- there is no transactional email/SMS delivery, bounce handling, retry queue,
  or delivery reconciliation;
- there is no independent identity verification, one-time challenge, MFA,
  passkey, or risk-based authentication policy;
- the uploaded source hash is recorded, but the event stream and completed
  package are not sealed by a protected platform key;
- signatures are appended on a signature page instead of being rendered into
  validated page coordinates on the immutable source document;
- there are no server-enforced decline, void, expiry, resend, recipient
  correction, or supersession flows;
- there is no malware scan, isolated PDF rendering, active-content rejection,
  retention lock, backup verification, or legal hold;
- there is no broker-approved form/template registry or form-by-form signing
  policy; and
- the consent language and evidence package have not been approved by LeCrown's
  broker, counsel, security owner, or transaction-operations owner.

It must not be described as DocuSign-compatible, DocuSign-certified, legally
equivalent to a particular vendor, or ready for live client signatures.

## Prototype-to-platform mapping

| Prototype behavior | Canonical platform target |
|---|---|
| Browser `SigningRoom` object | `Envelope` tied to brokerage, transaction, source `DocumentVersion`, policy version, sender, expiry, and state |
| Browser recipient list | Server-owned `Recipient` records with role, routing order, delivery target, identity tier, and terminal state |
| Browser fields | Versioned `SigningField` records with page coordinates, validation, recipient ownership, and stable field IDs |
| Local signing link | Hashed, single-use invitation redeemed for a short-lived, rotating `RecipientSession` |
| Consent checkbox | Versioned `ConsentRecord` with disclosure presentation, access test, acceptance, withdrawal path, and timestamps |
| Typed name | `SignatureAdoption` plus explicit intent event; the appearance alone is not identity evidence |
| Local audit array | Append-only `EnvelopeEvent` sequence with server time, actor type, request ID, policy version, and integrity linkage |
| Appended signature/audit pages | Deterministic completed PDF, completion certificate, JSON evidence manifest, and platform integrity seal |
| Browser download | Authorized, short-lived artifact delivery with immutable custody, access audit, and retention policy |

The prototype's TypeScript types are useful as UX vocabulary only. They are not
the production database or API schema.

## Integration with the Contract Copilot

The Contract Copilot and LeCrown Sign must remain separate workflow stages:

```text
conversational intake
  -> deterministic deal sheet
  -> approved form and field map
  -> broker review
  -> immutable source document version
  -> LeCrown Sign envelope preparation and preflight
  -> explicit approve and send
  -> signer delivery, consent, authentication, and signing
  -> finalization and immutable evidence package
```

Conversational input may prepare a draft. It must not select unapproved legal
terms, impersonate a signer, approve broker-only decisions, or send an envelope
without the required preflight and authorization.

## Recommended implementation order

1. Add the production `SigningTemplate`, `Envelope`, `Recipient`,
   `SigningField`, `ConsentRecord`, `RecipientSession`, `EnvelopeEvent`, and
   artifact models through reviewed Alembic migrations.
2. Add brokerage- and matter-scoped permissions for prepare, approve, send,
   void, audit, and sensitive artifact download.
3. Bind envelopes to immutable, scanned, rendered source `DocumentVersion`
   records in object storage.
4. Implement server-controlled lifecycle transitions, optimistic concurrency,
   idempotency keys, and append-only audit events.
5. Build preparation and preflight APIs before enabling delivery.
6. Build the external signer application as a separate minimal surface with no
   general back-office access.
7. Implement hashed single-use invitations, short-lived sessions, rate limits,
   replay resistance, and the approved identity tiers.
8. Version the disclosure, consent, and intent text and capture access evidence.
9. Render accepted values into validated source-document coordinates, calculate
   final hashes, issue the evidence manifest and certificate, and apply the
   protected platform seal.
10. Add delivery/retry reconciliation, completed-copy delivery, retention,
    backup/restore evidence, legal hold, verification tooling, and support
    runbooks.
11. Run synthetic security, authorization, accessibility, mobile, recovery,
    tamper, and disaster-recovery tests.
12. Permit a live pilot only for a broker/counsel-approved low-risk document
    type after all named owners approve the controls.

## Required acceptance gate

LeCrown Sign remains `reference prototype only` until the platform can prove:

- source and completed hashes reproduce and any byte change fails verification;
- a recipient cannot view or alter another recipient's fields;
- invitations cannot be replayed and expired or voided sessions fail closed;
- send and finalization retries do not create duplicate deliveries or artifacts;
- completed records are immutable through product and API paths;
- consent, intent, authentication, delivery, and signature events are associated
  with the exact source version and recipient;
- broker, counsel, security, and operations have accepted the pilot document
  type, disclosure, identity tier, retention policy, and support process; and
- backup restoration and offline evidence-package verification succeed.

Until then, live brokerage transactions must continue through the brokerage's
approved signing and transaction systems. The platform may record a handoff and
reconciled status, but it must not infer that an external document was sent,
viewed, signed, completed, or legally sufficient.
