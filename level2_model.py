"""
Deep Funding Contest - Level II
Originality Score Model - v2 (Iterative Blend Refinement)

Task: Assign each repo a score 0-1 indicating how original its work is
(inversely: how reliant it is on its dependencies)

0.2 = fork/wrapper/port — most value from deps
0.5 = significant original work BUT heavily built on deps
0.8 = primarily original research/engineering, deps are generic

Scoring: Sum of absolute errors (MAE) vs jury average. Lower = better.

Methodology (v2):
- Stage 1: Hand-scored each repo based on category taxonomy
- Stage 2: Iterative 30% blend-back toward sample baseline on diffs >0.25
  This improved MAE from 0.2294 → 0.2254
- Stage 3: Continue systematic blend-back from best submission

Submission history:
  l2-submission.csv    (v1, aggressive)  → 0.2294
  l2-submission-v2.csv (targeted tweaks) → 0.2294
  l2-submission-v3.csv (30% blend-back)  → 0.2254  ← current best
"""

import csv
import copy

# ── BASE SCORES (Stage 1 hand-scored) ────────────────────────────────────────
BASE_SCORES = {
    "https://github.com/argotorg/solidity":             0.88,
    "https://github.com/vyperlang/vyper":               0.85,
    "https://github.com/argotorg/fe":                   0.80,
    "https://github.com/argotorg/act":                  0.72,
    "https://github.com/argotorg/hevm":                 0.68,
    "https://github.com/ethereum/consensus-specs":      0.84,
    "https://github.com/ethereum/EIPs":                 0.82,
    "https://github.com/ethereum/execution-apis":       0.78,
    "https://github.com/ethdebug/format":               0.76,
    "https://github.com/paradigmxyz/reth":              0.82,
    "https://github.com/ethereum/go-ethereum":          0.75,
    "https://github.com/erigontech/erigon":             0.62,
    "https://github.com/NethermindEth/nethermind":      0.62,
    "https://github.com/hyperledger/besu":              0.63,
    "https://github.com/erigontech/silkworm":           0.55,
    "https://github.com/ipsilon/evmone":                0.38,
    "https://github.com/lambdaclass/ethrex":            0.65,
    "https://github.com/sigp/lighthouse":               0.62,
    "https://github.com/OffchainLabs/prysm":            0.52,
    "https://github.com/Consensys/teku":                0.55,
    "https://github.com/status-im/nimbus-eth2":         0.58,
    "https://github.com/chainsafe/lodestar":            0.55,
    "https://github.com/grandinetech/grandine":         0.65,
    "https://github.com/lambdaclass/lambda_ethereum_consensus": 0.48,
    "https://github.com/paradigmxyz/reth":              0.82,
    "https://github.com/ethereum/execution-apis":       0.83,
    "https://github.com/ethereum-lists/chains":         0.25,
    "https://github.com/supranational/blst":            0.75,
    "https://github.com/herumi/mcl":                    0.60,
    "https://github.com/paulmillr/noble-curves":        0.72,
    "https://github.com/ethereum/js-ethereum-cryptography": 0.58,
    "https://github.com/ethereum/py_ecc":               0.68,
    "https://github.com/ChainSafe/bls":                 0.45,
    "https://github.com/arkworks-rs/algebra":           0.80,
    "https://github.com/Consensys/gnark-crypto":        0.78,
    "https://github.com/skalenetwork/libBLS":           0.48,
    "https://github.com/succinctlabs/sp1":              0.72,
    "https://github.com/Plonky3/Plonky3":               0.78,
    "https://github.com/lambdaclass/lambdaworks":       0.75,
    "https://github.com/risc0/risc0-ethereum":          0.72,
    "https://github.com/EspressoSystems/jellyfish":     0.74,
    "https://github.com/0xMiden/miden-vm":              0.78,
    "https://github.com/axiom-crypto/snark-verifier":   0.72,
    "https://github.com/powdr-labs/powdr":              0.75,
    "https://github.com/succinctlabs/op-succinct":      0.38,
    "https://github.com/succinctlabs/rsp":              0.58,
    "https://github.com/NomicFoundation/hardhat":       0.70,
    "https://github.com/foundry-rs/foundry":            0.75,
    "https://github.com/remix-project-org/remix-project": 0.65,
    "https://github.com/vyperlang/titanoboa":           0.62,
    "https://github.com/ApeWorX/ape":                   0.52,
    "https://github.com/protofire/solhint":             0.62,
    "https://github.com/wighawag/hardhat-deploy":       0.55,
    "https://github.com/a16z/halmos":                   0.72,
    "https://github.com/Cyfrin/aderyn":                 0.68,
    "https://github.com/Certora/CertoraProver":         0.80,
    "https://github.com/argotorg/sourcify":             0.58,
    "https://github.com/shazow/whatsabi":               0.72,
    "https://github.com/intellij-solidity/intellij-solidity": 0.58,
    "https://github.com/evmts/tevm-monorepo":           0.38,
    "https://github.com/holiman/goevmlab":              0.65,
    "https://github.com/edb-rs/edb":                    0.68,
    "https://github.com/TrueBlocks/trueblocks-core":    0.68,
    "https://github.com/swiss-knife-xyz/swiss-knife":   0.42,
    "https://github.com/OpenZeppelin/openzeppelin-contracts": 0.58,
    "https://github.com/safe-global/safe-smart-account": 0.62,
    "https://github.com/eth-infinitism/account-abstraction": 0.65,
    "https://github.com/Vectorized/solady":             0.72,
    "https://github.com/dl-solarity/solidity-lib":      0.55,
    "https://github.com/alloy-rs/alloy":                0.65,
    "https://github.com/ethers-io/ethers.js":           0.65,
    "https://github.com/wevm/viem":                     0.62,
    "https://github.com/ethereum/web3.py":              0.52,
    "https://github.com/LFDT-web3j/web3j":              0.42,
    "https://github.com/hyperledger-web3j/web3j":       0.42,
    "https://github.com/Nethereum/Nethereum":           0.35,
    "https://github.com/flashbots/mev-boost":           0.28,
    "https://github.com/flashbots/mev-boost-relay":     0.48,
    "https://github.com/flashbots/rbuilder":            0.68,
    "https://github.com/Commit-Boost/commit-boost-client": 0.48,
    "https://github.com/aestus-relay/mev-boost-relay":  0.38,
    "https://github.com/libp2p/libp2p":                 0.72,
    "https://github.com/ethpandaops/ethereum-package":  0.38,
    "https://github.com/ethpandaops/ethereum-helm-charts": 0.20,
    "https://github.com/ethstaker/eth-docker":          0.22,
    "https://github.com/dappnode/DAppNode":             0.42,
    "https://github.com/ethstaker/ethstaker-deposit-cli": 0.42,
    "https://github.com/wealdtech/ethdo":               0.58,
    "https://github.com/ethpandaops/checkpointz":       0.45,
    "https://github.com/blockscout/blockscout":         0.72,
    "https://github.com/l2beat/l2beat":                 0.70,
    "https://github.com/DefiLlama/DefiLlama-Adapters":  0.38,
    "https://github.com/DefiLlama/chainlist":           0.28,
    "https://github.com/otterscan/otterscan":           0.55,
    "https://github.com/a16z/helios":                   0.75,
    "https://github.com/NethermindEth/juno":            0.62,
    "https://github.com/scaffold-eth/scaffold-eth-2":   0.38,
    "https://github.com/taikoxyz/taiko-mono":           0.65,
    "https://github.com/smartcontracts/simple-optimism-node": 0.22,
    "https://github.com/OffchainLabs/stylus-sdk-rs":    0.62,
    "https://github.com/deepfunding/dependency-graph":  0.45,
}

# ── SAMPLE BASELINE (from contest dataset) ───────────────────────────────────
SAMPLE_BASELINE = {
    "https://github.com/ethpandaops/checkpointz": 0.57,
    "https://github.com/argotorg/act": 0.33,
    "https://github.com/ethdebug/format": 0.74,
    "https://github.com/powdr-labs/powdr": 0.41,
    "https://github.com/evmts/tevm-monorepo": 0.28,
    "https://github.com/TrueBlocks/trueblocks-core": 0.63,
    "https://github.com/shazow/whatsabi": 0.71,
    "https://github.com/chainsafe/lodestar": 0.59,
    "https://github.com/erigontech/silkworm": 0.44,
    "https://github.com/ethpandaops/ethereum-helm-charts": 0.36,
    "https://github.com/DefiLlama/DefiLlama-Adapters": 0.66,
    "https://github.com/blockscout/blockscout": 0.77,
    "https://github.com/argotorg/hevm": 0.22,
    "https://github.com/wevm/viem": 0.48,
    "https://github.com/vyperlang/vyper": 0.80,
    "https://github.com/vyperlang/titanoboa": 0.51,
    "https://github.com/status-im/nimbus-eth2": 0.39,
    "https://github.com/scaffold-eth/scaffold-eth-2": 0.54,
    "https://github.com/OffchainLabs/prysm": 0.31,
    "https://github.com/safe-global/safe-smart-account": 0.47,
    "https://github.com/paradigmxyz/reth": 0.78,
    "https://github.com/openzeppelin/openzeppelin-contracts": 0.26,
    "https://github.com/nomicfoundation/hardhat": 0.69,
    "https://github.com/nethermindeth/nethermind": 0.62,
    "https://github.com/nethereum/nethereum": 0.23,
    "https://github.com/hyperledger-web3j/web3j": 0.34,
    "https://github.com/grandinetech/grandine": 0.73,
    "https://github.com/foundry-rs/foundry": 0.52,
    "https://github.com/ethers-io/ethers.js": 0.58,
    "https://github.com/argotorg/sourcify": 0.40,
    "https://github.com/argotorg/solidity": 0.79,
    "https://github.com/remix-project-org/remix-project": 0.46,
    "https://github.com/ethereum/go-ethereum": 0.61,
    "https://github.com/argotorg/fe": 0.37,
    "https://github.com/ethereum/execution-apis": 0.70,
    "https://github.com/ethereum/eips": 0.25,
    "https://github.com/ethereum-lists/chains": 0.56,
    "https://github.com/ethereum/consensus-specs": 0.74,
    "https://github.com/erigontech/erigon": 0.43,
    "https://github.com/consensys/teku": 0.67,
    "https://github.com/apeworx/ape": 0.29,
    "https://github.com/alloy-rs/alloy": 0.53,
    "https://github.com/a16z/helios": 0.72,
    "https://github.com/swiss-knife-xyz/swiss-knife": 0.38,
    "https://github.com/axiom-crypto/snark-verifier": 0.30,
    "https://github.com/risc0/risc0-ethereum": 0.76,
    "https://github.com/dl-solarity/solidity-lib": 0.55,
    "https://github.com/ethstaker/ethstaker-deposit-cli": 0.33,
    "https://github.com/OffchainLabs/stylus-sdk-rs": 0.41,
    "https://github.com/aestus-relay/mev-boost-relay": 0.46,
    "https://github.com/succinctlabs/rsp": 0.64,
    "https://github.com/edb-rs/edb": 0.71,
    "https://github.com/0xMiden/miden-vm": 0.32,
    "https://github.com/holiman/goevmlab": 0.58,
    "https://github.com/Cyfrin/aderyn": 0.36,
    "https://github.com/Commit-Boost/commit-boost-client": 0.79,
    "https://github.com/NethermindEth/juno": 0.50,
    "https://github.com/lambdaclass/ethrex": 0.63,
    "https://github.com/succinctlabs/sp1": 0.49,
    "https://github.com/succinctlabs/op-succinct": 0.27,
    "https://github.com/a16z/halmos": 0.68,
    "https://github.com/EspressoSystems/jellyfish": 0.44,
    "https://github.com/skalenetwork/libBLS": 0.39,
    "https://github.com/lambdaclass/lambdaworks": 0.73,
    "https://github.com/wealdtech/ethdo": 0.56,
    "https://github.com/dappnode/DAppNode": 0.31,
    "https://github.com/intellij-solidity/intellij-solidity": 0.45,
    "https://github.com/ChainSafe/bls": 0.60,
    "https://github.com/Plonky3/Plonky3": 0.35,
    "https://github.com/Certora/CertoraProver": 0.77,
    "https://github.com/ethstaker/eth-docker": 0.28,
    "https://github.com/supranational/blst": 0.57,
    "https://github.com/wighawag/hardhat-deploy": 0.53,
    "https://github.com/libp2p/libp2p": 0.48,
    "https://github.com/ethereum/js-ethereum-cryptography": 0.65,
    "https://github.com/flashbots/mev-boost-relay": 0.59,
    "https://github.com/flashbots/mev-boost": 0.24,
    "https://github.com/taikoxyz/taiko-mono": 0.62,
    "https://github.com/Vectorized/solady": 0.40,
    "https://github.com/Consensys/gnark-crypto": 0.75,
    "https://github.com/l2beat/l2beat": 0.32,
    "https://github.com/protofire/solhint": 0.55,
    "https://github.com/paulmillr/noble-curves": 0.46,
    "https://github.com/flashbots/rbuilder": 0.71,
    "https://github.com/arkworks-rs/algebra": 0.58,
    "https://github.com/herumi/mcl": 0.30,
    "https://github.com/LFDT-web3j/web3j": 0.69,
    "https://github.com/ethereum/py_ecc": 0.37,
    "https://github.com/lambdaclass/lambda_ethereum_consensus": 0.80,
    "https://github.com/sigp/lighthouse": 0.49,
    "https://github.com/otterscan/otterscan": 0.22,
    "https://github.com/hyperledger/besu": 0.63,
    "https://github.com/ethereum/web3.py": 0.43,
    "https://github.com/eth-infinitism/account-abstraction": 0.52,
    "https://github.com/smartcontracts/simple-optimism-node": 0.57,
    "https://github.com/ipsilon/evmone": 0.27,
    "https://github.com/ethpandaops/ethereum-package": 0.61,
    "https://github.com/DefiLlama/chainlist": 0.35,
}


def blend_toward_sample(base_scores, sample, blend_pct, threshold=0.15):
    """
    Pull scores that differ from sample by more than threshold
    back toward sample by blend_pct.
    e.g. blend_pct=0.30 means: new = ours - diff * 0.30
    """
    result = {}
    for repo, score in base_scores.items():
        s = sample.get(repo.lower(), 0.50)
        diff = score - s
        if abs(diff) > threshold:
            result[repo] = round(score - diff * blend_pct, 4)
        else:
            result[repo] = score
    return result


def generate_submission(input_csv, output_csv, scores):
    lower_scores = {k.lower(): v for k, v in scores.items()}

    with open(input_csv) as f:
        repos = [r["repo"] for r in csv.DictReader(f)]

    missing = [r for r in repos if r.lower() not in lower_scores]
    if missing:
        print(f"WARNING: {len(missing)} repos missing: {missing}")
        for m in missing:
            lower_scores[m.lower()] = 0.50

    out_scores = []
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["repo", "originality"])
        for repo in repos:
            score = lower_scores[repo.lower()]
            writer.writerow([repo, score])
            out_scores.append(score)

    print(f"Written {output_csv}: mean={sum(out_scores)/len(out_scores):.3f} "
          f"min={min(out_scores):.2f} max={max(out_scores):.2f}")


if __name__ == "__main__":
    # v3 = best so far (MAE 0.2254): 30% blend from base
    v3_scores = blend_toward_sample(BASE_SCORES, SAMPLE_BASELINE, 0.30, threshold=0.25)
    generate_submission("repos_to_predict_l2.csv", "l2-submission-v3.csv", v3_scores)

    # v4: another 30% blend from v3 (compounding)
    v4_scores = blend_toward_sample(v3_scores, SAMPLE_BASELINE, 0.30, threshold=0.15)
    generate_submission("repos_to_predict_l2.csv", "l2-submission-v4.csv", v4_scores)

    # v5: 50% blend from v3
    v5_scores = blend_toward_sample(v3_scores, SAMPLE_BASELINE, 0.50, threshold=0.15)
    generate_submission("repos_to_predict_l2.csv", "l2-submission-v5.csv", v5_scores)

    # v6: 40% blend from v3
    v6_scores = blend_toward_sample(v3_scores, SAMPLE_BASELINE, 0.40, threshold=0.15)
    generate_submission("repos_to_predict_l2.csv", "l2-submission-v6.csv", v6_scores)
