import time

from bs4 import BeautifulSoup        # 用于解析网页源代码的模块
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('chromedriver', options=chrome_options)

def add_cookie(cookie):
    driver.get("https://music.163.com/")
    driver.delete_all_cookies()
    for cookie_single in cookie:
        driver.add_cookie(cookie_single)
    driver.get("https://music.163.com/")
    print("来自NeteaseMusicCrawler：已初始化")

#不知道有什么用
def quit():
    driver.quit()

def get_userid(username):
    print(f'正在获取用户名id：{username}')
    link = "https://music.163.com/#/search/m/?s=" + username + "&type=1002"
    driver.get(link)
    try:
        WebDriverWait(driver, 3).until(EC.frame_to_be_available_and_switch_to_it("g_iframe"))#定位iframe
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/div[1]')))#
    except:
        print("连接超时呃呃")
        return "超时"
    #time.sleep(0.3)
    soup = BeautifulSoup(driver.page_source, "html.parser")  # 解析网页
    #print(soup.text)
    search_result = soup.find("div",class_='snote s-fc4 ztag').text
    if search_result == "0":
        return None
    first_user = soup.find("tr",class_='h-flag')#提前获取
    name = first_user.find("div",class_='ttc').find('a').get('title')#用户名
    if name == username:#确认用户名相符
        id = first_user.find("div",class_='u-cover u-cover-3').find("a").get("href")[14:]
        print("user_id:",id)
        return id
    else:
        return None

#id+所有时间或者本周+获取歌曲数量
def get_songs(id,type_,number,mod):
    print(f'正在获取用户播放排名：{id}')
    link = "https://music.163.com/#/user/songs/rank?id=" + str(id)
    #print(link)
    driver.get(link)#获取了cookie之后再访问
    try:
        WebDriverWait(driver, 3).until(EC.frame_to_be_available_and_switch_to_it("g_iframe"))#定位iframe
    except:
        print("连接超时呃呃")
        return "超时"
    if(type_ == "所有时间"):
        button = driver.find_element('xpath','//*[@id="songsall"]')
        button.click()
    #print(driver.get_cookie("MUSIC_U"))
    #print(driver.find_element(By.XPATH,"/html/body/div[3]/div/div[2]/div/div[1]/ul/li[1]/div[1]/span[2]"))
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH,"/html/body/div[3]/div/div[2]/div/div[1]/ul/li[1]/div[1]/span[2]")))
    except:
        print("未开启所有人可见")
        return "失败"
    #<div class="u-load s-fc4"><i class="icn"></i> 加载中...</div></div>
    #time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")  # 解析网页
    song_info = {}
    '''例子song_info = {'song_id_list':[],'song_id':{'song_name':'xxx','song_author':'xx'}}'''
    #print(soup.text)
    if mod == "前":
        song_info['song_id_list'] = []
        for i in range(0,number):
            #print(i)
            try:
                song_id = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[i].find('div', class_='ttc').find('a').get('href')[9:]
                song_info['song_id_list'].append(song_id)
                song_info[song_id] = {}
                song_info[song_id]['song_name'] = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[i]\
                    .find('div', class_='ttc').find('b').get('title')
                song_info[song_id]['song_author'] = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[i]\
                    .find('div', class_='ttc').find('span', class_="ar s-fc8").find('span').get('title')
            except:
                if(i == 0):
                    return "超出范围"
                else:
                    break
        return song_info

    if mod == "第":
        try:
            song_info['song_id_list'] = []
            song_id = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[number].find('div', class_='ttc').find('a').get('href')[9:]
            song_info['song_id_list'].append(song_id)
            song_info[song_id] = {}
            song_info[song_id]['song_name'] = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[number]\
                    .find('div', class_='ttc').find('b').get('title')
            song_info[song_id]['song_author'] = soup.find("div", id='m-record').find('div', class_='j-flag').findAll("li")[number]\
                    .find('div', class_='ttc').find('span', class_="ar s-fc8").find('span').get('title')
            return song_info
        except:
            return "超出范围"

def get_search_songs(name):
    print(f'正在搜索歌曲：{name}')
    link = 'https://music.163.com/#/search/m/?s=' + name + '&type=1'
    driver.get(link)
    #搜索~
    try:
        WebDriverWait(driver, 3).until(EC.frame_to_be_available_and_switch_to_it("g_iframe"))#定位iframe
    except:
        print("连接超时呃呃")
        return "超时"
    print('已定位iframe')
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[1]/div')))
    except:
        print("连接超时呃呃")
        #soup = BeautifulSoup(driver.page_source, "html.parser")  # 解析网页
        #print(soup)
        return "超时"
    print('iframe加载完全')
    soup = BeautifulSoup(driver.page_source, "html.parser")  # 解析网页
    print('已解析网页')
    result_number = int(soup.find('div', id="m-search").find('div', class_="snote s-fc4 ztag").find('em', class_="s-fc6").text)
    print('结果数量',result_number)
    if result_number == 0:
        print("未找到结果")
        return "无结果"

    song_info = {}
    song_info['song_id_list'] = []
    '''例子song_info = {'song_id_list':[],'song_id':{'song_name':'xxx','song_author':'xx'}}'''

    len_not_even = len(soup.find('div', class_ ="srchsongst").findAll('div',class_="item f-cb h-flag"))
    len_even = len(soup.find('div', class_ ="srchsongst").findAll('div',class_="item f-cb h-flag even"))
    real_result = len_even + len_not_even

    for i in range(0,15):
        if i == real_result:
            print(f'返回了前{i}个结果')
            return song_info
        #交替搜索even和无even
        if i%2 == 0:
            premake = soup.find('div', class_ ="srchsongst").findAll('div',class_="item f-cb h-flag")[int(i/2)]
        elif i%2 == 1:
            premake = soup.find('div', class_="srchsongst").findAll('div', class_="item f-cb h-flag even")[int(i/2)]

        song_id = premake.find('div', class_='td w0').find('div', class_='text').find('a').get('href')[9:]

        song_info['song_id_list'].append(song_id)
        song_info[song_id] = {}
        song_info[song_id]['song_name'] = premake.find('div', class_='td w0').find('div', class_='text').find('b').get('title')
        song_info[song_id]['song_author'] = premake.find('div', class_='td w1').find('div', class_='text').text
    print(f'返回了前{real_result}个结果')
    return song_info






def main():
    name = input("id:")
    id = get_userid(name)
    if id == None:
        return None
    get_songs(id,"所有时间",66)

    return

if __name__ == '__main__':
    main()