import asyncio
import os
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_configs import ProxyConfig

class AdvancedTikTokScraper:
    def __init__(self, headless=False, use_undetected=True):
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=True,
            browser_type="undetected" if use_undetected else "chromium",
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
            user_data_dir=None,
            use_persistent_context=False,
        )
        
    async def scrape(self, url: str, wait_time: int = 5):
        """爬取抖音内容，支持多种策略"""
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                magic=True,
                word_count_threshold=1,
                js_code=[
                    f"""
                    (async () => {{
                        await new Promise(resolve => setTimeout(resolve, {wait_time * 1000}));
                        
                        const results = {{
                            pageTitle: document.title,
                            pageUrl: window.location.href,
                            videos: [],
                            images: [],
                            networkRequests: [],
                            pageData: {{}}
                        }};
                        
                        const videos = Array.from(document.querySelectorAll('video'));
                        results.videos = videos.map(video => {{
                            return {{
                                src: video.src,
                                currentSrc: video.currentSrc,
                                poster: video.poster,
                                width: video.videoWidth,
                                height: video.videoHeight,
                                duration: video.duration,
                                sources: Array.from(video.querySelectorAll('source')).map(s => s.src)
                            }};
                        }});
                        
                        const images = Array.from(document.querySelectorAll('img'));
                        results.images = images.map(img => {{
                            return {{
                                src: img.src,
                                srcset: img.srcset,
                                alt: img.alt,
                                width: img.naturalWidth,
                                height: img.naturalHeight
                            }};
                        }});
                        
                        const allScripts = Array.from(document.querySelectorAll('script'));
                        results.pageData.scripts = allScripts
                            .filter(s => s.textContent && s.textContent.includes('__INITIAL_STATE__'))
                            .map(s => s.textContent.substring(0, 500));
                        
                        const metaTags = Array.from(document.querySelectorAll('meta'));
                        results.pageData.meta = metaTags.map(m => ({{
                            name: m.name,
                            property: m.getAttribute('property'),
                            content: m.content
                        }}));
                        
                        const links = Array.from(document.querySelectorAll('a[href]'));
                        results.pageData.links = links.map(a => a.href).slice(0, 20);
                        
                        return results;
                    }})();
                    """
                ],
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if result.success:
                return {
                    "success": True,
                    "url": url,
                    "title": result.metadata.get("title", ""),
                    "markdown": result.markdown,
                    "html_length": len(result.html),
                    "media": result.js_result if result.js_result else None,
                    "links": result.links
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }
    
    async def scrape_with_network_capture(self, url: str, wait_time: int = 8):
        """使用网络请求捕获来寻找媒体资源"""
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                magic=True,
                capture_network_requests=True,
                js_code=[
                    f"""
                    (async () => {{
                        await new Promise(resolve => setTimeout(resolve, {wait_time * 1000}));
                        
                        const scrollInterval = setInterval(() => {{
                            window.scrollBy(0, 500);
                        }}, 500);
                        
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        clearInterval(scrollInterval);
                        window.scrollTo(0, 0);
                        
                        return {{
                            videos: Array.from(document.querySelectorAll('video')).map(v => v.src),
                            images: Array.from(document.querySelectorAll('img')).map(i => i.src),
                            pageTitle: document.title
                        }};
                    }})();
                    """
                ]
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if result.success:
                media_requests = []
                if result.network_requests:
                    for req in result.network_requests:
                        url_lower = req.get('url', '').lower()
                        if any(ext in url_lower for ext in ['.mp4', '.webm', '.m3u8', '.ts', '.mp3', '.flv']):
                            media_requests.append({
                                'type': 'video',
                                'url': req.get('url'),
                                'method': req.get('method')
                            })
                        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                            media_requests.append({
                                'type': 'image',
                                'url': req.get('url'),
                                'method': req.get('method')
                            })
                
                return {
                    "success": True,
                    "media_requests": media_requests,
                    "js_result": result.js_result,
                    "network_count": len(result.network_requests) if result.network_requests else 0
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }

async def main():
    print("=" * 70)
    print("抖音高级爬取工具")
    print("=" * 70)
    
    url = input("\n请输入抖音链接: ").strip()
    
    if not url:
        print("请输入有效的链接！")
        return
    
    print("\n选择爬取模式:")
    print("1. 基础模式 (快速)")
    print("2. 高级模式 (网络请求捕获)")
    mode = input("\n请选择模式 (1 或 2, 默认 1): ").strip() or "1"
    
    scraper = AdvancedTikTokScraper(headless=False, use_undetected=True)
    
    if mode == "2":
        print("\n🚀 使用高级模式 (网络请求捕获)...")
        result = await scraper.scrape_with_network_capture(url)
    else:
        print("\n🚀 使用基础模式...")
        result = await scraper.scrape(url)
    
    if result["success"]:
        print("\n✅ 爬取成功！\n")
        
        if mode == "2" and "media_requests" in result:
            media_requests = result["media_requests"]
            print(f"📡 捕获到 {len(media_requests)} 个媒体请求\n")
            
            videos = [m for m in media_requests if m["type"] == "video"]
            images = [m for m in media_requests if m["type"] == "image"]
            
            if videos:
                print("📹 视频资源:")
                for i, v in enumerate(videos[:5], 1):
                    print(f"  {i}. {v['url']}")
                if len(videos) > 5:
                    print(f"  ... 还有 {len(videos) - 5} 个视频\n")
            
            if images:
                print("🖼️ 图片资源:")
                for i, img in enumerate(images[:5], 1):
                    print(f"  {i}. {img['url']}")
                if len(images) > 5:
                    print(f"  ... 还有 {len(images) - 5} 张图片\n")
        else:
            media = result.get("media")
            if media:
                videos = media.get("videos", [])
                images = media.get("images", [])
                print(f"📹 找到 {len(videos)} 个视频")
                print(f"🖼️ 找到 {len(images)} 张图片\n")
                
                if videos:
                    print("视频:")
                    for v in videos[:3]:
                        print(f"  - {v.get('src')}")
                
                if images:
                    print("\n图片 (前 5 个):")
                    for img in images[:5]:
                        print(f"  - {img.get('src')}")
        
        print("\n" + "=" * 70)
        print("⚠️ 重要提示:")
        print("1. 抖音有严格的反爬机制，可能需要多次尝试")
        print("2. 建议使用真实的用户代理和合理的请求间隔")
        print("3. 请遵守抖音的使用条款和 robots.txt")
        print("4. 仅用于学习和研究目的")
        print("=" * 70)
        
        save_file = input("\n是否保存结果到文件? (y/n, 默认 n): ").strip().lower()
        if save_file == "y":
            filename = f"tiktok_result_{asyncio.get_event_loop().time()}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {filename}")
    else:
        print(f"\n❌ 爬取失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
