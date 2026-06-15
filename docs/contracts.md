# QSignal Contracts

QSignal uses `SignalLedger` to timestamp public signal/report commitments on
Mantle. The contract stores an immutable owner, a mutable oracle, and emits a
`SignalCommitted(bytes32,address,uint256,string)` event for each published
report hash.

## Mantle Mainnet

Use the vanity deployment as the canonical QSignal ledger:

- SignalLedger: [`0x0000000c5c652995bdcAe8e78902414A00AF8983`](https://mantlescan.xyz/address/0x0000000c5c652995bdcAe8e78902414A00AF8983#code) — source verified on Mantlescan
- Owner/oracle: `0xaa116bf1647ba3c39579bd25d02172a8da6b42c0`
- CREATE2 factory: `0x4e59b44847b379578588920cA78FbF26c0B4956C`
- Salt: `0x92f256c2f4223c98ebf08d580abd859db36171e6dbb5c8bd801be1c472b39d96`
- Tx: `0x1bad0bdde0ce71bc82dd7fccee568a70f6a46e3b7914b4fdfe8cda5aff2f54d2`

The regular first deployment is preserved for traceability:

- SignalLedger: `0xA6cCd635A593eA2Ea1EB16c826C8f4C23a84DAB4`
- Tx: `0xcea123052e68aee99f22ad795739e71f92394fc8b3ba221905338ca7c7ecd18b`

Full machine-readable deployment data lives in
`contracts/deployments/mantle-mainnet.json`.

## Commands

```bash
forge test
forge build --force
```

Verify the canonical ledger:

```bash
cast code 0x0000000c5c652995bdcAe8e78902414A00AF8983 --rpc-url https://rpc.mantle.xyz
cast call 0x0000000c5c652995bdcAe8e78902414A00AF8983 'owner()(address)' --rpc-url https://rpc.mantle.xyz
cast call 0x0000000c5c652995bdcAe8e78902414A00AF8983 'oracle()(address)' --rpc-url https://rpc.mantle.xyz
```

Publish a report commitment:

```bash
cast send 0x0000000c5c652995bdcAe8e78902414A00AF8983 \
  'commit(bytes32,string)' \
  <report_hash> <report_uri> \
  --rpc-url https://rpc.mantle.xyz \
  --private-key "$PK_MANTLE_QSIGNAL"
```
