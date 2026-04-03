# 抖音内容爬取工具

基于 Crawl4AI 的抖音内容爬取工具，支持视频和图片资源提取。

## 安装说明

项目已成功安装并配置完成！

## 使用方法

### 1. 基础版爬取工具

```bash
python tiktok_scraper.py
```

功能：
- 基础页面爬取
- 提取视频和图片资源
- 简单易用的交互界面

### 2. 高级版爬取工具（推荐）

```bash
python tiktok_scraper_advanced.py
```

功能：
- 两种爬取模式：
  - 基础模式：快速爬取页面内容
  - 高级模式：网络请求捕获，更全面的资源发现
- 使用 undetected-chromium 反检测浏览器
- 支持网络请求捕获
- 自动滚动页面加载更多内容
- 结果导出为 JSON 文件

## 注意事项

⚠️ **重要提示**：

1. **反爬机制**：抖音有严格的反爬机制，可能需要多次尝试
2. **遵守条款**：请遵守抖音的使用条款和 robots.txt
3. **合法使用**：仅用于学习和研究目的
4. **请求间隔**：建议使用合理的请求间隔
5. **用户代理**：使用真实的用户代理

## 高级功能

### 使用代理

如需使用代理，可以修改脚本中的 `BrowserConfig`：

```python
from crawl4ai.async_configs import ProxyConfig

browser_config = BrowserConfig(
    proxy_config=ProxyConfig(server="http://your-proxy:port")
)
```

### 使用持久化会话

```python
browser_config = BrowserConfig(
    user_data_dir="/path/to/profile",
    use_persistent_context=True
)
```

## 文件说明

- `tiktok_scraper.py` - 基础版爬取工具
- `tiktok_scraper_advanced.py` - 高级版爬取工具（推荐）
- `TIKTOK_SCRAPER_README.md` - 本说明文件

## 技术支持

如遇问题，请查看：
- Crawl4AI 官方文档：https://docs.crawl4ai.com
- 项目 GitHub：https://github.com/unclecode/crawl4ai
