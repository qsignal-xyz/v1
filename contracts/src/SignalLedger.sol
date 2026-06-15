// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract SignalLedger {
    error NotOwner();
    error NotOracle();
    error ZeroAddress();

    event OracleUpdated(address indexed previousOracle, address indexed newOracle);
    event SignalCommitted(
        bytes32 indexed signalHash,
        address indexed oracle,
        uint256 timestamp,
        string reportUri
    );

    address public immutable owner;
    address public oracle;

    constructor(address initialOwner, address initialOracle) {
        if (initialOwner == address(0) || initialOracle == address(0)) revert ZeroAddress();
        owner = initialOwner;
        oracle = initialOracle;
        emit OracleUpdated(address(0), oracle);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyOracle() {
        if (msg.sender != oracle) revert NotOracle();
        _;
    }

    function updateOracle(address newOracle) external onlyOwner {
        if (newOracle == address(0)) revert ZeroAddress();
        emit OracleUpdated(oracle, newOracle);
        oracle = newOracle;
    }

    function commit(bytes32 signalHash) external onlyOracle {
        emit SignalCommitted(signalHash, msg.sender, block.timestamp, "");
    }

    function commit(bytes32 signalHash, string calldata reportUri) external onlyOracle {
        emit SignalCommitted(signalHash, msg.sender, block.timestamp, reportUri);
    }
}
