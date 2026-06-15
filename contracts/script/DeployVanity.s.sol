// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/SignalLedger.sol";

/// @notice Deploys SignalLedger through Foundry's canonical CREATE2 deployer.
/// Mine QSIGNAL_SALT with `cast create2` against the full constructor init code.
contract DeployVanity is Script {
    function run() external {
        uint256 pk = vm.envUint("PK_MANTLE_QSIGNAL");
        bytes32 salt = vm.envBytes32("QSIGNAL_SALT");
        address owner = vm.addr(pk);
        address oracle = owner;

        vm.startBroadcast(pk);
        SignalLedger ledger = new SignalLedger{salt: salt}(owner, oracle);
        vm.stopBroadcast();

        console.log("SignalLedger vanity deployed at:", address(ledger));
        console.log("Owner:", ledger.owner());
        console.log("Oracle:", ledger.oracle());
        console.log("Salt:");
        console.logBytes32(salt);

        require(uint160(address(ledger)) >> 132 == 0, "address missing 0x0000000 prefix");
        require(ledger.owner() == owner, "owner mismatch");
        require(ledger.oracle() == oracle, "oracle mismatch");
        console.log("OK: 0x0000000 vanity prefix + owner/oracle verified");
    }
}
