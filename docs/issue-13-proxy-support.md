# issue 13 – Add Proxy Support  

##  Overview

Task 13 implements **proxy support** for the LinkedIn Scraper. This allows the scraper to route browser traffic through a proxy server, which is useful for:

- Maintaining anonymity while scraping  
- Avoiding IP-based rate limits or temporary bans  
- Accessing LinkedIn content from different geographic locations  

Proxy support is **optional** and fully configurable through the `config.json` file.

---

## ⚙️ Features Implemented

1. **Proxy Configuration**
   - Configurable via `config.json` under `proxy_settings`.
   - Supports both **authenticated** and **unauthenticated** proxies.
   - Example config snippet:
     ```json
     "proxy_settings": {
       "enabled": true,
       "host": "123.45.67.89",
       "port": 8080,
       "username": "proxy_user",
       "password": "proxy_pass"
     }
     ```

2. **Dynamic ChromeDriver Proxy Setup**
   - When proxy is enabled, ChromeDriver routes traffic through the specified host/port.
   - Supports adding proxy extensions for authentication when username/password are provided.
   - Fallbacks to direct connection if proxy is disabled or missing.

3. **Integration with Existing Scraper**
   - Proxy functionality works seamlessly with:
     - Human-like scrolling
     - Search automation
     - Post extraction
     - Anti-bot human mimicry
   - Ensures that all previously implemented features continue to operate correctly under proxy.

4. **Error Handling**
   - Validates proxy settings before initializing ChromeDriver.
   - Logs warnings if proxy is enabled but host/port are missing.
   - Ensures scraper does not crash due to missing or invalid proxy configuration.

5. **Unit Testing**
   - Added `tests/test_proxy_support.py` for:
     - Proxy-enabled initialization
     - Proxy-disabled initialization
     - Proper ChromeDriver setup call checks
   - Dummy proxy extensions used to mock authentication in tests.

---

##  Usage

1. Open `config/config.json`.
2. Enable proxy and provide `host` and `port`. Optionally, provide credentials if required.
3. Run the scraper normally:
   ```bash
   python main.py
