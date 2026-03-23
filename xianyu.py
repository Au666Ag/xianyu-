import time
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_credentials():
    """在控制台获取用户名和密码"""
    print("\n" + "=" * 50)
    print("请输入闲鱼登录信息")
    print("=" * 50)

    username = input("闲鱼账号: ").strip()
    password = input("登录密码: ").strip()

    print("=" * 50 + "\n")

    return username, password


def save_cookies(driver, filename="xianyu_cookies.json"):
    """保存cookies到文件"""
    cookies = driver.get_cookies()
    clean_cookies = []
    for cookie in cookies:
        clean_cookie = {
            'name': cookie.get('name'),
            'value': cookie.get('value'),
            'path': cookie.get('path', '/'),
        }
        if cookie.get('domain'):
            domain = cookie.get('domain')
            if domain.startswith('.'):
                domain = domain[1:]
            clean_cookie['domain'] = domain
        clean_cookies.append(clean_cookie)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(clean_cookies, f, ensure_ascii=False, indent=2)
    print(f"Cookies已保存到 {filename}")


def load_cookies(driver, filename="xianyu_cookies.json"):
    """从文件加载cookies"""
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cookies = json.load(f)

        # 先访问闲鱼，建立会话
        driver.get("https://www.goofish.com")
        time.sleep(3)

        for cookie in cookies:
            try:
                if 'domain' not in cookie or not cookie['domain']:
                    cookie['domain'] = '.goofish.com'
                if 'path' not in cookie:
                    cookie['path'] = '/'
                driver.add_cookie(cookie)
            except Exception as e:
                continue

        driver.refresh()
        time.sleep(3)
        return True

    except Exception as e:
        print(f"加载cookies失败: {e}")
        return False


def is_logged_in(driver):
    """检查是否已登录闲鱼"""
    current_url = driver.current_url

    # 如果还在登录页面，说明未登录
    if "login" in current_url:
        return False

    # 检查是否有用户信息元素
    try:
        user_selectors = [
            ".user-info",
            ".avatar",
            ".nickname",
            "[class*='user']",
            "[class*='avatar']"
        ]

        for selector in user_selectors:
            user_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if user_elements and user_elements[0].is_displayed():
                return True

        # 检查页面中是否包含"我的闲鱼"等登录成功标志
        if "我的闲鱼" in driver.page_source or "个人中心" in driver.page_source:
            return True

    except:
        pass

    return False


def login_with_cookies(driver, cookies_file="xianyu_cookies.json"):
    """尝试使用cookies登录"""
    print("尝试使用cookies登录...")

    if load_cookies(driver, cookies_file):
        if is_logged_in(driver):
            print("使用cookies登录成功！")
            return True
        else:
            print("Cookies已过期，需要重新登录")
            return False

    return False


def manual_login(driver, cookies_file="xianyu_cookies.json"):
    """手动登录并保存cookies"""
    print("\n" + "=" * 50)
    print("开始手动登录流程...")
    print("=" * 50)

    # 直接打开淘宝登录页面（闲鱼使用淘宝登录）
    driver.get('https://login.taobao.com/')
    time.sleep(3)

    try:
        # 尝试切换到密码登录
        try:
            password_login_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '密码登录')]"))
            )
            password_login_btn.click()
            time.sleep(1)
            print("已切换到密码登录模式")
        except:
            print("未找到密码登录按钮，可能已在密码登录页面")

        # 获取账号密码
        username, password = get_credentials()

        if not username or not password:
            print("账号或密码不能为空，程序退出")
            return False

        # 输入账号
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "fm-login-id"))
        )
        username_input.clear()
        username_input.send_keys(username)
        print("账号已输入")

        # 输入密码
        password_input = driver.find_element(By.ID, "fm-login-password")
        password_input.clear()
        password_input.send_keys(password)
        print("密码已输入")

        # 点击登录按钮
        login_button = driver.find_element(By.CLASS_NAME, "fm-button")
        login_button.click()
        print("已点击登录按钮")

        print("登录请求已提交，等待登录结果...")

        # 等待登录完成，最多等待60秒
        for i in range(60):
            time.sleep(1)
            current_url = driver.current_url
            # 如果跳转到淘宝首页或闲鱼，说明登录成功
            if "taobao.com" in current_url and "login" not in current_url:
                break
            if i % 10 == 0 and i > 0:
                print(f"等待登录中... 已等待 {i} 秒")

        time.sleep(3)

        # 检查是否登录成功
        if "login" not in driver.current_url:
            print("登录成功！")
            # 访问闲鱼首页
            driver.get("https://www.goofish.com")
            time.sleep(2)
            save_cookies(driver, cookies_file)
            return True
        else:
            print("可能需要手动处理验证码，你有30秒时间...")
            input("请手动完成验证码后，按回车键继续...")

            # 再次检查
            if "login" not in driver.current_url:
                print("手动验证后登录成功！")
                driver.get("https://www.goofish.com")
                time.sleep(2)
                save_cookies(driver, cookies_file)
                return True
            else:
                print("登录失败")
                return False

    except Exception as e:
        print(f"登录过程发生错误: {e}")
        return False


def setup_driver():
    """配置并返回driver对象"""
    options = Options()

    # 解决SSL错误的配置
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--disable-web-security')

    # 反检测设置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 用户代理
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 窗口大小
    options.add_argument('--window-size=1200,800')

    # 禁用GPU加速
    options.add_argument('--disable-gpu')

    # 禁用沙箱
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = webdriver.Chrome(options=options)
        print("成功启动 Chrome 浏览器")

        # 执行JavaScript来隐藏webdriver属性
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    except Exception as e:
        print(f"启动 Chrome 失败: {e}")
        print("\n请确保 ChromeDriver 已正确安装")
        exit(1)


def crawl_data(driver):
    """
    搜索商品并爬取指定页数的商品名称、价格和地址
    """
    print("\n" + "=" * 50)
    print("开始执行爬虫任务...")
    print("=" * 50)

    product_name = input("\n请输入要搜索的商品名称: ").strip()
    if not product_name:
        print("商品名称不能为空，程序退出")
        return None

    # 询问要爬取多少页
    try:
        max_pages = int(input("请输入要爬取的页数 (默认1页，最多5页): ").strip() or "1")
        max_pages = min(max_pages, 5)
        print(f"将爬取前 {max_pages} 页的商品数据\n")
    except:
        max_pages = 1
        print("输入无效，将只爬取第1页\n")

    from urllib.parse import quote
    all_products = []
    current_page = 1

    while current_page <= max_pages:
        print(f"\n{'=' * 50}")
        print(f"正在爬取第 {current_page} 页...")
        print(f"{'=' * 50}")

        # 构建标准闲鱼搜索URL
        base_url = "https://www.goofish.com/search"
        encoded_keyword = quote(product_name)
        params = f"?q={encoded_keyword}&spm=a21ybx.home.searchInput.0"

        search_url = base_url + params

        # 设置正确的Referer和Origin
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
            'headers': {
                'Referer': 'https://www.goofish.com/',
                'Origin': 'https://www.goofish.com'
            }
        })

        print(f"访问搜索页面: {search_url}")
        driver.get(search_url)

        # 等待页面加载
        time.sleep(5)

        try:
            print(f"当前页面URL: {driver.current_url}")
            print(f"页面标题: {driver.title}")

            # 滚动页面加载更多内容
            print("\n正在滚动加载商品...")
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # 保存页面源码用于调试
            debug_file = f"debug_xianyu_{product_name}_page{current_page}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"✅ 已保存页面源码到 {debug_file}")

            # 使用您提供的商品项class直接定位所有商品
            item_selector = ".feeds-item-wrap--rGdH_KoF"

            # 等待商品加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, item_selector))
                )
                print(f"✓ 找到商品项容器")
            except:
                print(f"✗ 未找到商品项: {item_selector}")
                break

            # 获取所有商品项
            items = driver.find_elements(By.CSS_SELECTOR, item_selector)
            print(f"📦 找到 {len(items)} 个商品")

            if not items:
                print(f"❌ 未找到商品项")
                break

            page_products = []

            # 遍历每个商品提取信息
            for idx, item in enumerate(items):
                try:
                    product = {
                        "name": "",
                        "price": "",
                        "location": "",  # 地址/位置
                        "link": ""
                    }

                    # 1. 提取商品链接（从商品项本身的href属性）
                    try:
                        # 商品项本身可能包含href
                        link_href = item.get_attribute("href")
                        if link_href:
                            product["link"] = link_href
                        else:
                            # 如果商品项本身没有href，查找内部的a标签
                            link_elem = item.find_element(By.CSS_SELECTOR, "a")
                            product["link"] = link_elem.get_attribute("href")
                    except:
                        # 尝试查找任何a标签
                        try:
                            all_links = item.find_elements(By.TAG_NAME, "a")
                            for link in all_links:
                                href = link.get_attribute("href")
                                if href and ("item" in href or "goofish" in href):
                                    product["link"] = href
                                    break
                        except:
                            product["link"] = ""

                    if not product["link"]:
                        product["link"] = ""

                    # 2. 提取商品名称/简介
                    name_selectors = [
                        ".title",
                        ".name",
                        "[class*='title']",
                        "h3",
                        ".item-title"
                    ]
                    for selector in name_selectors:
                        try:
                            name_elem = item.find_element(By.CSS_SELECTOR, selector)
                            product["name"] = name_elem.text.strip()
                            if product["name"]:
                                break
                        except:
                            continue

                    if not product["name"]:
                        # 尝试获取整个item的文本第一行
                        item_text = item.text.strip()
                        if item_text:
                            product["name"] = item_text.split('\n')[0]

                    if not product["name"] or len(product["name"]) < 2:
                        continue

                    # 3. 提取商品价格
                    price_selectors = [
                        ".price",
                        "[class*='price']",
                        ".amount",
                        ".money",
                        "[class*='Price']"
                    ]
                    for selector in price_selectors:
                        try:
                            price_elem = item.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text:
                                # 提取数字价格
                                price_match = re.search(r'¥?\s*(\d+\.?\d*)', price_text)
                                if price_match:
                                    product["price"] = f"¥{price_match.group(1)}"
                                else:
                                    product["price"] = price_text
                                break
                        except:
                            continue

                    if not product["price"]:
                        # 从整个文本中查找价格
                        item_text = item.text
                        price_match = re.search(r'¥\s*(\d+\.?\d*)', item_text)
                        if price_match:
                            product["price"] = f"¥{price_match.group(1)}"
                        else:
                            product["price"] = "价格未找到"

                    # 4. 提取商品位置/地址（使用您提供的class）
                    try:
                        # 在item中查找地址元素
                        location_elem = item.find_element(By.CSS_SELECTOR, ".row4-wrap-seller--E0pIfXoF")
                        product["location"] = location_elem.text.strip()
                        if product["location"]:
                            # 清理地址文本，去除多余空格和换行
                            product["location"] = ' '.join(product["location"].split())
                    except:
                        # 如果找不到，尝试其他可能的选择器
                        location_selectors = [
                            "[class*='location']",
                            "[class*='address']",
                            "[class*='seller']",
                            ".user-location"
                        ]
                        for selector in location_selectors:
                            try:
                                location_elem = item.find_element(By.CSS_SELECTOR, selector)
                                product["location"] = location_elem.text.strip()
                                if product["location"]:
                                    product["location"] = ' '.join(product["location"].split())
                                    break
                            except:
                                continue

                    if not product["location"]:
                        product["location"] = ""

                    page_products.append(product)

                    # 控制台输出前10个商品
                    if len(page_products) <= 10:
                        print(f"\n  [{len(page_products)}] {product['name'][:60]}")
                        print(f"      价格: {product['price']}")
                        if product['location']:
                            print(f"      位置: {product['location']}")
                        if product['link']:
                            print(f"      链接: {product['link'][:80]}")
                        print()

                except Exception as e:
                    print(f"  处理第 {idx + 1} 个商品时出错: {e}")
                    continue

            # 本页统计
            print(f"\n📊 第 {current_page} 页统计:")
            print(f"   - 找到商品: {len(items)}")
            print(f"   - 成功爬取: {len(page_products)}")

            # 统计有链接的商品
            with_link = sum(1 for p in page_products if p.get('link'))
            with_location = sum(1 for p in page_products if p.get('location'))
            print(f"   - 包含链接: {with_link}")
            print(f"   - 包含位置信息: {with_location}")

            all_products.extend(page_products)

            # 检查是否有更多内容（通过页面高度判断）
            if current_page < max_pages:
                old_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")

                if new_height == old_height:
                    print("\n⚠️ 页面高度未增加，可能没有更多商品了")
                    break

            current_page += 1

        except Exception as e:
            print(f"第 {current_page} 页搜索过程出错: {e}")
            import traceback
            traceback.print_exc()
            break

    # 保存结果
    if all_products:
        # 保存JSON文件
        json_file = f"xianyu_{product_name}_全部{len(all_products)}个商品.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        # 保存CSV文件
        csv_file = f"xianyu_{product_name}_全部{len(all_products)}个商品.csv"
        with open(csv_file, 'w', encoding='utf-8-sig') as f:
            f.write("商品名称,价格,位置,链接\n")
            for p in all_products:
                name = p['name'].replace(',', '，').replace('\n', ' ').replace('"', '')
                location = p.get('location', '').replace(',', '，')
                f.write(f"{name},{p['price']},{location},{p.get('link', '')}\n")

        print("\n" + "=" * 60)
        print(f"📊 总体统计:")
        print(f"   - 爬取页数: {current_page - 1}")
        print(f"   - 成功爬取商品总数: {len(all_products)}")

        with_link_count = sum(1 for p in all_products if p.get('link'))
        with_location_count = sum(1 for p in all_products if p.get('location'))
        print(f"   - 包含链接: {with_link_count}")
        print(f"   - 包含位置信息: {with_location_count}")

        print(f"\n✅ 结果已保存到:")
        print(f"   - {json_file}")
        print(f"   - {csv_file}")
        print("=" * 60)

        # 显示前5个商品示例
        print("\n📋 商品示例（前5个）:")
        print("-" * 60)
        for i, p in enumerate(all_products[:5]):
            print(f"{i + 1}. {p['name']}")
            print(f"   价格: {p['price']}")
            if p.get('location'):
                print(f"   位置: {p['location']}")
            if p.get('link'):
                print(f"   链接: {p['link']}")
            print()
    else:
        print("❌ 未提取到任何商品信息")

    return all_products

def main():
    """主函数"""
    print("=" * 60)
    print("闲鱼商品爬虫程序")
    print("=" * 60)

    cookies_file = "xianyu_cookies.json"
    driver = setup_driver()

    try:
        if not login_with_cookies(driver, cookies_file):
            print("\n开始手动登录...")
            if not manual_login(driver, cookies_file):
                print("登录失败，程序退出")
                return

        print("\n登录成功！开始爬虫任务...")

        while True:
            crawl_data(driver)
            choice = input("\n是否继续搜索其他商品？(y/n): ").strip().lower()
            if choice != 'y':
                break

    except KeyboardInterrupt:
        print("\n\n用户中断程序")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()
        print("程序结束")


if __name__ == "__main__":
    main()