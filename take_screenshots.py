"""使用 Playwright 对博客各页面进行截图渲染。"""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path("/workspace/screenshots")
OUTPUT_DIR.mkdir(exist_ok=True)

PAGES = [
    # 前台页面
    ("/", "homepage", "首页"),
    ("/archive", "archive", "归档页"),
    ("/timeline", "timeline", "时间轴"),
    ("/links", "links", "友链页"),
    ("/search", "search", "搜索页"),
    ("/article/welcome-to-anncix-blog", "article_detail", "文章详情页"),
    ("/article/fastapi-getting-started", "article_detail2", "文章详情页-FastAPI入门"),
    ("/category/tech", "category", "分类页"),
    ("/tag/python", "tag", "标签页"),
    # 后台页面
    ("/admin/login", "admin_login", "后台登录页"),
]


async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome-stable",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = await context.new_page()

        results = []
        for path, name, desc in PAGES:
            url = BASE_URL + path
            print(f"正在渲染: {desc} ({url})")
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)  # 等待页面完全渲染
                # 全页截图
                screenshot_path = OUTPUT_DIR / f"{name}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                file_size = screenshot_path.stat().st_size
                results.append((name, desc, str(screenshot_path), file_size))
                print(f"  ✓ 已保存: {screenshot_path} ({file_size // 1024}KB)")
            except Exception as e:
                print(f"  ✗ 失败: {e}")

        # 登录后台并截取仪表盘
        print("正在截取后台仪表盘（需要登录）...")
        try:
            await page.goto(BASE_URL + "/admin/login", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(500)
            # 填写登录表单
            await page.fill('input[name="username"]', "admin")
            await page.fill('input[name="password"]', "admin123")
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            screenshot_path = OUTPUT_DIR / "admin_dashboard.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            file_size = screenshot_path.stat().st_size
            results.append(("admin_dashboard", "后台仪表盘", str(screenshot_path), file_size))
            print(f"  ✓ 已保存: {screenshot_path} ({file_size // 1024}KB)")

            # 截取文章管理页
            await page.goto(BASE_URL + "/admin/articles", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            screenshot_path = OUTPUT_DIR / "admin_articles.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            file_size = screenshot_path.stat().st_size
            results.append(("admin_articles", "后台文章管理", str(screenshot_path), file_size))
            print(f"  ✓ 已保存: {screenshot_path} ({file_size // 1024}KB)")

            # 截取评论管理页
            await page.goto(BASE_URL + "/admin/comments", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            screenshot_path = OUTPUT_DIR / "admin_comments.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            file_size = screenshot_path.stat().st_size
            results.append(("admin_comments", "后台评论管理", str(screenshot_path), file_size))
            print(f"  ✓ 已保存: {screenshot_path} ({file_size // 1024}KB)")

            # 截取设置页
            await page.goto(BASE_URL + "/admin/settings", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            screenshot_path = OUTPUT_DIR / "admin_settings.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            file_size = screenshot_path.stat().st_size
            results.append(("admin_settings", "后台站点设置", str(screenshot_path), file_size))
            print(f"  ✓ 已保存: {screenshot_path} ({file_size // 1024}KB)")

        except Exception as e:
            print(f"  ✗ 后台页面截图失败: {e}")

        await browser.close()

        print("\n" + "=" * 60)
        print(f"截图完成！共生成 {len(results)} 张渲染图")
        print(f"保存目录: {OUTPUT_DIR}")
        print("=" * 60)
        for name, desc, path, size in results:
            print(f"  {desc}: {path} ({size // 1024}KB)")


if __name__ == "__main__":
    asyncio.run(take_screenshots())
