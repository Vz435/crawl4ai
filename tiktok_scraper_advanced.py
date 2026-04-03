import asyncio
import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_configs import ProxyConfig
import httpx

class MediaDownloader:
    def __init__(self, output_dir: str = "./downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
    
    def _sanitize_filename(self, url: str, default_ext: str = ".mp4") -> str:
        """从 URL 生成安全的文件名"""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)
        
        if not filename or '.' not in filename:
            filename = f"media_{hash(url) % 100000}{default_ext}"
        
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    async def download_file(self, url: str, file_type: str = "video") -> dict:
        """下载单个文件"""
        try:
            ext = ".mp4" if file_type == "video" else ".jpg"
            filename = self._sanitize_filename(url, ext)
            
            if file_type == "video":
                output_path = self.output_dir / "videos" / filename
            else:
                output_path = self.output_dir / "images" / filename
            
            if output_path.exists():
                return {
                    "success": True,
                    "url": url,
                    "path": str(output_path),
                    "skipped": True,
                    "message": "文件已存在，跳过下载"
                }
            
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
        """批量下载文件"""
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
                    "js_result": result.js_result,
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
                src = video.get("src") or video.get("currentSrc")
                if src:
                    video_urls.append(src)
                for s in video.get("sources", []):
                    if s and s not in video_urls:
                        video_urls.append(s)
            
            for image in media.get("images", []):
                src = image.get("src")
                if src:
                    image_urls.append(src)
    
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
        result = await scraper.scrape_with_network_capture(url)
    else:
        print("\n🚀 使用基础模式...")
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
                downloader = MediaDownloader(output_dir="./downloads")
                
                if download_choice in ["1", "3"] and video_urls:
                    print(f"\n📥 开始下载 {len(video_urls)} 个视频...")
                    await downloader.download_batch(video_urls, "video")
                    print(f"\n✅ 视频下载完成！保存位置: ./downloads/videos/")
                
                if download_choice in ["2", "3"] and image_urls:
                    print(f"\n📥 开始下载 {len(image_urls)} 张图片...")
                    await downloader.download_batch(image_urls, "image")
                    print(f"\n✅ 图片下载完成！保存位置: ./downloads/images/")
                
                print(f"\n📁 所有文件已保存到: {downloader.output_dir.absolute()}")
            
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
