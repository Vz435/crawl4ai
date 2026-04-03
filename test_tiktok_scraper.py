import asyncio
import os
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

async def test_tiktok_scraper(url: str):
    print("=" * 70)
    print("抖音测试爬取工具")
    print("=" * 70)
    print(f"正在爬取链接: {url}")
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        browser_type="undetected",
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
        user_data_dir=None,
        use_persistent_context=False,
    )
    
    js_code = '''
    (async () => {
        console.log('开始等待页面加载...');
        
        await new Promise(resolve => {
            let loadAttempts = 0;
            const maxLoadAttempts = 60;
            
            const checkLoadStatus = () => {
                loadAttempts++;
                if (document.readyState === 'complete') {
                    console.log('页面完全加载完成');
                    resolve();
                } else if (loadAttempts >= maxLoadAttempts) {
                    console.log('页面加载超时，继续执行');
                    resolve();
                } else {
                    setTimeout(checkLoadStatus, 500);
                }
            };
            
            checkLoadStatus();
        });
        
        console.log('页面加载完成，开始处理登录窗口...');
        
        const closeLoginModal = () => {
            const closeButtons = [
                '.login-modal .close',
                '.modal-close',
                '.close-btn',
                '.x-button',
                '[aria-label="关闭"]',
                '[aria-label="Close"]',
                '.popup-close',
                '.dialog-close',
                '.login-dialog .close',
                '.modal__close',
                '.modal-close-btn',
                '.close-icon',
                '.icon-close',
                '.login-pop .close',
                '.dy-modal .close',
                '#login-modal .close',
                '.login-overlay .close'
            ];
            
            for (const selector of closeButtons) {
                const button = document.querySelector(selector);
                if (button) {
                    console.log('找到登录窗口关闭按钮，点击...');
                    button.click();
                    return true;
                }
            }
            
            const modalBackdrops = [
                '.modal-backdrop',
                '.login-backdrop',
                '.popup-backdrop',
                '.modal-overlay',
                '.login-overlay',
                '.dy-modal__overlay'
            ];
            
            for (const selector of modalBackdrops) {
                const backdrop = document.querySelector(selector);
                if (backdrop) {
                    console.log('点击背景关闭登录窗口...');
                    backdrop.click();
                    return true;
                }
            }
            
            return false;
        };
        
        for (let i = 0; i < 5; i++) {
            if (closeLoginModal()) {
                await new Promise(resolve => setTimeout(resolve, 1500));
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 800));
        }
        
        console.log('开始等待关键元素...');
        
        await new Promise(resolve => {
            let attempts = 0;
            const maxAttempts = 40;
            
            const checkElements = () => {
                attempts++;
                
                const videos = document.querySelectorAll('video');
                const validVideos = Array.from(videos).filter(video => {
                    const src = video.src || video.currentSrc;
                    const poster = video.poster || '';
                    const videoWidth = video.videoWidth || 0;
                    const videoHeight = video.videoHeight || 0;
                    return src && 
                           !src.includes('loading') && 
                           !poster.includes('loading') &&
                           (videoWidth > 0 || videoHeight > 0);
                });
                
                const images = document.querySelectorAll('img');
                const validImages = Array.from(images).filter(img => {
                    const src = img.src || '';
                    const alt = img.alt || '';
                    const width = img.naturalWidth || 0;
                    const height = img.naturalHeight || 0;
                    return src && 
                           !src.includes('loading') && 
                           !alt.includes('加载') && 
                           !alt.includes('loading') &&
                           (width > 100 || height > 100);
                });
                
                const contentElements = document.querySelectorAll('.video-container, .post-content, .content, .video-player, .video-feed, .item-video, .aweme-list, .tiktok-verse, .video-item');
                
                const hasValidVideos = validVideos.length > 0;
                const hasValidImages = validImages.length > 0;
                const hasContent = contentElements.length > 0;
                
                console.log(`尝试 ${attempts}: 有效视频=${hasValidVideos}, 有效图片=${hasValidImages}, 内容元素=${hasContent}`);
                
                if (hasValidVideos || hasValidImages || hasContent || attempts >= maxAttempts) {
                    console.log(`等待完成: 有效视频=${hasValidVideos}, 有效图片=${hasValidImages}, 内容=${hasContent}, 尝试=${attempts}`);
                    resolve();
                } else {
                    setTimeout(checkElements, 1000);
                }
            };
            
            checkElements();
        });
        
        console.log('开始滚动页面...');
        
        for (let i = 0; i < 5; i++) {
            window.scrollBy(0, 800);
            await new Promise(resolve => setTimeout(resolve, 1200));
        }
        window.scrollTo(0, 0);
        
        closeLoginModal();
        await new Promise(resolve => setTimeout(resolve, 800));
        
        console.log('开始提取数据...');
        
        const videos = document.querySelectorAll('video');
        const validVideos = Array.from(videos).filter(video => {
            const src = video.src || video.currentSrc;
            const poster = video.poster || '';
            return src && !src.includes('loading') && !poster.includes('loading');
        }).map(v => v.src || v.currentSrc);
        
        const images = document.querySelectorAll('img');
        const validImages = Array.from(images).filter(img => {
            const src = img.src || '';
            const alt = img.alt || '';
            return src && !src.includes('loading') && !alt.includes('加载') && !alt.includes('loading');
        }).map(i => i.src);
        
        return {
            videos: validVideos,
            images: validImages,
            pageTitle: document.title,
            pageUrl: window.location.href
        };
    })();
    '''
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            capture_network_requests=True,
            js_code=[js_code],
        )
        
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success:
            print("\n✅ 爬取成功！\n")
            
            media = getattr(result, 'js_result', None)
            video_urls = []
            image_urls = []
            
            if media:
                video_urls = list(dict.fromkeys(media.get('videos', [])))
                image_urls = list(dict.fromkeys(media.get('images', [])))
            
            if result.network_requests:
                for req in result.network_requests:
                    req_url = req.get('url', '')
                    url_lower = req_url.lower()
                    if 'loading' in url_lower:
                        continue
                    if any(ext in url_lower for ext in ['.mp4', '.webm', '.m3u8', '.ts']):
                        if req_url not in video_urls:
                            video_urls.append(req_url)
                    elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        if req_url not in image_urls:
                            image_urls.append(req_url)
            
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
            
            if video_urls or image_urls:
                download_choice = input("\n是否下载视频? (y/n, 默认 y): ").strip().lower() or "y"
                if download_choice == "y" and video_urls:
                    downloader = MediaDownloader()
                    print(f"\n📥 开始下载 {len(video_urls)} 个视频...")
                    
                    for i, video_url in enumerate(video_urls):
                        print(f"  正在下载 {i+1}/{len(video_urls)}...")
                        result = await downloader.download_file(video_url, "video")
                        if result["success"]:
                            status = "✓" if not result.get("skipped") else "○"
                            print(f"  {status} {os.path.basename(result['path'])} - {result.get('message', '')}")
                        else:
                            print(f"  ✗ 下载失败: {result.get('error', '未知错误')}")
                    
                    print(f"\n✅ 下载完成！文件已保存到: {downloader.output_dir}")
        else:
            print(f"\n❌ 爬取失败: {result.error_message}")

if __name__ == "__main__":
    test_url = "https://v.douyin.com/Rqj_efdaTVc/"
    asyncio.run(test_tiktok_scraper(test_url))

