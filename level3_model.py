"""
Deep Funding Contest - Level III
Dependency Weight Model v2

Key improvements:
- Package family awareness (alloy-rs/*, rustcrypto/*, arkworks-rs/*)
- Context-aware scoring (arkworks high for ZK repos, moderate for dev tools)
- Moderate temperature (T=10) to avoid extreme over-concentration
- Known L1 repos strongly boosted when they appear as deps
"""

import csv
import math
from collections import defaultdict

# ZK-focused repos (arkworks/lambdaworks/plonky3 are critical here)
ZK_REPOS = {
    'axiom-crypto/snark-verifier', 'lambdaclass/lambdaworks', 'espressosystems/jellyfish',
    '0xmiden/miden-vm', 'plonky3/plonky3', 'powdr-labs/powdr', 'succinctlabs/sp1',
    'risc0/risc0-ethereum', 'consensys/gnark-crypto', 'skalenetwork/libbls',
    'edb-rs/edb', 'succinctlabs/op-succinct',
}

# Rust Ethereum repos (alloy-rs packages are critical here)
RUST_ETH_REPOS = {
    'paradigmxyz/reth', 'foundry-rs/foundry', 'sigp/lighthouse', 'a16z/helios',
    'flashbots/rbuilder', 'grandinetech/grandine', 'commit-boost/commit-boost-client',
    'lambdaclass/ethrex', 'succinctlabs/rsp', 'taikoxyz/taiko-mono',
    'offchainlabs/stylus-sdk-rs', 'evmts/tevm-monorepo',
}

# Known important L1 repos (scored by ecosystem importance)
L1_IMPORTANCE = {
    'supranational/blst': 95,
    'paulmillr/noble-curves': 88,
    'consensys/gnark-crypto': 90,
    'arkworks-rs/algebra': 86,
    'herumi/mcl': 80,
    'ethereum/go-ethereum': 92,
    'paradigmxyz/reth': 90,
    'alloy-rs/alloy': 86,
    'ethers-io/ethers.js': 83,
    'wevm/viem': 81,
    'ethereum/consensus-specs': 90,
    'ethereum/eips': 82,
    'ethereum/execution-apis': 82,
    'argotorg/solidity': 93,
    'foundry-rs/foundry': 88,
    'nomicfoundation/hardhat': 85,
    'libp2p/libp2p': 83,
    'plonky3/plonky3': 86,
    '0xmiden/miden-vm': 85,
    'lambdaclass/lambdaworks': 84,
    'espressosystems/jellyfish': 82,
    'openzeppelin/openzeppelin-contracts': 80,
    'safe-global/safe-smart-account': 78,
    'eth-infinitism/account-abstraction': 80,
    'flashbots/mev-boost': 70,
    'flashbots/mev-boost-relay': 73,
    'ethereum/web3.py': 76,
    'ethereum/js-ethereum-cryptography': 80,
    'sigp/lighthouse': 82,
    'chainsafe/lodestar': 78,
    'status-im/nimbus-eth2': 78,
    'ethdebug/format': 74,
    'argotorg/sourcify': 74,
    'argotorg/hevm': 76,
    'argotorg/fe': 78,
    'argotorg/act': 74,
    'vectorized/solady': 76,
    'protofire/solhint': 72,
    'wighawag/hardhat-deploy': 72,
    'dl-solarity/solidity-lib': 70,
    'ethereum/py_ecc': 76,
    'vyperlang/vyper': 86,
    'grandinetech/grandine': 80,
    'consensys/teku': 78,
    'erigontech/erigon': 82,
    'nethermindeth/nethermind': 80,
    'hyperledger/besu': 78,
    'a16z/helios': 78,
    'risc0/risc0-ethereum': 76,
    'succinctlabs/sp1': 78,
    'powdr-labs/powdr': 80,
    'axiom-crypto/snark-verifier': 78,
    'flashbots/rbuilder': 74,
    'shazow/whatsabi': 72,
    'alloy-rs/alloy-evm': 82,
    'alloy-rs/rlp': 76,
    'alloy-rs/trie': 76,
    'alloy-rs/eips': 78,
    'alloy-rs/hardforks': 72,
    'alloy-rs/chains': 68,
    'alloy-rs/svm-rs': 70,
    'rustcrypto/elliptic-curves': 78,
    'rustcrypto/hashes': 76,
    'rustcrypto/signatures': 76,
    'rustcrypto/formats': 72,
    'rustcrypto/utils': 68,
    'arkworks-rs/snark': 80,
    'arkworks-rs/curves': 82,
    'ethereum/c-kzg-4844': 86,
    'crate-crypto/go-eth-kzg': 84,
    'holiman/uint256': 78,
    'protolambda/zrnt': 78,
    'protolambda/ztyp': 74,
    'protolambda/bls12-381-util': 80,
    'cockroachdb/pebble': 74,
    'syndtr/goleveldb': 72,
    'tokio-rs/tokio': 72,
    'tokio-rs/bytes': 68,
    'sigp/ssz_types': 78,
}

# Important keyword patterns
IMPORTANT_PATTERNS = [
    ('crypto', 15), ('kzg', 20), ('bls', 18), ('bn254', 18), ('secp256', 18),
    ('elliptic', 15), ('snark', 18), ('stark', 16), ('zk', 14), ('proof', 12),
    ('merkle', 14), ('trie', 14), ('sha', 10), ('keccak', 14), ('hash', 10),
    ('ssz', 16), ('rlp', 14), ('abi', 12), ('evm', 16), ('revm', 18),
    ('consensus', 14), ('libp2p', 16), ('discv5', 16), ('p2p', 10),
    ('leveldb', 12), ('rocksdb', 14), ('pebble', 12), ('lmdb', 12),
    ('solidity', 14), ('bytecode', 12), ('opcode', 12),
    ('grpc', 10), ('protobuf', 10), ('wasm', 12), ('cranelift', 14),
    ('blst', 20), ('gnark', 18), ('arkworks', 18),
    ('uint256', 14), ('bigint', 10),
    ('ethereum', 12), ('ethers', 12), ('alloy', 12),
]

UTILITY_PATTERNS = [
    ('color', -12), ('colour', -12), ('ansi', -10), ('terminal', -8),
    ('logger', -10), ('-log', -8), ('tracing-sub', -8),
    ('uuid', -10), ('rand', -6), ('-random', -8),
    ('lint', -12), ('eslint', -14), ('prettier', -12), ('clippy', -10),
    ('mock', -10), ('mocha', -10), ('chai', -12), ('jest', -10),
    ('-fmt', -8), ('abbrev', -14), ('glob', -8), ('minimatch', -10),
    ('clap', -6), ('cobra', -6),
    ('chrono', -8), ('-time', -6),
    ('fdlimit', -14), ('strip-ansi', -14), ('backtrace', -8),
    ('derive_more', -8), ('proc-macro', -6), ('paste', -8),
    ('-yaml', -8), ('-toml', -6), ('-json', -4),
    ('mdbook', -14), ('ripgrep', -12), ('dialoguer', -12),
    ('ratatui', -12), ('comfy-table', -12), ('console-', -10),
    ('test', -6), ('debug-js', -12),
]


def score_dep(dep: str, repo: str) -> float:
    name = dep.lower()
    repo_l = repo.lower()

    # Direct L1 importance lookup
    if name in L1_IMPORTANCE:
        score = float(L1_IMPORTANCE[name])
        # Context adjustments
        if name.startswith('arkworks-rs/') and repo_l not in ZK_REPOS:
            score *= 0.7  # arkworks less critical for non-ZK repos
        if name.startswith('alloy-rs/') and repo_l not in RUST_ETH_REPOS:
            score *= 0.8
        return score

    # Keyword scoring
    score = 35.0
    for pattern, delta in IMPORTANT_PATTERNS:
        if pattern in name:
            score += delta
    for pattern, delta in UTILITY_PATTERNS:
        if pattern in name:
            score += delta

    # Org-level boosts
    org = name.split('/')[0] if '/' in name else ''
    if org in ('rustcrypto', 'arkworks-rs', 'alloy-rs'):
        score += 12
    if org in ('ethereum', 'consensys', 'sigp', 'paradigmxyz'):
        score += 10

    return max(3.0, score)


def softmax(scores, T=10.0):
    exp_s = [math.exp(s / T) for s in scores]
    total = sum(exp_s)
    return [e / total for e in exp_s]


def generate(input_csv, output_csv, T=10.0):
    pairs = []
    with open(input_csv) as f:
        for r in csv.DictReader(f):
            pairs.append((r['dependency'], r['repo']))

    by_repo = defaultdict(list)
    for dep, repo in pairs:
        by_repo[repo.lower()].append(dep)

    pair_weights = {}
    for repo, deps in by_repo.items():
        scores = [score_dep(d, repo) for d in deps]
        weights = softmax(scores, T)
        for dep, w in zip(deps, weights):
            pair_weights[(dep.lower(), repo)] = w

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['dependency', 'repo', 'weight'])
        for dep, repo in pairs:
            w = pair_weights[(dep.lower(), repo.lower())]
            writer.writerow([dep, repo, w])

    # Verify
    sums = defaultdict(float)
    for dep, repo in pairs:
        sums[repo.lower()] += pair_weights[(dep.lower(), repo.lower())]
    assert all(abs(s - 1.0) < 1e-9 for s in sums.values())

    all_w = list(pair_weights.values())
    print(f"T={T}: {len(pairs)} rows | mean={sum(all_w)/len(all_w):.5f} max={max(all_w):.4f}")

    # Show key repos
    by_repo_w = defaultdict(list)
    for (dep, repo), w in pair_weights.items():
        by_repo_w[repo].append((dep, w))
    for r in ['ethereum/go-ethereum', 'foundry-rs/foundry', 'sigp/lighthouse',
              'eth-infinitism/account-abstraction']:
        top = sorted(by_repo_w.get(r, []), key=lambda x: x[1], reverse=True)[:4]
        print(f"  {r}: " + "  ".join(f"{w:.3f} {d}" for d, w in top))

    return output_csv


if __name__ == '__main__':
    generate('pairs_to_predict_l3.csv', 'l3-submission.csv', T=10.0)
