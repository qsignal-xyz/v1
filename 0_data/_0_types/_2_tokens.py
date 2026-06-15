from __future__ import annotations

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

L2_STANDARD_BRIDGE = "0x4200000000000000000000000000000000000010"
USDT0_OFT_ADAPTER = "0xcb768e263fb1c62214e7cab4aa8d036d76dc59cc"
STARGATE_POOL_ETH = "0x4c1d3Fc3fC3c177c3b633427c2F769276c547463"
STARGATE_POOL_USDC = "0xAc290Ad4e0c891FDc295ca4F0a6214cf6dC6acDC"
STARGATE_POOL_USDT = "0xB715B85682B731dB9D5063187C450095c91C57FC"
STARGATE_POOL_METH = "0xF7628d84a2BbD9bb9c8E686AC95BB5d55169F3F1"
RELAY_DEPOSITORY = "0x59916da825d2d2ec1bf878d71c88826f6633ecca"
DEBRIDGE_DLN_SOURCE = "0xeF4fB24aD0916217251F553c0596F8Edc630EB66"
DEBRIDGE_DLN_DESTINATION = "0xE7351Fd770A37282b91D153Ee690B63579D6dd7f"
DEBRIDGE_ROUTER = "0x663DC15D3C1aC63ff12E45Ab68FeA3F0a883C251"
HYPERLANE_ETH_ROUTE = "0xA92D6084709469A2B2339919FfC568b7C5D7888D"
HYPERLANE_USDT_ROUTE = "0x803e7524526c579cCF6Ef0474d03012EdFD0d3Ec"

BRIDGE_PROTOCOLS = {
    L2_STANDARD_BRIDGE.lower(): "Mantle",
    USDT0_OFT_ADAPTER.lower(): "USDT0",
    STARGATE_POOL_ETH.lower(): "Stargate",
    STARGATE_POOL_USDC.lower(): "Stargate",
    STARGATE_POOL_USDT.lower(): "Stargate",
    STARGATE_POOL_METH.lower(): "Stargate",
    RELAY_DEPOSITORY.lower(): "Relay",
    DEBRIDGE_DLN_SOURCE.lower(): "deBridge",
    DEBRIDGE_DLN_DESTINATION.lower(): "deBridge",
    DEBRIDGE_ROUTER.lower(): "deBridge",
    HYPERLANE_ETH_ROUTE.lower(): "Hyperlane",
    HYPERLANE_USDT_ROUTE.lower(): "Hyperlane",
}
GLOBAL_BRIDGE_CONTRACTS = [RELAY_DEPOSITORY, DEBRIDGE_DLN_SOURCE, DEBRIDGE_DLN_DESTINATION, DEBRIDGE_ROUTER]


def token(
    symbol: str,
    address: str,
    decimals: int,
    category: str,
    coingecko_id: str | None,
    *,
    stable: bool = False,
    yield_pool_token: bool = False,
    bridge_type: str = "",
    bridge_contracts: list[str] | None = None,
    bridge_mint_burn: bool = False,
    global_bridges: bool = True,
    alert_min_usd: float = 100_000,
    medium_usd: float = 1_000_000,
    high_usd: float = 5_000_000,
) -> dict[str, object]:
    contracts = [*(bridge_contracts or []), *(GLOBAL_BRIDGE_CONTRACTS if global_bridges else [])]
    contracts = sorted({item.lower() for item in contracts})
    return {
        "symbol": symbol,
        "address": address,
        "stable": stable,
        "yield_pool_token": yield_pool_token,
        "decimals_fallback": decimals,
        "category": category,
        "coingecko_id": coingecko_id,
        "bridge_type": bridge_type,
        "bridge_contracts": contracts,
        "bridge_protocols": {item: BRIDGE_PROTOCOLS.get(item, bridge_type or "bridge") for item in contracts},
        "bridge_mint_burn": bridge_mint_burn,
        "alert_min_usd": alert_min_usd,
        "medium_usd": medium_usd,
        "high_usd": high_usd,
    }


XSTOCKS = [
    ("ABBVx", "0xfbf2398df672cee4afcc2a4a733222331c742a6a", "abbvie-xstock"),
    ("GOOGLx", "0xe92f673ca36c5e2efd2de7628f815f84807e803f", "alphabet-xstock"),
    ("AMZNx", "0x3557ba345b01efa20a1bddc61f573bfd87195081", "amazon-xstock"),
    ("AAPLx", "0x9d275685dc284c8eb1c79f6aba7a63dc75ec890a", "apple-xstock"),
    ("BRK.Bx", "0x12992613fdd35abe95dec5a4964331b1ee23b50d", "berkshire-hathaway-xstock"),
    ("AVGOx", "0x38bac69cbbd28156796e4163b2b6dcb81e336565", "broadcom-xstock"),
    ("CVXx", "0xad5cdc3340904285b8159089974a99a1a09eb4c0", "chevron-xstock"),
    ("KOx", "0xdcc1a2699441079da889b1f49e12b69cc791129b", "coca-cola-xstock"),
    ("LLYx", "0x19c41ea77b34bbdee61c3a87a75d1abda2ed0be4", "eli-lilly-xstock"),
    ("XOMx", "0xeedb0273c5af792745180e9ff568cd01550ffa13", "exxon-mobil-xstock"),
    ("HDx", "0x766b0cd6ed6d90b5d49d2c36a3761e9728501ba9", "home-depot-xstock"),
    ("JNJx", "0xdb0482cfad4789798623e64b15eeba01b16e917c", "johnson-johnson-xstock"),
    ("JPMx", "0xd9fc3e075d45254a1d834fea18af8041207dea0a", "jpmorgan-chase-xstock"),
    ("MAx", "0xb365cd2588065f522d379ad19e903304f6b622c6", "mastercard-xstock"),
    ("MRKx", "0x17d8186ed8f68059124190d147174d0f6697dc40", "merck-xstock"),
    ("METAx", "0x96702be57cd9777f835117a809c7124fe4ec989a", "meta-xstock"),
    ("MSFTx", "0x5621737f42dae558b81269fcb9e9e70c19aa6b35", "microsoft-xstock"),
    ("NVDAx", "0xc845b2894dbddd03858fd2d643b4ef725fe0849d", "nvidia-xstock"),
    ("PEPx", "0x36c424a6ec0e264b1616102ad63ed2ad7857413e", "pepsico-xstock"),
    ("PFEx", "0x1ac765b5bea23184802c7d2d497f7c33f1444a9e", "pfizer-xstock"),
    ("PGx", "0xa90424d5d3e770e8644103ab503ed775dd1318fd", "procter-gamble-xstock"),
    ("SPCXx", "0x68fa48b1c2fe52b3d776e1953e0e782b5044ce28", "spacex-xstocks"),
    ("TSLAx", "0x8ad3c73f833d3f9a523ab01476625f269aeb7cf0", "tesla-xstock"),
    ("UNHx", "0x167a6375da1efc4a5be0f470e73ecefd66245048", "unitedhealth-xstock"),
    ("Vx", "0x2363fd1235c1b6d3a5088ddf8df3a0b3a30c5293", "visa-xstock"),
]


TOKENS = [
    token("WMNT", "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8", 18, "native", "wrapped-mantle", alert_min_usd=100_000, medium_usd=250_000, high_usd=1_000_000),
    token("WETH", "0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111", 18, "eth", "ethereum", bridge_type="standard", bridge_contracts=[L2_STANDARD_BRIDGE, STARGATE_POOL_ETH, HYPERLANE_ETH_ROUTE], bridge_mint_burn=True, alert_min_usd=250_000),
    token("mETH", "0xcDA86A272531e8640cD7F1a92c01839911B90bb0", 18, "eth", "mantle-staked-ether", bridge_type="standard", bridge_contracts=[L2_STANDARD_BRIDGE, STARGATE_POOL_METH], bridge_mint_burn=True, alert_min_usd=250_000),
    token("cmETH", "0xE6829d9a7eE3040e1276Fa75293Bde931859e8fA", 18, "eth", "mantle-restaked-eth", alert_min_usd=250_000),
    token("FBTC", "0xC96dE26018A54D51c097160568752c4E3BD6C364", 8, "btc", "ignition-fbtc", bridge_type="fbtc", bridge_mint_burn=True, alert_min_usd=250_000),
    token("WBTC", "0xCAbAE6f6Ea1ecaB08Ad02fE02ce9A44F09aebfA2", 8, "btc", "wrapped-bitcoin", bridge_type="standard", bridge_contracts=[L2_STANDARD_BRIDGE], bridge_mint_burn=True, alert_min_usd=250_000),
    token("COOK", "0x9F0C013016E8656bC256f948CD4B79ab25c7b94D", 18, "governance", "meth-protocol", alert_min_usd=50_000, medium_usd=100_000, high_usd=500_000),
    token("USDC", "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9", 6, "stable", "usd-coin", stable=True, yield_pool_token=True, bridge_type="standard", bridge_contracts=[L2_STANDARD_BRIDGE, STARGATE_POOL_USDC], bridge_mint_burn=True),
    token("USDT", "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae", 6, "stable", "tether", stable=True, bridge_type="standard", bridge_contracts=[L2_STANDARD_BRIDGE, STARGATE_POOL_USDT, HYPERLANE_USDT_ROUTE], bridge_mint_burn=True),
    token("USDe", "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34", 18, "stable", "ethena-usde", stable=True, yield_pool_token=True, bridge_type="layerzero", bridge_mint_burn=True),
    token("sUSDe", "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2", 18, "stable", "ethena-staked-usde", stable=True, yield_pool_token=True, bridge_type="layerzero", bridge_mint_burn=True),
    token("USDY", "0x5be26527e817998a7206475496fde1e68957c5a6", 18, "stable", "ondo-us-dollar-yield", stable=True, yield_pool_token=True, bridge_type="symbiosis", bridge_mint_burn=True),
    token("USDT0", "0x779ded0c9e1022225f8e0630b35a9b54be713736", 6, "stable", "usdt0", stable=True, yield_pool_token=True, bridge_type="oft", bridge_contracts=[USDT0_OFT_ADAPTER], bridge_mint_burn=True),
    *[token(symbol, address, 18, "rwa", gecko, alert_min_usd=25_000, medium_usd=100_000, high_usd=500_000) for symbol, address, gecko in XSTOCKS],
]


def token_by_address() -> dict[str, dict[str, object]]:
    return {str(token["address"]).lower(): token for token in TOKENS}
