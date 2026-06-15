// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SignalLedger} from "../src/SignalLedger.sol";

contract Caller {
    function tryDeploy(address owner, address oracle) external returns (bool) {
        try new SignalLedger(owner, oracle) {
            return true;
        } catch {
            return false;
        }
    }

    function tryUpdate(SignalLedger ledger, address newOracle) external returns (bool) {
        try ledger.updateOracle(newOracle) {
            return true;
        } catch {
            return false;
        }
    }

    function tryCommit(SignalLedger ledger, bytes32 signalHash) external returns (bool) {
        try ledger.commit(signalHash) {
            return true;
        } catch {
            return false;
        }
    }
}

contract SignalLedgerTest {
    function testConstructorSetsOwnerAndOracle() public {
        address owner = address(0xA11CE);
        address oracle = address(0xB0B);
        SignalLedger ledger = new SignalLedger(owner, oracle);

        assert(ledger.owner() == owner);
        assert(ledger.oracle() == oracle);
    }

    function testConstructorRejectsZeroAddresses() public {
        Caller caller = new Caller();

        assert(!caller.tryDeploy(address(0), address(0xB0B)));
        assert(!caller.tryDeploy(address(0xA11CE), address(0)));
    }

    function testOwnerCanUpdateOracle() public {
        SignalLedger ledger = new SignalLedger(address(this), address(this));
        address nextOracle = address(0xBEEF);

        ledger.updateOracle(nextOracle);

        assert(ledger.oracle() == nextOracle);
    }

    function testNonOwnerCannotUpdateOracle() public {
        SignalLedger ledger = new SignalLedger(address(this), address(this));
        Caller caller = new Caller();

        bool ok = caller.tryUpdate(ledger, address(0xBEEF));

        assert(!ok);
        assert(ledger.oracle() == address(this));
    }

    function testNonOracleCannotCommit() public {
        SignalLedger ledger = new SignalLedger(address(this), address(0xCAFE));
        Caller caller = new Caller();

        bool ok = caller.tryCommit(ledger, bytes32("daily-signal"));

        assert(!ok);
    }
}
