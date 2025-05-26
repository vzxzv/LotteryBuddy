import os
import requests
from bs4 import BeautifulSoup
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from lottery_recommendation import generate_numbers, get_recommended_numbers
from email.utils import formataddr
from email.header import Header

def get_lottery_type():
    """判断今日开奖类型"""
    today = datetime.now().weekday()
    print(f"今天是星期{today + 1}")
    if today in [0, 2, 5]:  # 周一、三、六
        print("今天开大乐透")
        return "大乐透"
    else:
        print("今天开双色球")
        return "双色球"

def get_lottery_result(lottery_type):
    """获取开奖结果"""
    try:
        if lottery_type == "大乐透":
            url = "https://datachart.500.com/dlt/history/newinc/history.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        else:
            url = "https://datachart.500.com/ssq/history/newinc/history.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
        print(f"正在获取{lottery_type}开奖结果，URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'  # 500彩票网使用gb2312编码
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        print("成功解析HTML")

        # 查找开奖表格
        tbody = soup.find('tbody', id='tdata')
        if tbody:
            print("找到开奖表格")
            first_tr = tbody.find('tr')
            if first_tr:
                tds = first_tr.find_all('td')
                if len(tds) >= 8:
                    # 第2到8个td（索引1到7）
                    numbers = [td.text.strip() for td in tds[1:8]]
                    print(f"找到开奖号码: {' '.join(numbers)}")
                    return numbers
                else:
                    print("td数量不足，无法提取开奖号码")
                    return None
            else:
                print("未找到第一个tr")
                return None
        else:
            print("未找到id为tdata的tbody")
            return None
                
    except requests.exceptions.Timeout:
        print("请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {str(e)}")
        return None
    except Exception as e:
        print(f"获取开奖结果失败: {str(e)}")
        return None

def check_winning(lottery_type, recommended_numbers, winning_numbers):
    """检查是否中奖"""
    if lottery_type == "大乐透":
        # 解析推荐号码
        recommended = recommended_numbers.replace("前区：", "").replace("后区：", "").split("，")
        front_recommended = [int(n.strip()) for n in recommended[0].split(",")]
        back_recommended = [int(n.strip()) for n in recommended[1].split(",")]
        
        # 解析开奖号码
        front_winning = [int(n) for n in winning_numbers[:5]]
        back_winning = [int(n) for n in winning_numbers[5:]]
        
        # 计算前区匹配数
        front_matches = len(set(front_recommended) & set(front_winning))
        # 计算后区匹配数
        back_matches = len(set(back_recommended) & set(back_winning))
        
        # 判断中奖等级
        if front_matches == 5 and back_matches == 2:
            return "🥳恭喜您中了一等奖！成功实现财富自由！！！🎉"
        elif front_matches == 5 and back_matches == 1:
            return "🥳恭喜您中了二等奖！！！！！！！！！！！！🎉"
        elif front_matches == 5 and back_matches == 0:
            return "🎉恭喜您中了三等奖！奖金为10000元~"
        elif front_matches == 4 and back_matches == 2:
            return "🎉恭喜您中了四等奖！奖金为3000元~"
        elif front_matches == 4 and back_matches == 1:
            return "🎉恭喜您中了五等奖！奖金为300元~"
        elif front_matches == 3 and back_matches == 2:
            return "🎉恭喜您中了六等奖！奖金为200元~"
        elif front_matches == 4 and back_matches == 0:
            return "🎉恭喜您中了七等奖！奖金为100元~"
        elif (front_matches == 3 and back_matches == 1) or (front_matches == 2 and back_matches == 2):
            return "🎉恭喜您中了八等奖！奖金为15元~"
        elif (front_matches == 3 and back_matches == 0) or (front_matches == 1 and back_matches == 2) or (front_matches == 2 and back_matches == 1) or (front_matches == 0 and back_matches == 2):
            return "🎉恭喜您中了九等奖！奖金为5元~"
        else:
            return "很遗憾，您没有中奖。"
    else:
        # 解析推荐号码
        recommended = recommended_numbers.replace("红球：", "").replace("蓝球：", "").split("，")
        red_recommended = [int(n.strip()) for n in recommended[0].split(",")]
        blue_recommended = int(recommended[1].strip())
        
        # 解析开奖号码
        red_winning = [int(n) for n in winning_numbers[:6]]
        blue_winning = int(winning_numbers[6])
        
        # 计算红球匹配数
        red_matches = len(set(red_recommended) & set(red_winning))
        # 计算蓝球是否匹配
        blue_match = blue_recommended == blue_winning
        
        # 判断中奖等级
        if red_matches == 6 and blue_match:
            return "🥳恭喜您中了一等奖！成功实现财富自由！！！🎉"
        elif red_matches == 6 and not blue_match:
            return "🥳恭喜您中了二等奖！！！！！！！！！！！！🎉"
        elif red_matches == 5 and blue_match:
            return "🎉恭喜您中了三等奖！奖金为3000元~"
        elif (red_matches == 5 and not blue_match) or (red_matches == 4 and blue_match):
            return "🎉恭喜您中了四等奖！奖金为200元~"
        elif (red_matches == 4 and not blue_match) or (red_matches == 3 and blue_match):
            return "🎉恭喜您中了五等奖！奖金为10元~"
        elif red_matches == 2 and blue_match or red_matches == 1 and blue_match or red_matches == 0 and blue_match:
            return "🎉恭喜您中了六等奖！奖金为5元~"
        else:
            return "很遗憾，您没有中奖。"

def send_email(subject, content):
    """发送邮件"""
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    msg = MIMEMultipart()
    msg['From'] = formataddr((str(Header('【来彩助手】', 'utf-8')), email_user))
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(content, 'html'))

    try:
        # 使用QQ邮箱的SMTP服务器
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")

def main():
    print("开始执行开奖查询...")
    lottery_type = get_lottery_type()
    
    # 获取今日推荐号码
    recommended_numbers, analysis = get_recommended_numbers(lottery_type)
    
    if recommended_numbers is None:
        print("未找到今日推荐号码，请先运行推荐程序")
        return
    
    print(f"\n今日推荐号码：\n{recommended_numbers}")
    
    # 获取开奖结果
    winning_numbers = get_lottery_result(lottery_type)
    
    if winning_numbers:
        # 检查是否中奖
        result = check_winning(lottery_type, recommended_numbers, winning_numbers)
        
        subject = f"今日{lottery_type}开奖结果：{result}"
        content = f"""<html>
          <head><style>body {{ font-family: Arial, sans-serif; }} .section {{ margin-bottom: 20px; }} .title {{ color: #2c3e50; font-weight: bold; }} .numbers {{ font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px; }} .number-section {{ margin-bottom: 15px; padding: 10px; border: 1px solid #e0e0e0; border-radius: 4px; }} .section-title {{ font-size: 1.1em; color: #34495e; margin-bottom: 8px; font-weight: bold; }} .number-row {{ margin-bottom: 6px; }} .label {{ color: #7f8c8d; margin-right: 8px; }}</style></head>
          <body>
            <div class="section">
              <p class="title">您好！</p>
              <p class="title">今日{lottery_type}开奖结果：</p>
              <div class="numbers">{' '.join(winning_numbers)}</div>
            </div>
            <div class="section">
              <p class="title">您的号码：</p>
              <div class="numbers">{recommended_numbers}</div>
            </div>
            <div class="section">
              <p class="title">号码匹配：</p>
              <div class="numbers">{format_number_comparison(lottery_type, recommended_numbers, winning_numbers)}</div>
            </div>
            <div class="section">
              <p class="title">{result}</p>
            </div>
            <p>祝您早日中奖！实现财富自由~🫵💪👊🫶😁</p>
          </body>
        </html>"""
        print(f"\n今日{lottery_type}开奖结果：")
        print(' '.join(winning_numbers))
        print(f"\n{result}")
        
        # 发送邮件
        send_email(subject, content)
    else:
        print("无法获取开奖结果")

def format_number_comparison(lottery_type, recommended_numbers, winning_numbers):
    """格式化号码匹配信息"""
    if lottery_type == "大乐透":
        # 解析推荐号码
        recommended = recommended_numbers.replace("前区：", "").replace("后区：", "").split("，")
        front_recommended = [int(n.strip()) for n in recommended[0].split(",")]
        back_recommended = [int(n.strip()) for n in recommended[1].split(",")]
        
        # 解析开奖号码
        front_winning = [int(n) for n in winning_numbers[:5]]
        back_winning = [int(n) for n in winning_numbers[5:]]
        
        # 找出匹配的号码
        front_matches = set(front_recommended) & set(front_winning)
        back_matches = set(back_recommended) & set(back_winning)
        
        # 格式化输出
        front_recommended_str = " ".join([f"{n:02d}" for n in front_recommended])
        back_recommended_str = " ".join([f"{n:02d}" for n in back_recommended])
        front_winning_str = " ".join([f"{n:02d}" for n in front_winning])
        back_winning_str = " ".join([f"{n:02d}" for n in back_winning])
        
        return f"""<div class="number-section">
            <div class="section-title">前区匹配</div>
            <div class="number-row"><span class="label">推荐：</span><span class="numbers">{front_recommended_str}</span></div>
            <div class="number-row"><span class="label">开奖：</span><span class="numbers">{front_winning_str}</span></div>
            <div class="number-row"><span class="label">匹配：</span><span class="numbers">{' '.join([f"{n:02d}" for n in front_matches])}（{len(front_matches)}个）</span></div>
        </div>
        <div class="number-section">
            <div class="section-title">后区匹配</div>
            <div class="number-row"><span class="label">推荐：</span><span class="numbers">{back_recommended_str}</span></div>
            <div class="number-row"><span class="label">开奖：</span><span class="numbers">{back_winning_str}</span></div>
            <div class="number-row"><span class="label">匹配：</span><span class="numbers">{' '.join([f"{n:02d}" for n in back_matches])}（{len(back_matches)}个）</span></div>
        </div>"""
    else:
        # 解析推荐号码
        recommended = recommended_numbers.replace("红球：", "").replace("蓝球：", "").split("，")
        red_recommended = [int(n.strip()) for n in recommended[0].split(",")]
        blue_recommended = int(recommended[1].strip())
        
        # 解析开奖号码
        red_winning = [int(n) for n in winning_numbers[:6]]
        blue_winning = int(winning_numbers[6])
        
        # 找出匹配的号码
        red_matches = set(red_recommended) & set(red_winning)
        blue_match = blue_recommended == blue_winning
        
        # 格式化输出
        red_recommended_str = " ".join([f"{n:02d}" for n in red_recommended])
        red_winning_str = " ".join([f"{n:02d}" for n in red_winning])
        
        return f"""<div class="number-section">
            <div class="section-title">红球匹配</div>
            <div class="number-row"><span class="label">推荐：</span><span class="numbers">{red_recommended_str}</span></div>
            <div class="number-row"><span class="label">开奖：</span><span class="numbers">{red_winning_str}</span></div>
            <div class="number-row"><span class="label">匹配：</span><span class="numbers">{' '.join([f"{n:02d}" for n in red_matches])}（{len(red_matches)}个）</span></div>
        </div>
        <div class="number-section">
            <div class="section-title">蓝球匹配</div>
            <div class="number-row"><span class="label">推荐：</span><span class="numbers">{blue_recommended:02d}</span></div>
            <div class="number-row"><span class="label">开奖：</span><span class="numbers">{blue_winning:02d}</span></div>
            <div class="number-row"><span class="label">匹配：</span><span class="numbers">{'是' if blue_match else '否'}</span></div>
        </div>"""

if __name__ == "__main__":
    main()