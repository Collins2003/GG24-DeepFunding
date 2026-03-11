# GG24 Deep Funding Contest — Model Submissions

Author:Collins Aondongu  Contest: [Gitcoin GG24 Deep Funding](https://joinpond.ai)  
**Levels:** I, II, and III  

---

## Results Summary

| Level | Task | Best Score | Approach |
|---|---|---|---|
| **Level I** | Assign weights to 98 repos (sum to 1) | **1.1930** | Softmax + temperature tuning |
| **Level II** | Originality score per repo (0-1) | **0.2250** | Category taxonomy + iterative blend |
| **Level III** | Weight 3,677 dependency pairs | **1.2657** | Keyword importance + context-aware softmax |

---

## Repository Structure

```
├── level1/
│   ├── model.py                  # Scoring model with softmax
│   ├── l1-submission-v6.csv      # Best submission (T=4, score 1.1930)
│   └── WRITEUP.md                # Full methodology writeup
│
├── level2/
│   ├── model_l2_v2.py            # Model with iterative blend refinement
│   ├── l2-submission-v4.csv      # Best submission (score 0.2250)
│   └── WRITEUP.md                # Full methodology writeup
│
├── level3/
│   ├── model_l3.py               # Keyword + package family scoring
│   ├── l3-submission-v2.csv      # Best submission (T=10, score 1.2657)
│   └── WRITEUP.md                # Full methodology writeup
│
└── README.md                     # This file
```

---

## Level I — Seed Node Weights

**Task:** Assign relative importance weights to 98 Ethereum repos. All weights sum to 1. Scored using Huber loss on log-ratios of pairwise jury comparisons.

**Core insight:** The scoring function rewards *confident correct predictions*. A flat (uniform) distribution scores terribly because it expresses no ratio preferences. The jury has strong opinions about relative importance — so the model needs to too.

**Model:** Softmax over hand-scored repos:
```
weight_i = exp(score_i / T) / sum(exp(score_j / T))
```

Repos scored by category:
- Compilers & languages (Solidity, Vyper): 95–100
- Core clients (geth, reth, lighthouse): 85–98  
- Consensus specs / EIPs: 94–96
- Dev tooling (hardhat, foundry, ethers.js): 87–92
- Crypto primitives (blst, noble-curves): 85–88
- Infrastructure / wrappers: 28–75

**Temperature tuning results:**

| T | Max/Min Ratio | Score |
|---|---|---|
| 35 | 7.6x | 0.4064 |
| 25 | 17.8x | 0.3223 |
| 12 | 403x | 0.5395 |
| 8 | 8,103x | 0.7689 |
| 6 | 162,755x | 0.9262 |
| **4** | **65,000,000x** | **1.1930** |

Lower temperature consistently improved scores — the jury has very strong preferences between top repos (especially Solidity vs. everything else).

---

## Level II — Originality Scores

**Task:** Score each repo 0–1 for originality. 1 = primarily original work. 0 = mostly a wrapper/port of dependencies. Scored by MAE against jury averages.

**Core insight:** The sample baseline was systematically wrong — it scored `ethereum/EIPs` at 0.25 (implying high dependency) despite EIPs being pure intellectual proposals with no code dependencies at all. And `simple-optimism-node` (a docker-compose file) at 0.57.

**Scoring tiers:**
- 0.80–0.90: Original compilers, consensus specs, EIPs, novel ZK systems (Plonky3, Miden-VM)
- 0.60–0.75: Novel clients (reth, geth), original tooling (foundry), crypto libs (blst)
- 0.45–0.60: Consensus clients implementing existing spec, smart contract libs
- 0.30–0.45: MEV relay infra, language ports, mixed-dep tools
- 0.15–0.30: Docker/Helm configs, data registries, simple wrappers

**Iterative blend refinement:**

Initial aggressive scores were directionally right but too extreme. Applied systematic 30% blend-back toward sample baseline on large diffs:

```python
new_score = ours - (ours - sample) * 0.30
# applied when |ours - sample| > 0.25
```

| Submission | Strategy | Score |
|---|---|---|
| v1 | Hand-scored | 0.2294 |
| v3 | 30% blend toward sample | 0.2254 |
| **v4** | **Another 30% compound blend** | **0.2250** |
| v5 | 50% blend (too aggressive) | 0.2350 |

Key finding: 30% compounding blend improves; 50% in one shot overshoots.

---

## Level III — Dependency Weights

**Task:** For each of 83 repos, weight their dependencies so all weights per repo sum to 1. 3,677 total pairs. Scored by MAE against jury pairwise comparisons.

**Core insight:** The sample baseline was randomly ordered — `supranational/blst` (the BLS cryptography library fundamental to every consensus client) was ranked **last out of 70 dependencies** for erigon. `fdlimit` (a file descriptor utility) was ranked #1 for foundry. The model just needed to be reasonable.

**Scoring approach:**

1. **Known L1 repos as deps** → use their L1 importance score directly (blst=95, gnark-crypto=90, etc.)
2. **Package family boosts** → `alloy-rs/*`, `rustcrypto/*`, `arkworks-rs/*`, `ethereum/*` all important
3. **Keyword scoring** → `kzg`, `bls`, `snark`, `evm`, `merkle` = boost; `color`, `logger`, `uuid`, `lint` = penalty
4. **Context adjustments** → arkworks reduced 30% for non-ZK repos; alloy-rs reduced 20% for non-Rust-Ethereum repos

**Key corrections vs sample:**

| Repo | Sample top dep | Our top dep | Why |
|---|---|---|---|
| erigon | (blst ranked last) | blst 30%+ | BLS signatures for all consensus ops |
| lighthouse | (blst mid-ranked) | blst 43% | Core validator crypto |
| account-abstraction | abbrev-js | hardhat 32% | Primary dev framework |
| foundry | fdlimit | alloy-evm 15% | EVM execution layer |

**Temperature tuning:**

| T | Score |
|---|---|
| 12 | 1.2676 |
| **10** | **1.2657** |

Lower T continues to improve — T=8, T=6 are next iterations.

---

## Running the Models

```bash
# Level I
python3 level1/model.py

# Level II  
python3 level2/model_l2_v2.py

# Level III
python3 level3/model_l3.py
```

Each model reads the dataset CSV from the current directory and outputs the submission CSV.

---

## Notes on Scoring Mechanics

**Level I & III** use Huber loss on log-ratios of pairwise jury comparisons. This rewards confident predictions that match jury preferences — a uniform distribution scores near zero because it can't express any preference between repos.

**Level II** uses MAE directly against jury-averaged originality scores. The jury averages independent 0–1 ratings from multiple jurors per repo.

In all three cases, the leaderboard updates only when new jury data arrives — not immediately on submission.
