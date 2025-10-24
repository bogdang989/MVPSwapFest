import * as fcl from "@onflow/fcl";
import { init } from "@onflow/fcl-wc";

const WC_PROJECT_ID = "56fce212e878d76623e53be15ab998c5";

// 1️⃣ Standard FCL configuration
fcl.config()
  .put("app.detail.title", "MVP on Flow")
  .put("app.detail.icon", "https://mvponflow.cc/favicon.png")
  .put("accessNode.api", "https://rest-mainnet.onflow.org")
  .put("discovery.wallet", "https://fcl-discovery.onflow.org/authn")
  .put("flow.network", "mainnet")
  .put("discovery.authn.include", ["0x33f75ff0b830dcec"])
  .put("discovery.authn.exclude", ["0x95b85a9ef4daabb1", "0x55ad22f01ef568a1"]);

// 2️⃣ Add WalletConnect 2.0 support
init({
  projectId: WC_PROJECT_ID,
  metadata: {
    name: "MVP on Flow",
    description: "Fan-powered Jokic project",
    url: "https://mvponflow.cc",
    icons: ["https://mvponflow.cc/favicon.png"]
  }
}).then(({ FclWcServicePlugin }) => {
  fcl.pluginRegistry.add(FclWcServicePlugin);
});
