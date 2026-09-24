# Clean-room frontend audit

REPROVE was built from a fresh application structure around scientific preregistration and replication. It does not reuse the PATHCLOCK route model, component names, page composition, visual system or security-review metaphor, and it does not use an `ometere123` frontend as a starter.

## Route surface

REPROVE uses only:

- `/`
- `/lab`
- `/claim/[studyKey]`
- `/attempt/[attemptKey]`
- `/archive/[recordKey]`

The release guard rejects old-style route directories such as dashboard, console, release, proof, account, protocol, incidents, settlements and agreements.

## Information architecture

The product is organized as a Replication Atlas → frozen protocol paper → replication notebook → archive record. It deliberately avoids control-room dashboards, security release rooms, agreement ledgers, incident consoles and ABI-shaped forms.

## Component architecture

There are no generic project-shell components named `Header.tsx`, `Footer.tsx`, `WalletButton.tsx`, `TxNotice.tsx`, `Sidebar.tsx` or `Dashboard.tsx`. Product surfaces and domain modules are named for research concepts instead.

## Visual system

The REPROVE palette is cool and research-oriented:

- glacier `#edf5fb`
- sheet `#f8fbfe`
- ink `#11243e`
- cobalt `#2457d6`
- violet `#6e47d8`
- magenta `#c13d87`
- cyan `#177f9b`

The release guard explicitly rejects the prior PATHCLOCK warm palette tokens.

## Guard

Run:

```bash
python3 scripts/release_check.py
```

A guard failure is a release blocker.

## Exact colour collision check

Before handoff, exact-code searches across the accessible `github.com/ometere123` repositories returned no matches for REPROVE's primary palette values `#edf5fb`, `#11243e`, `#2457d6`, `#6e47d8`, `#c13d87`, or `#177f9b`. This is an additional collision check, not a substitute for visual review.
