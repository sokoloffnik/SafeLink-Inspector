chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "setIcon" && message.path) {
    chrome.action.setIcon({ path: message.path, tabId: sender.tab.id });
  }
});