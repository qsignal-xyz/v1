let days = [
  {
    date: "2026-06-13:00:00:00",
    action: "Negative",
    proposed: "Recommendation: Allocate to Stable Yield",
    strength: "44/100",
    signal: "Ecosystem Outflow Risk",
    report: [
      "Daily AI Interpretation",
      "Stable outflows and WMNT movement to exchange-linked wallets weaken the setup. The 120d walk-forward health supports a cautious risk-off posture.",
      "Recommendation: allocate idle capital to stable yield for 1-3d. Avoid fresh MNT long exposure until stable inflows recover.",
      "Active signal: ecosystem_outflow_risk. Prior active fires: 55.6% hit, +0.5% median at 1d.",
    ],
    alerts: [
      ["2026-06-13:01:00:00", "medium", "stableMint", "Watch only", "+$1.0M", "-", "USDC mint after the daily signal. New events append at the bottom of the opened day."],
      ["2026-06-13:11:11:11", "medium", "exchangeTransfer", "Prefer yield", "$1.4M", "-", "WMNT moved to exchange-linked wallet. Updated 12m ago; moved 2h ago."],
      ["2026-06-13:22:22:22", "high", "bridgeExit", "Go yield", "-$8.2M", "-", "USDT bridge exit to Ethereum. Updated 4m ago; moved 40m ago."],
    ],
  },
  {
    date: "2026-06-12:00:00:00",
    action: "Neutral",
    proposed: "Recommendation: Allocate to Stable Yield",
    strength: "18/100",
    signal: "No Valid Daily Edge",
    report: [
      "Daily AI Interpretation",
      "No walk-forward-valid parent signal fired. Intraday stable events are mixed and informational.",
      "Stay neutral. Prefer stable yield until a parent signal passes health filters.",
      "No active daily signal. Child alerts are context only.",
    ],
    alerts: [
      ["2026-06-12:09:40:00", "info", "stableMint", "Watch only", "+$2.1M", "-", "USDC mint below p95, not enough to offset exits. Updated 28m ago; minted 5h ago."],
      ["2026-06-12:22:22:22", "medium", "stableMintCluster", "Watch only", "+$5.7M", "-", "USDe mint cluster across two transactions. Updated 3h ago; minted 15h ago."],
    ],
  },
  {
    date: "2026-06-11:00:00:00",
    action: "Positive",
    proposed: "Recommendation: Long MNT",
    strength: "62/100",
    signal: "Ecosystem Growth Confirmed",
    report: [
      "Daily AI Interpretation",
      "Daily long signal aligned with stable inflow and WMNT LP movement. This is the cleanest recent positive setup.",
      "Allow small long exposure for 1-2d. Keep size modest because historical worst cases remain material.",
      "Active signal: ecosystem_growth_confirmed. Prior active fires: 60.0% hit, +1.4% median at 2d.",
    ],
    alerts: [
      ["2026-06-11:02:30:00", "medium", "stableMint", "Supports risk on", "+$3.4M", "-", "USDC mint then DEX routing. Updated 1d ago; minted 2d ago."],
      ["2026-06-11:16:00:00", "medium", "lpWalletTransfer", "Supports risk on", "$780k", "-", "WMNT transfer into LP wallet. Updated 1d ago; moved 2d ago."],
      ["2026-06-11:18:45:00", "high", "stableInflow", "Risk on", "+$12.9M", "-", "USDT inflow p99 event. Updated 1d ago; minted 2d ago."],
    ],
  },
];
