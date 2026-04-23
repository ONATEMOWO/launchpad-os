# LaunchPad OS Browser Clipper Prototype

This prototype extension sends the current page title, URL, and selected text to LaunchPad OS Quick Capture.

## What it does

- Reads the current tab title
- Reads the current tab URL
- Reads selected text on the page when available
- Opens LaunchPad OS Quick Capture with those values prefilled

## Local setup

1. Make sure LaunchPad OS is running locally on port `5001`.
2. Open the browser's extension management page.
3. Enable developer mode.
4. Load this `browser_extension/` folder as an unpacked extension.
5. Open the extension options page and confirm the LaunchPad OS base URL.

## Configuration

- Default base URL: `http://127.0.0.1:5001`
- To change it, open the extension options page and save the correct base URL.
- The clipper removes any trailing slash before opening:

```text
/opportunities/capture/
```

with `source`, `title`, `url`, and `selected_text` query parameters.

## Notes

- This is a lightweight prototype, not a packaged store-ready extension.
- It depends on the authenticated LaunchPad OS session already being available in the browser.
