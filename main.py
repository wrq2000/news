from bs4 import BeautifulSoup
import pandas as pd
import unicodedata
import datetime as dt
import requests
import smtplib
from email import encoders
import mimetypes
from email.mime.base import MIMEBase  
from email.mime.multipart import MIMEMultipart
import lxml
import datetime as dt
from datetime import timedelta
import io

def export_excel(df):
  with io.BytesIO() as buffer:
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer)
    return buffer.getvalue()


# Получение приложений-картинок для письма
def get_attach(df):
    result = []
    file = MIMEBase('application', "octet-stream")
    file.set_payload(export_excel(df))
    encoders.encode_base64(file)      
    file.add_header('Content-Disposition', 'attachment', filename='df.xlsx')
    result.append(file)
    #except:
    #print(f'Что-то не так')

    return result

    


def date_from_unix(d:int):
  return UNIX_EPOCH + dt.timedelta(days= d / 3600 / 24)

news_now_url = "https://www.newsnow.co.uk/h/Industry+Sectors/Energy+&+Utilities/Natural+Gas"
UNIX_EPOCH = dt.datetime(1970, 1, 1)

def handler(event, context):
    # Импорт библиотек
    response = requests.get(news_now_url)
    print('Данные получены')

    news_now_html = response.content

    # Делаем суп для парсинга
    news_now_soup = BeautifulSoup(news_now_html, "html.parser")
    # news_now_soup
    # Вынимаем элементы с названием статей и ссылками  {'class':'item_i'} hl hl_inv
    news_now = news_now_soup.find_all('div', {'class':'hl__inner'})
    nn_table = []
    for i in news_now:
        text = ''
        link = ''
        date = UNIX_EPOCH
        try:
            text = i.find('a', {'class':'hll'}).text
        except:
            pass
        try:
            href = i.find('a', {'class':'hll'}).get('href')
            if href.find('http') == -1:
                continue
            

        except:
            pass
        r = requests.get(href)
        soup = BeautifulSoup(r.text,'lxml')
        link = soup.find('script')
        link = str(link).split('url: \'')
        link = link[1].split('\'')[0]
            

        try:
            date = date_from_unix(int(i.find('span', {'class':'time'}).get('data-time')))
        except:
            pass
        nn_table.append([text, link, date])

    df = pd.DataFrame(nn_table)
    df.sort_values(by=[2], ascending=False, inplace=True)


    d = dt.datetime.now().date() - timedelta(days=1)
    # Создаем сообщение  
    msg = MIMEMultipart()    
    addr_from =      "vologzhaninovas@yandex.ru"                       
    msg['From']    =      addr_from                  
    msg['To']      = "a.vologzhaninov@adm.gazprom.ru; vologzhaninov@gmail.com" 
    password  = "tflqfxqfhsowfose"
    msg['Subject'] = f' {d:%Y.%m.%d}'
    atts = get_attach(df) 
    for i in atts:
        msg.attach(i)                
    server = smtplib.SMTP('smtp.yandex.ru', 587)
    # Начинаем шифрованный обмен по TLS
    server.starttls()        
    # Получаем доступ                           
    server.login(addr_from, password)         
    # Отправляем сообщение          
    server.send_message(msg)                            
    server.quit()
