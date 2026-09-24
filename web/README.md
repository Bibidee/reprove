# REPROVE web

The frontend is a clean-room Next.js application with five routes only:

- `/`
- `/lab`
- `/claim/[studyKey]`
- `/attempt/[attemptKey]`
- `/archive/[recordKey]`

Copy `.env.example` to `.env.local` after the canonical Studionet contracts are deployed. The application uses an injected EIP-1193 wallet and talks directly to GenLayer; there is no backend database or server wallet.
