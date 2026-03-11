# Level I Submission — Seed Node Weights (collinsaondongu)

Hey everyone, sharing my approach for Level I. I'll keep this honest about what worked and what didn't since I think that's more useful than just presenting the final result.

---

## What I was trying to solve

The task is assigning weights to 98 repos where all weights sum to 1, scored against jury pairwise comparisons using Huber loss on log-ratios. I spent some time thinking about what that scoring function actually rewards before writing a single line.

The key insight: Huber loss on log-ratios means the jury is essentially saying "repo A is X times more important than repo B." If I get the *ordering* right and make the weights *sufficiently spread out*, I score well. A flat distribution (everyone gets ~0.01) would score terribly because it can't express any ratio preferences at all.

---

## The model

I went with a softmax over hand-scored repos:

```
weight_i = exp(score_i / T) / sum(exp(score_j / T))
```

The temperature T controls how peaked the distribution is. Low T = winner takes most. High T = closer to uniform.

I scored each repo manually based on category:

- **Compilers & languages** (Solidity, Vyper): top tier, 95-100
- **Core clients** (geth, reth, lighthouse): 85-98
- **Consensus specs / EIPs**: 94-96 — these are foundational intellectual work
- **Dev tooling** (hardhat, foundry, ethers.js): 87-92
- **Crypto primitives** (blst, noble-curves): 85-88
- **Infrastructure / infra wrappers**: lower, 28-75

The scoring reflects a view that the jury — Ethereum ecosystem participants — would weight protocol-level work over application tooling, and tooling over pure infrastructure scripts.

---

## What I learned from submissions

This is where it got interesting. I started at T=35 (basically uniform) and worked down:

| Submission | T | Max/Min Ratio | Score |
|---|---|---|---|
| v2 | 35 | 7.6x | 0.4064 |
| v3 | 25 | 17.8x | 0.3223 |
| v1 | 12 | 403x | 0.5395 |
| v4 | 8 | 8,103x | 0.7689 |
| v5 | 6 | 162,755x | 0.9262 |
| v6 | 4 | 65,000,000x | **1.1930** |

Every single step down in temperature improved the score. The relationship is clear: the jury has strong opinions about relative importance, and the scoring function rewards confident predictions that match those opinions. A flat model hedges everything and scores poorly.

At T=4, Solidity gets about 37% of all weight on its own. The jury apparently agrees that Solidity is in a completely different league from most of the other 97 repos — which honestly makes sense. Every smart contract ever written on Ethereum depends on it.

---

## What I'm still exploring

The curve hasn't flattened yet so I'm continuing to test T=3, T=2, T=1. I expect it keeps improving until the model starts over-concentrating on repos the jury doesn't rate as highly as I do — at which point I'd need to revisit the underlying score ordering rather than just the temperature.

The other thing worth exploring is whether the score *ordering* itself can be improved by using on-chain data (GitHub stars, number of dependents, commit frequency) rather than pure manual judgment. I kept it manual for now since the jury is also making judgment calls, but there's probably signal in dependency graphs and usage metrics.

---

## Files

- `model.py` — full Python scoring model with score tiers and softmax
- `l1-submission-v6.csv` — best submission (T=4, score 1.1930)
- Writeup attached

Thanks for running this — genuinely interesting problem.
