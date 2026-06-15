// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/SignalLedger.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PK_MANTLE_QSIGNAL");
        address owner = vm.addr(pk);
        address oracle = owner;

        vm.startBroadcast(pk);
        SignalLedger ledger = new SignalLedger(owner, oracle);
        vm.stopBroadcast();

        console.log("SignalLedger deployed at:", address(ledger));
        console.log("Owner:", ledger.owner());
        console.log("Oracle:", ledger.oracle());
    }
}
