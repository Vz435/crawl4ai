# Windows 安装问题修复指南

## 问题分析
您遇到的错误是：
1. `lxml` 包无法编译（缺少 Visual Studio 编译工具）
2. 执行了中文注释（`# 安装浏览器` 被当作命令执行了）

---

## ✅ 解决方案

### 方案一：使用预编译的 wheel 包（推荐）

打开 PowerShell 或 CMD，按顺序执行：

```bash
# 1. 先安装预编译的 lxml
pip install lxml --only-binary :all:

# 2. 然后安装 Crawl4AI
pip install -U crawl4ai

# 3. 最后安装浏览器
crawl4ai-setup
```

---

### 方案二：使用国内镜像 + 预编译包

```bash
# 1. 使用清华镜像，只安装二进制包
pip install lxml --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 安装 Crawl4AI
pip install -U crawl4ai -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 安装浏览器
crawl4ai-setup
```

---

### 方案三：直接安装 Playwright 浏览器（如果上面的方法失败）

```bash
# 1. 先安装 Playwright
pip install playwright

# 2. 安装浏览器
python -m playwright install chromium

# 3. 再安装 Crawl4AI（跳过 lxml 检查）
pip install -U crawl4ai --no-deps
pip install aiofiles aiohttp aiosqlite anyio numpy pillow python-dotenv requests beautifulsoup4 playwright-stealth pydantic PyYAML nltk rich httpx
```

---

### 方案四：下载预编译的 lxml

访问 https://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
下载对应 Python 版本的 `.whl` 文件，然后：

```bash
pip install 下载的文件路径.whl
```

---

## 🚀 安装成功后运行

下载 `tiktok_scraper_advanced.py` 文件到你的电脑，然后：

```bash
python tiktok_scraper_advanced.py
```

---

## ⚠️ 注意事项

1. **不要执行中文注释** - `#` 开头的是注释，不要复制粘贴执行
2. **以管理员身份运行** - 右键 PowerShell 选择"以管理员身份运行"
3. **Python 版本** - 确保使用 Python 3.10 或更高版本

---

## 检查 Python 版本

```bash
python --version
```

应该显示类似 `Python 3.10.x` 或更高
