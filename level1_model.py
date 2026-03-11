"""
Deep Funding Contest - Level 1
Ethereum Open Source Dependency Importance Model

Methodology:
- Multi-factor scoring based on repo category, ecosystem role, and domain knowledge
- Weights are derived from a principled taxonomy of the Ethereum stack
- Scoring reflects pairwise jury logic: "has A been more valuable to Ethereum than B?"
"""

import csv
import math

# ─── REPO SCORES ────────────────────────────────────────────────────────────
# Score reflects importance to Ethereum's success. Based on:
# 1. Foundational layer (EVM, consensus, execution clients): highest
# 2. Core developer tooling widely used across ecosystem: high
# 3. Utility libraries and infra: medium
# 4. Specialized/niche tools: lower
#
# Scores are then softmax-normalised so they sum to 1.

RAW_SCORES = {
    # ── CORE PROTOCOL & EXECUTION CLIENTS ──────────────────────────────────
    # These are the literal machinery of Ethereum. Without them, nothing runs.
    "https://github.com/argotorg/solidity":           100,  # The EVM language
    "https://github.com/ethereum/go-ethereum":         98,  # Dominant execution client
    "https://github.com/paradigmxyz/reth":             80,  # Rising modern execution client (Rust)
    "https://github.com/erigontech/erigon":            79,  # Archive-focused execution client
    "https://github.com/NethermindEth/nethermind":     75,  # .NET execution client
    "https://github.com/hyperledger/besu":             72,  # Java execution client (enterprise)
    "https://github.com/erigontech/silkworm":          60,  # C++ execution layer library
    "https://github.com/ipsilon/evmone":               58,  # Fast EVM implementation
    "https://github.com/lambdaclass/ethrex":           38,  # Rust execution client (emerging)

    # ── CONSENSUS CLIENTS ───────────────────────────────────────────────────
    # Post-merge, consensus clients are equally essential to execution clients
    "https://github.com/ethereum/consensus-specs":     96,  # The spec itself — ground truth
    "https://github.com/sigp/lighthouse":              88,  # Most popular consensus client (Rust)
    "https://github.com/OffchainLabs/prysm":           86,  # Most widely deployed consensus client (Go)
    "https://github.com/Consensys/teku":               78,  # Java consensus client
    "https://github.com/status-im/nimbus-eth2":        75,  # Nim consensus client
    "https://github.com/ChainSafe/lodestar":           70,  # JS/TS consensus client
    "https://github.com/grandinetech/grandine":        48,  # Rust consensus client (newer)
    "https://github.com/lambdaclass/lambda_ethereum_consensus": 33,

    # ── CORE SPECS & STANDARDS ──────────────────────────────────────────────
    "https://github.com/ethereum/EIPs":                94,  # EIP process — all protocol changes
    "https://github.com/ethereum/execution-apis":      82,  # JSON-RPC standard
    "https://github.com/ethereum-lists/chains":        65,  # Chain registry (chainlist)

    # ── CRYPTOGRAPHY LIBRARIES ──────────────────────────────────────────────
    # BLS and curve libs underpin the entire PoS validator system
    "https://github.com/supranational/blst":           84,  # BLS12-381 — used by all consensus clients
    "https://github.com/herumi/mcl":                   70,  # BLS lib (used by many)
    "https://github.com/paulmillr/noble-curves":       72,  # Pure JS crypto (widely used)
    "https://github.com/ethereum/js-ethereum-cryptography": 68,
    "https://github.com/ethereum/py_ecc":              62,  # Python BLS/ECC library
    "https://github.com/ChainSafe/bls":                55,  # BLS wrappers (JS)
    "https://github.com/arkworks-rs/algebra":          58,  # Rust algebraic structures (ZK)
    "https://github.com/Consensys/gnark-crypto":       55,  # Go ZK crypto
    "https://github.com/skalenetwork/libBLS":          40,

    # ── ZK PROVING SYSTEMS ──────────────────────────────────────────────────
    "https://github.com/succinctlabs/sp1":             60,  # zkVM (widely adopted)
    "https://github.com/Plonky3/Plonky3":              58,  # Plonky3 proving system
    "https://github.com/lambdaclass/lambdaworks":      48,  # Rust ZK lib
    "https://github.com/risc0/risc0-ethereum":         50,  # RISC Zero zkVM integration
    "https://github.com/EspressoSystems/jellyfish":    42,
    "https://github.com/0xMiden/miden-vm":             45,  # Miden VM (ZK rollup)
    "https://github.com/axiom-crypto/snark-verifier":  44,
    "https://github.com/powdr-labs/powdr":             36,
    "https://github.com/succinctlabs/op-succinct":     42,  # ZK-proven OP stack
    "https://github.com/succinctlabs/rsp":             35,

    # ── DEVELOPER TOOLING ───────────────────────────────────────────────────
    "https://github.com/NomicFoundation/hardhat":      90,  # Most used dev framework
    "https://github.com/foundry-rs/foundry":           89,  # Dominant modern dev toolkit
    "https://github.com/remix-project-org/remix-project": 80,  # Browser IDE — onboards devs
    "https://github.com/vyperlang/vyper":              74,  # Alt smart contract language
    "https://github.com/wighawag/hardhat-deploy":      60,
    "https://github.com/protofire/solhint":            55,  # Solidity linter
    "https://github.com/ApeWorX/ape":                  52,  # Python dev framework
    "https://github.com/argotorg/hevm":                50,  # EVM symbolic executor
    "https://github.com/a16z/halmos":                  44,  # Symbolic testing for Solidity
    "https://github.com/Cyfrin/aderyn":                42,  # Rust Solidity auditor
    "https://github.com/intellij-solidity/intellij-solidity": 45,
    "https://github.com/argotorg/fe":                  38,  # Fe language (EF experimental)
    "https://github.com/evmts/tevm-monorepo":          36,
    "https://github.com/dl-solarity/solidity-lib":     32,
    "https://github.com/argotorg/act":                 30,  # Formal verification language

    # ── FORMAL VERIFICATION & AUDITING ─────────────────────────────────────
    "https://github.com/Certora/CertoraProver":        58,  # Formal verification (industry standard)
    "https://github.com/edb-rs/edb":                   28,

    # ── SMART CONTRACT LIBRARIES ────────────────────────────────────────────
    "https://github.com/OpenZeppelin/openzeppelin-contracts": 92,  # Universal contract library
    "https://github.com/safe-global/safe-smart-account": 74,  # Safe multisig (billions in TVL)
    "https://github.com/eth-infinitism/account-abstraction": 70,  # ERC-4337 reference
    "https://github.com/Vectorized/solady":            62,  # Gas-optimized libs
    "https://github.com/vyperlang/titanoboa":          42,  # Vyper interpreter/testing
    "https://github.com/alloy-rs/alloy":               55,  # Rust Ethereum primitives

    # ── CLIENT LIBRARIES (user-facing) ──────────────────────────────────────
    "https://github.com/ethers-io/ethers.js":          88,  # Most used JS library
    "https://github.com/wevm/viem":                    80,  # Modern TS library (rapidly dominant)
    "https://github.com/ethereum/web3.py":             76,  # Python web3
    "https://github.com/LFDT-web3j/web3j":             62,  # Java web3
    "https://github.com/Nethereum/Nethereum":          58,  # .NET web3

    # ── MEV & BLOCK BUILDING ────────────────────────────────────────────────
    "https://github.com/flashbots/mev-boost":          78,  # Core MEV-boost relay
    "https://github.com/flashbots/mev-boost-relay":    65,
    "https://github.com/flashbots/rbuilder":           52,
    "https://github.com/Commit-Boost/commit-boost-client": 42,
    "https://github.com/aestus-relay/mev-boost-relay": 35,

    # ── NODE INFRASTRUCTURE & STAKING ───────────────────────────────────────
    "https://github.com/libp2p/libp2p":                78,  # p2p networking layer
    "https://github.com/ethpandaops/ethereum-package": 55,
    "https://github.com/ethpandaops/ethereum-helm-charts": 50,
    "https://github.com/ethstaker/eth-docker":         55,
    "https://github.com/dappnode/DAppNode":            55,  # Node deployment for home stakers
    "https://github.com/ethstaker/ethstaker-deposit-cli": 50,
    "https://github.com/wealdtech/ethdo":              45,
    "https://github.com/ethpandaops/checkpointz":      40,

    # ── EXPLORERS & ANALYTICS ───────────────────────────────────────────────
    "https://github.com/blockscout/blockscout":        68,  # Open source block explorer
    "https://github.com/l2beat/l2beat":                62,  # L2 analytics (critical for L2 era)
    "https://github.com/DefiLlama/DefiLlama-Adapters": 60,  # TVL data
    "https://github.com/DefiLlama/chainlist":          58,
    "https://github.com/TrueBlocks/trueblocks-core":   44,
    "https://github.com/otterscan/otterscan":          40,
    "https://github.com/holiman/goevmlab":             40,

    # ── LIGHT CLIENTS ───────────────────────────────────────────────────────
    "https://github.com/a16z/helios":                  52,  # Light client (Rust)
    "https://github.com/NethermindEth/juno":           42,  # Starknet client

    # ── SCAFFOLDING & EDUCATION ─────────────────────────────────────────────
    "https://github.com/scaffold-eth/scaffold-eth-2":  62,  # Developer onboarding tool

    # ── SOURCERY / VERIFICATION ─────────────────────────────────────────────
    "https://github.com/argotorg/sourcify":            65,  # Contract verification
    "https://github.com/shazow/whatsabi":              42,
    "https://github.com/swiss-knife-xyz/swiss-knife":  32,

    # ── DEBUGGING & DEV EXPERIENCE ──────────────────────────────────────────
    "https://github.com/ethdebug/format":              38,
    "https://github.com/OffchainLabs/stylus-sdk-rs":   45,  # Arbitrum Stylus (WASM contracts)

    # ── META / CONTEST ──────────────────────────────────────────────────────
    "https://github.com/deepfunding/dependency-graph":  35,

    # ── L2 ECOSYSTEM ────────────────────────────────────────────────────────
    "https://github.com/taikoxyz/taiko-mono":           52,  # Taiko ZK-rollup (significant L2)
    "https://github.com/smartcontracts/simple-optimism-node": 42,  # OP stack node runner
}


def softmax(scores_dict, temperature=1.0):
    """
    Softmax normalisation — converts raw scores into a probability distribution.
    Temperature controls how "peaked" the distribution is.
    Lower temp = more weight to top repos. Higher = more uniform.
    """
    repos = list(scores_dict.keys())
    raw = [scores_dict[r] / temperature for r in repos]
    max_val = max(raw)
    exp_vals = [math.exp(v - max_val) for v in raw]
    total = sum(exp_vals)
    return {repos[i]: exp_vals[i] / total for i in range(len(repos))}


def generate_predictions(input_csv, output_csv, temperature=12.0):
    # Load repos from input
    with open(input_csv) as f:
        rows = list(csv.DictReader(f))

    repos = [r["repo"] for r in rows]
    parents = {r["repo"]: r["parent"] for r in rows}

    # Check all repos are scored
    missing = [r for r in repos if r not in RAW_SCORES]
    if missing:
        print(f"WARNING: {len(missing)} repos missing scores, assigning default 30:")
        for m in missing:
            print(f"  {m}")
            RAW_SCORES[m] = 30

    # Compute weights
    subset_scores = {r: RAW_SCORES[r] for r in repos}
    weights = softmax(subset_scores, temperature=temperature)

    # Sort descending
    sorted_repos = sorted(repos, key=lambda r: weights[r], reverse=True)

    total = sum(weights.values())
    print(f"\nWeight sum: {total:.8f}")
    print(f"\nTop 10 repos:")
    for r in sorted_repos[:10]:
        print(f"  {weights[r]:.6f}  {r.split('github.com/')[-1]}")
    print(f"\nBottom 5 repos:")
    for r in sorted_repos[-5:]:
        print(f"  {weights[r]:.6f}  {r.split('github.com/')[-1]}")

    # Write output CSV
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["repo", "parent", "weight"])
        for r in sorted_repos:
            writer.writerow([r, parents[r], f"{weights[r]:.18f}"])

    print(f"\nWritten to {output_csv}")
    return weights


if __name__ == "__main__":
    weights = generate_predictions(
        input_csv="repos_to_predict.csv",
        output_csv="l1-submission.csv",
        temperature=12.0,
    )
