## 1：定位
最近又开始了爬虫，写爬虫很快乐，但是有验证码就不快乐了。一个很有名的验证服务商就是Cloudflare，简称cf盾，又叫五秒盾
最开始的时候，我尝试不知死活的去逆向一下js，一天过去，一点进展都没有，这条路还是太难了。
第二天，我打算用DrissionPage来进行过这个五秒盾。这个库文档都写的很全，马上就上手了，我就着手准备去过盾了。
既然要过盾那么肯定要先定位到盾在哪里吧？审查元素了半天，发现TM的根本就定位不到，什么Div啥的根本就定位不到，我日啊。不过功夫不负有心人，网上有现成的。
``` def cf_click(page):
    challengeSolution = page.ele("@name=cf-turnstile-response")
    challengeWrapper = challengeSolution.parent()
    challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
    challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
    challengeButton = challengeIframeBody.ele("tag:input")
    challengeButton.click()
```
## 2：点击
定位到了是吧？那我是不是可以开始点击了，欸你猜怎么着？虽然点击了，但是根本过不去
回到五秒盾上，既然自动点击不成，那我模拟鼠标不久好了，，我用pyautogui来模拟鼠标，定位盾的那个box框框上，我点击一下不久好了，事实证明，还真可以啊。最后就变成了这样子，只需要传入x和y就好了，其他的交给天意！
``` def human_like_mouse_click(
    target_x, target_y, control_points=1, steps=50, base_duration=0.00001
):
    """
    模拟人类鼠标移动并点击指定位置

    参数:
        target_x: 目标x坐标
        target_y: 目标y坐标
        control_points: 贝塞尔曲线控制点数量
        steps: 移动路径点数
        base_duration: 基础移动时间
    """
    # 获取当前鼠标位置
    current_x, current_y = pyautogui.position()
    print(f"当前鼠标位置: {current_x}, {current_y}")
    print(f"目标位置: {target_x}, {target_y}")

    def generate_bezier_points(start_x, start_y, end_x, end_y, control_points=2):
        points = []
        # 生成控制点
        control_x = [start_x]
        control_y = [start_y]
        for i in range(control_points):
            # 在起点和终点之间随机生成控制点
            control_x.append(
                start_x
                + (end_x - start_x) * (i + 1) / (control_points + 1)
                + random.randint(-100, 100)
            )
            control_y.append(
                start_y
                + (end_y - start_y) * (i + 1) / (control_points + 1)
                + random.randint(-100, 100)
            )
        control_x.append(end_x)
        control_y.append(end_y)

        # 生成贝塞尔曲线上的点
        for t in range(steps + 1):
            t = t / steps
            x = y = 0
            n = len(control_x) - 1
            for i in range(n + 1):
                binomial = math.comb(n, i)
                x += binomial * (1 - t) ** (n - i) * t**i * control_x[i]
                y += binomial * (1 - t) ** (n - i) * t**i * control_y[i]
            points.append((x, y))
        return points

    # 生成路径点
    path_points = generate_bezier_points(current_x, current_y, target_x, target_y)

    # 计算总距离
    total_distance = math.sqrt(
        (target_x - current_x) ** 2 + (target_y - current_y) ** 2
    )
    # 根据距离调整移动速度
    duration = min(0.001, base_duration * (total_distance / 1000))

    # 沿着路径移动鼠标
    for point in path_points:
        # 添加更小的随机偏移，使移动更平滑
        offset_x = random.uniform(-1, 1)
        offset_y = random.uniform(-1, 1)
        pyautogui.moveTo(point[0] + offset_x, point[1] + offset_y, duration=duration)

    # 短暂等待以确保窗口准备就绪
    time.sleep(0.5)

    # 点击
    pyautogui.click()

    # 短暂等待以确保点击完成
    time.sleep(0.1)

    # 将鼠标移回初始位置
    pyautogui.moveTo(current_x, current_y, duration=base_duration)
```
唯一美中不足的就是浏览器需要在前台，不然点击不到框框啊
### 2.1：
很快啊，我又找到了一个神奇的玩意，靠他我居然可以自动点击，而不用去操纵鼠标
[githuh仓库](https://github.com/ObjectAscended/CDP-bug-MouseEvent-.screenX-.screenY-patcher)
https://github.com/ObjectAscended/CDP-bug-MouseEvent-.screenX-.screenY-patcher
通过它我成功的去点击了五秒盾，并且成功的过去了

回到开头的那个函数，咱们将它恢复原样。欸，可以了，五秒盾还拦得住我吗？区区小盾，不过如此
```
def getTurnstileToken():
    page.run_js("try { turnstile.reset() } catch(e) { }")

    turnstileResponse = None

    for i in range(0, 5):
        try:
            turnstileResponse = page.run_js(
                "try { return turnstile.getResponse() } catch(e) { return null }"
            )
            if turnstileResponse:
                return turnstileResponse

            challengeSolution = page.ele("@name=cf-turnstile-response")
            challengeWrapper = challengeSolution.parent()
            challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
            challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
            challengeButton = challengeIframeBody.ele("tag:input")
            challengeButton.click()
        except:
            pass
        time.sleep(1)
```
