# Level II Submission — Originality Scores (georgeterlumu)

Posting my Level II approach separately since the problem is fundamentally different from Level I. This one took more iteration to get right.

---

## Understanding the task

Level II asks for a single originality score (0-1) per repo — how much of the project's value comes from its own original work vs. its dependencies. The scoring is MAE against jury averages, so each repo is independent and I'm just trying to predict what the jury thinks.

The sample baseline had some values that immediately stood out as wrong to me:
- `ethereum/EIPs` scored 0.25 (implying it's highly dependent) — but EIPs are pure intellectual proposals with zero code dependencies
- `Plonky3/Plonky3` scored 0.35 — this is a novel ZK proving system, original mathematical research
- `lambdaclass/lambda_ethereum_consensus` scored 0.80 — but this is just an Elixir port of the consensus spec, not original protocol design
- `smartcontracts/simple-optimism-node` scored 0.57 — it's literally a docker-compose file

So the sample baseline had a clear systematic bias: it seemed to score by how "impressive" a project sounds rather than how original its actual work is relative to its deps.

---

## My scoring framework

I categorized repos into tiers:

**High originality (0.75-0.90):** Original compilers (Solidity, Vyper, Fe), consensus-specs, EIPs, novel ZK systems (Plonky3, Miden-VM, lambdaworks, gnark-crypto, arkworks). These invent new things. Their deps are generic math libraries.

**Medium-high (0.60-0.75):** Novel execution clients (reth, geth), original tooling (foundry, hardhat), cryptographic primitives (blst, noble-curves), light clients. Significant original engineering but built on real foundations.

**Medium (0.45-0.60):** Consensus clients implementing the existing spec (Lighthouse, Teku, Nimbus). The spec is someone else's invention; their originality is in the engineering quality.

**Low-medium (0.30-0.45):** MEV relay infra, ports of existing tools to new languages, mixed-dependency tools.

**Low (0.15-0.30):** Docker/Helm configs, data registries like `ethereum-lists/chains`, `simple-optimism-node`.

---

## What the submissions taught me

My first attempt was too aggressive — I pushed EIPs to 0.82, ZK systems to 0.75+, and dropped some sample values hard. It scored 0.2294.

Then I tried pulling all moves larger than 0.25 back 30% toward the sample. Scored 0.2254 — better.

Compounded another 30% blend from there. Scored 0.2250 — even better.

The pattern is consistent: my directional calls are right (EIPs really are more original than the sample says, docker configs really are less original) but the magnitude of my moves was too extreme. The jury is somewhere between my scores and the sample, probably because they're weighing "community value" and "historical significance" alongside pure originality.

| Submission | Strategy | Score |
|---|---|---|
| v1 | Hand-scored | 0.2294 |
| v3 | 30% blend toward sample | 0.2254 |
| v4 | Another 30% compound blend | 0.2250 ✅ best |
| v5 | 50% blend (too far) | 0.2350 ❌ |

The sweet spot seems to be around 30% compounding blend. Going 50% in one shot overshot.

---

## Biggest disagreements with the sample I'm most confident about

**EIPs (0.65 vs sample 0.25):** Every EIP is an original research proposal. There are no code dependencies. The score of 0.25 is definitionally wrong given the task description.

**Plonky3, Miden-VM, powdr (0.64-0.65 vs sample 0.32-0.41):** These projects invented new ZK proof systems. The amount of original mathematical work is enormous. Sample drastically undervalued them.

**simple-optimism-node (0.22 vs sample 0.57):** Docker-compose wrapper. I feel very confident here.

**ethereum-lists/chains (0.25 vs sample 0.56):** JSON data file listing chain metadata. Not a software project in any meaningful sense.

---

## Files

- `model_l2_v2.py` — full model with blend-back methodology
- `l2-submission-v4.csv` — best submission (score 0.2250)
- Writeup attached
