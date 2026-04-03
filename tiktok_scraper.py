import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class TikTokScraper:
    def __init__(self, headless=True):
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=True,
        )
        
    async def scrape_video(self, url: str, output_dir: str = "./downloads"):
        """爬取抖音视频"""
        os.makedirs(output_dir, exist_ok=True)
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                magic=True,
                js_code=[
                    """
                    (async () => {
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        
                        const videos = Array.from(document.querySelectorAll('video'));
                        const videoSources = videos.map(video => ({
                            src: video.src,
                            poster: video.poster,
                            width: video.videoWidth,
                            height: video.videoHeight
                        }));
                        
                        const images = Array.from(document.querySelectorAll('img'));
                        const imageSources = images.map(img => img.src);
                        
                        return {
                            videos: videoSources,
                            images: imageSources
                        };
                    })();
                    """
                ]
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if result.success:
                print("✓ 页面爬取成功！")
                
                media_data = None
                try:
                    if result.js_result:
                        media_data = result.js_result
                except:
                    pass
                
                if not media_data:
                    print("ℹ️ 尝试从 HTML 中提取媒体资源...")
                    media_data = self._extract_media_from_html(result.html)
                
                return {
                    "success": True,
                    "markdown": result.markdown,
                    "media": media_data,
                    "url": url
                }
            else:
                print("✗ 爬取失败")
                return {
                    "success": False,
                    "error": result.error_message
                }
    
    def _extract_media_from_html(self, html: str):
        """从 HTML 中提取媒体资源"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        videos = []
        for video in soup.find_all('video'):
            video_data = {}
            if video.get('src'):
                video_data['src'] = video['src']
            if video.get('poster'):
                video_data['poster'] = video['poster']
            
            sources = video.find_all('source')
            if sources:
                video_data['sources'] = [s.get('src') for s in sources if s.get('src')]
            
            if video_data:
                videos.append(video_data)
        
        images = []
        for img in soup.find_all('img'):
            if img.get('src'):
                images.append(img['src'])
        
        return {
            "videos": videos,
            "images": images
        }
    
    async def download_file(self, url: str, output_path: str):
        """下载文件"""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path

async def main():
    print("=" * 60)
    print("抖音内容爬取工具")
    print("=" * 60)
    
    url = input("请输入抖音链接 (例如: https://www.douyin.com/video/...): ").strip()
    
    if not url:
        print("✗ 请输入有效的链接！")
        return
    
    scraper = TikTokScraper(headless=False)
    
    print(f"\n正在爬取: {url}")
    print("-" * 60)
    
    result = await scraper.scrape_video(url)
    
    if result["success"]:
        print("\n✓ 爬取完成！")
        
        media = result.get("media", {})
        videos = media.get("videos", [])
        images = media.get("images", [])
        
        print(f"\n📹 找到 {len(videos)} 个视频")
        print(f"🖼️ 找到 {len(images)} 张图片")
        
        if videos:
            print("\n视频资源:")
            for i, video in enumerate(videos, 1):
                print(f"  {i}. {video.get('src', 'N/A')}")
        
        if images:
            print("\n图片资源 (前 10 个):")
            for i, img in enumerate(images[:10], 1):
                print(f"  {i}. {img}")
            if len(images) > 10:
                print(f"  ... 还有 {len(images) - 10} 张图片")
        
        print("\n" + "=" * 60)
        print("提示: 对于抖音这类有严格反爬机制的网站，")
        print("建议:")
        print("1. 使用非 headless 模式（当前已启用）")
        print("2. 考虑使用代理")
        print("3. 注意遵守网站的使用条款")
        print("=" * 60)
    else:
        print(f"\n✗ 爬取失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
