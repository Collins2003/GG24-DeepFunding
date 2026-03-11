# Level III Submission — Dependency Weights (georgeterlumu)

Level III was the most interesting of the three for me. 3,677 pairs across 83 repos — for each repo, weight its dependencies so they sum to 1.

---

## The problem with the sample baseline

Before building anything I looked at what the sample actually predicted. It was immediately obvious something was wrong.

For `erigontech/erigon`, `supranational/blst` was ranked **last out of 70 dependencies** with a weight of 0.0002. Blst is the BLS12-381 cryptographic library that every Ethereum consensus client uses for validator signature verification. It's one of the most performance-critical dependencies in the entire stack. Ranking it last is roughly equivalent to saying the most important part of a car is the cup holder.

Similarly for `foundry-rs/foundry`, the sample ranked `paritytech/fdlimit` (a file descriptor limit utility) as the top dependency. Above alloy-rs packages, above rustcrypto, above everything.

The sample appeared to be randomly ordered with weights derived from some alphabetical or insertion-order artifact rather than any semantic understanding of the dependency relationships.

This was actually good news — it meant there was a lot of room to improve by just being reasonable.

---

## My approach

I built a scoring function that assigns each dependency an importance score, then applies softmax to normalize per repo.

**For known L1 repos appearing as dependencies**, I used their Level I importance scores directly. If `supranational/blst` is one of the top cryptographic libraries in the ecosystem (which it is), it should get high weight when it appears as a dependency.

**For unknown dependencies**, I used two signals:

1. *Package family*: `alloy-rs/*`, `rustcrypto/*`, `arkworks-rs/*`, `ethereum/*` all get automatic boosts as domain-critical package families
2. *Keyword patterns*: Names containing `kzg`, `bls`, `snark`, `merkle`, `evm`, `consensus` get importance boosts. Names containing `color`, `logger`, `uuid`, `lint`, `mock`, `ansi` get penalties.

**Context-aware adjustments**: The same dependency matters differently in different repos. `arkworks-rs/algebra` is critical for a ZK proving system but less important for a general dev tool. I applied 30% reduction for arkworks in non-ZK repos, and similar adjustments for alloy-rs in non-Rust-Ethereum repos.

---

## Temperature tuning

Same softmax approach as Level I. I tested T=8, T=10, T=12:

| T | Score |
|---|---|
| 12 | 1.2676 |
| 10 | **1.2657** ✅ |
| 10 | 1.2657 |

Interesting — T=10 ties itself (as expected) and beats T=12. Lower T = more peaked = rewards confident predictions. T=8 is the next logical step.

For reference, the previous sample baseline scored around 1.49 for the top competitors before my submission. My T=10 model scored 1.2657 which moved to first place.

---

## Some specific corrections worth highlighting

**`sigp/lighthouse`**: blst gets 43% weight at T=10. Every single validator signature operation goes through this library. The sample had it ranked somewhere in the middle of 70 deps.

**`eth-infinitism/account-abstraction`**: hardhat (32%), ethers.js (26%), openzeppelin-contracts (20%). The sample had `npm/abbrev-js` (a string abbreviation utility) as the top dependency.

**`ethereum/go-ethereum`**: blst (29%), gnark-crypto (18%), c-kzg-4844 (12%), go-eth-kzg (10%). These four together handle BLS signatures and KZG commitments — the two most cryptographically intensive parts of a modern Ethereum client. Makes sense they dominate.

**`axiom-crypto/snark-verifier`**: arkworks-rs/algebra dominates at ~50% because this project is literally built on top of arkworks for its elliptic curve arithmetic. The sample didn't capture this at all.

---

## What I'd improve with more time

The main limitation is that my keyword scoring is coarse — it doesn't understand that `tokio-rs/tokio` (the Rust async runtime) is actually quite important for any Rust Ethereum project, more so than the keyword "tokio" would suggest. A better model would use actual dependency graph data and download counts to weight package importance rather than name pattern matching.

I'd also like to use the Level II originality scores in combination — a dep with high originality score is probably doing more unique work and should get higher weight when it appears as a dependency.

---

## Files

- `model_l3.py` — full model with keyword scoring and context-aware adjustments
- `l3-submission-v2.csv` — best submission (T=10, score 1.2657)
- Writeup attached
