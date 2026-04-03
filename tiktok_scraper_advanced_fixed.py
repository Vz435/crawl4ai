import asyncio
import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import httpx

class MediaDownloader:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            desktop = Path.home() / "Desktop"
            output_dir = desktop / "啊哈哈哈哈"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
    
    async def download_file(self, url: str, file_type: str = "video") -> dict:
        try:
            ext = ".mp4" if file_type == "video" else ".jpg"
            parsed = urlparse(url)
            filename = os.path.basename(unquote(parsed.path))
            if not filename or '.' not in filename:
                filename = f"media_{hash(url) % 100000}{ext}"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            output_path = self.output_dir / ("videos" if file_type == "video" else "images") / filename
            
            if output_path.exists():
                return {"success": True, "path": str(output_path), "skipped": True}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
                "Accept": "*/*",
            }
            
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = output_path.stat().st_size
                
                return {
                    "success": True,
                    "url": url,
                    "path": str(output_path),
                    "size": file_size,
                    "skipped": False,
                    "message": f"下载成功 ({file_size / 1024:.1f} KB)"
                }
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    async def download_batch(self, urls: list, file_type: str = "video", max_concurrent: int = 3) -> list:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(url):
            async with semaphore:
                result = await self.download_file(url, file_type)
                if result["success"]:
                    status = "✓" if not result.get("skipped") else "○"
                    print(f"  {status} {os.path.basename(result['path'])} - {result.get('message', '')}")
                else:
                    print(f"  ✗ 下载失败: {result.get('error', '未知错误')}")
                return result
        
        tasks = [download_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

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
        
    async def scrape(self, url: str, wait_time: int = 10):
        """爬取抖音内容，支持多种策略"""
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                magic=True,
                word_count_threshold=1,
                js_code=[
                    f"""
                    (async () => {{
                        console.log('开始等待页面加载...');
                        
                        // 等待页面加载完成
                        await new Promise(resolve => {
                            if (document.readyState === 'complete') {
                                resolve();
                            } else {
                                window.addEventListener('load', resolve);
                                setTimeout(resolve, 15000); // 15秒超时
                            }
                        });
                        
                        console.log('页面加载完成，开始等待关键元素...');
                        
                        // 等待视频或图片元素出现
                        await new Promise(resolve => {
                            let attempts = 0;
                            const maxAttempts = 20;
                            
                            const checkElements = () => {
                                attempts++;
                                const hasVideos = document.querySelector('video') !== null;
                                const hasImages = document.querySelector('img') !== null;
                                const hasContent = document.querySelector('.video-container, .post-content, .content') !== null;
                                
                                if (hasVideos || hasImages || hasContent || attempts >= maxAttempts) {
                                    console.log(`等待完成: 视频=${hasVideos}, 图片=${hasImages}, 内容=${hasContent}, 尝试=${attempts}`);
                                    resolve();
                                } else {
                                    setTimeout(checkElements, 500);
                                }
                            };
                            
                            checkElements();
                        });
                        
                        console.log('关键元素出现，开始等待网络稳定...');
                        
                        // 等待网络请求稳定
                        let lastNetworkActivity = Date.now();
                        await new Promise(resolve => {
                            const checkNetwork = () => {
                                const now = Date.now();
                                if (now - lastNetworkActivity > 2000) {
                                    console.log('网络请求稳定');
                                    resolve();
                                } else {
                                    setTimeout(checkNetwork, 500);
                                }
                            };
                            
                            // 监听网络请求
                            const originalFetch = window.fetch;
                            window.fetch = async (...args) => {
                                lastNetworkActivity = Date.now();
                                return originalFetch.apply(this, args);
                            };
                            
                            const originalXHR = XMLHttpRequest;
                            XMLHttpRequest.prototype.send = function(...args) {
                                lastNetworkActivity = Date.now();
                                return originalXHR.prototype.send.apply(this, args);
                            };
                            
                            setTimeout(checkNetwork, 1000);
                        });
                        
                        console.log('网络稳定，开始提取数据...');
                        
                        // 模拟用户行为：滚动页面
                        for (let i = 0; i < 3; i++) {
                            window.scrollBy(0, 500);
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                        window.scrollTo(0, 0);
                        
                        const results = {{
                            pageTitle: document.title,
                            pageUrl: window.location.href,
                            videos: [],
                            images: [],
                            pageData: {{}}
                        }};
                        
                        // 提取视频
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
                        
                        // 提取图片
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
                        
                        console.log(`提取完成: 视频=${results.videos.length}, 图片=${results.images.length}`);
                        return results;
                    }})();
                    """
                ],
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if result.success:
                media = getattr(result, 'js_result', None)
                return {
                    "success": True,
                    "url": url,
                    "title": result.metadata.get("title", ""),
                    "markdown": result.markdown,
                    "html_length": len(result.html),
                    "media": media,
                    "links": result.links
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }
    
    async def scrape_with_network_capture(self, url: str, wait_time: int = 12):
        """使用网络请求捕获来寻找媒体资源"""
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                magic=True,
                capture_network_requests=True,
                js_code=[
                    f"""
                    (async () => {{
                        console.log('开始等待页面加载...');
                        
                        // 等待页面加载完成
                        await new Promise(resolve => {
                            if (document.readyState === 'complete') {
                                resolve();
                            } else {
                                window.addEventListener('load', resolve);
                                setTimeout(resolve, 20000); // 20秒超时
                            }
                        });
                        
                        console.log('页面加载完成，开始等待关键元素...');
                        
                        // 等待视频或图片元素出现
                        await new Promise(resolve => {
                            let attempts = 0;
                            const maxAttempts = 30;
                            
                            const checkElements = () => {
                                attempts++;
                                const hasVideos = document.querySelector('video') !== null;
                                const hasImages = document.querySelector('img') !== null;
                                const hasContent = document.querySelector('.video-container, .post-content, .content, .video-player') !== null;
                                
                                if (hasVideos || hasImages || hasContent || attempts >= maxAttempts) {
                                    console.log(`等待完成: 视频=${hasVideos}, 图片=${hasImages}, 内容=${hasContent}, 尝试=${attempts}`);
                                    resolve();
                                } else {
                                    setTimeout(checkElements, 500);
                                }
                            };
                            
                            checkElements();
                        });
                        
                        console.log('关键元素出现，开始等待网络稳定...');
                        
                        // 等待网络请求稳定
                        let lastNetworkActivity = Date.now();
                        await new Promise(resolve => {
                            const checkNetwork = () => {
                                const now = Date.now();
                                if (now - lastNetworkActivity > 3000) {
                                    console.log('网络请求稳定');
                                    resolve();
                                } else {
                                    setTimeout(checkNetwork, 500);
                                }
                            };
                            
                            // 监听网络请求
                            const originalFetch = window.fetch;
                            window.fetch = async (...args) => {
                                lastNetworkActivity = Date.now();
                                return originalFetch.apply(this, args);
                            };
                            
                            const originalXHR = XMLHttpRequest;
                            XMLHttpRequest.prototype.send = function(...args) {
                                lastNetworkActivity = Date.now();
                                return originalXHR.prototype.send.apply(this, args);
                            };
                            
                            setTimeout(checkNetwork, 1000);
                        });
                        
                        console.log('网络稳定，开始滚动页面...');
                        
                        // 模拟用户滚动
                        const scrollInterval = setInterval(() => {
                            window.scrollBy(0, 600);
                        }, 600);
                        
                        await new Promise(resolve => setTimeout(resolve, 5000));
                        clearInterval(scrollInterval);
                        window.scrollTo(0, 0);
                        
                        console.log('滚动完成，提取数据...');
                        
                        return {{
                            videos: Array.from(document.querySelectorAll('video')).map(v => v.src || v.currentSrc),
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
                        req_url = req.get('url', '')
                        url_lower = req_url.lower()
                        if any(ext in url_lower for ext in ['.mp4', '.webm', '.m3u8', '.ts', '.mp3', '.flv']):
                            media_requests.append({
                                'type': 'video',
                                'url': req_url,
                                'method': req.get('method')
                            })
                        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                            media_requests.append({
                                'type': 'image',
                                'url': req_url,
                                'method': req.get('method')
                            })
                
                return {
                    "success": True,
                    "media_requests": media_requests,
                    "js_result": getattr(result, 'js_result', None),
                    "network_count": len(result.network_requests) if result.network_requests else 0
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }

def extract_media_urls(result: dict, mode: str) -> tuple:
    """从结果中提取视频和图片 URL"""
    video_urls = []
    image_urls = []
    
    if mode == "2" and "media_requests" in result:
        for item in result["media_requests"]:
            if item["type"] == "video" and item.get("url"):
                video_urls.append(item["url"])
            elif item["type"] == "image" and item.get("url"):
                image_urls.append(item["url"])
    else:
        media = result.get("media")
        if media:
            for video in media.get("videos", []):
                if isinstance(video, dict):
                    src = video.get("src") or video.get("currentSrc")
                    if src:
                        video_urls.append(src)
                    for s in video.get("sources", []):
                        if s and s not in video_urls:
                            video_urls.append(s)
                else:
                    if video:
                        video_urls.append(video)
            
            for image in media.get("images", []):
                if isinstance(image, dict):
                    src = image.get("src")
                    if src:
                        image_urls.append(src)
                else:
                    if image:
                        image_urls.append(image)
    
    video_urls = list(dict.fromkeys(video_urls))
    image_urls = list(dict.fromkeys(image_urls))
    
    return video_urls, image_urls

async def main():
    print("=" * 70)
    print("抖音高级爬取工具 (支持下载)")
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
        print("⏳ 正在等待页面完全加载，请耐心等待...")
        result = await scraper.scrape_with_network_capture(url)
    else:
        print("\n🚀 使用基础模式...")
        print("⏳ 正在等待页面完全加载，请耐心等待...")
        result = await scraper.scrape(url)
    
    if result["success"]:
        print("\n✅ 爬取成功！\n")
        
        video_urls, image_urls = extract_media_urls(result, mode)
        
        print(f"📹 找到 {len(video_urls)} 个视频")
        print(f"🖼️ 找到 {len(image_urls)} 张图片\n")
        
        if video_urls:
            print("视频资源:")
            for i, v in enumerate(video_urls[:5], 1):
                print(f"  {i}. {v}")
            if len(video_urls) > 5:
                print(f"  ... 还有 {len(video_urls) - 5} 个视频")
        
        if image_urls:
            print("\n图片资源:")
            for i, img in enumerate(image_urls[:5], 1):
                print(f"  {i}. {img}")
            if len(image_urls) > 5:
                print(f"  ... 还有 {len(image_urls) - 5} 张图片")
        
        print("\n" + "=" * 70)
        
        if video_urls or image_urls:
            print("\n📥 下载选项:")
            print("1. 下载所有视频")
            print("2. 下载所有图片")
            print("3. 下载全部 (视频 + 图片)")
            print("4. 仅保存链接到文件")
            print("5. 不下载，退出")
            
            download_choice = input("\n请选择 (1-5, 默认 4): ").strip() or "4"
            
            if download_choice in ["1", "2", "3"]:
                desktop_path = Path.home() / "Desktop"
                download_dir = desktop_path / "啊哈哈哈哈"
                downloader = MediaDownloader(output_dir=str(download_dir))
                
                if download_choice in ["1", "3"] and video_urls:
                    print(f"\n📥 开始下载 {len(video_urls)} 个视频...")
                    await downloader.download_batch(video_urls, "video")
                    print(f"\n✅ 视频下载完成！")
                
                if download_choice in ["2", "3"] and image_urls:
                    print(f"\n📥 开始下载 {len(image_urls)} 张图片...")
                    await downloader.download_batch(image_urls, "image")
                    print(f"\n✅ 图片下载完成！")
                
                print(f"\n📁 所有文件已保存到: 桌面/啊哈哈哈哈/")
                print(f"   - 视频位置: 桌面/啊哈哈哈哈/videos/")
                print(f"   - 图片位置: 桌面/啊哈哈哈哈/images/")
            
            if download_choice == "4" or download_choice in ["1", "2", "3"]:
                save_links = input("\n是否同时保存链接到 JSON 文件? (y/n, 默认 y): ").strip().lower() or "y"
                if save_links == "y":
                    output_data = {
                        "url": url,
                        "video_urls": video_urls,
                        "image_urls": image_urls,
                        "result": result
                    }
                    filename = "tiktok_result.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                    print(f"📄 链接已保存到: {filename}")
        
        print("\n" + "=" * 70)
        print("⚠️ 重要提示:")
        print("1. 抖音有严格的反爬机制，可能需要多次尝试")
        print("2. 建议使用真实的用户代理和合理的请求间隔")
        print("3. 请遵守抖音的使用条款和 robots.txt")
        print("4. 仅用于学习和研究目的")
        print("=" * 70)
    else:
        print(f"\n❌ 爬取失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
