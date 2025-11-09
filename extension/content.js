(async () => {
  const url = window.location.href;

  chrome.storage.local.get(["checkedUrls"], async (result) => {
    const checkedUrls = result.checkedUrls || {};

    if (checkedUrls[url]) {
      console.log("URL found in cache:", url, "->", checkedUrls[url]);
      chrome.runtime.sendMessage({ action: "setIcon", path: checkedUrls[url] });
      return;
    }

    try {
      const response = await fetch("https://kvazilliano.online/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });

      const data = await response.json();
      const status = data.status || "unknown";

      let iconPath = "icons/icon_128.png";
      if (status === "malicious") {
        iconPath = "icons/icon_alert.png";
      } else if (status === "clean") {
        iconPath = "icons/icon_ok.png";
      } else if (status === "pending") {
        iconPath = "icons/icon_pending.png";
      }

      checkedUrls[url] = iconPath;
      chrome.storage.local.set({ checkedUrls });

      chrome.runtime.sendMessage({ action: "setIcon", path: iconPath });

    } catch (error) {
      console.error("Error while checking URL:", error);
    }
  });
})();