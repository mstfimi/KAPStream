from pprint import pprint
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup
import time
import pytz
from emoji import emojize
from collections import deque
import traceback
import os
import random
import streamlit as st


# Streamlit app header
st.set_page_config(page_title="KAP Bildirimleri", layout="wide")
st.title("Filtrelenmiş en güncel KAP Bildirimleri")
tab1, tab2 = st.tabs(["Bildirimler", "Diğer (Yakında)"])
df_placeholder = st.empty()

# Read the list from the .txt file
with open("istenmeyen_bildirimler.txt", "r", encoding="utf-8") as file:
    istenmeyen_bildirimler = [line.strip() for line in file]


token = "7998489410:AAEsQLVpDc01dmnTaq8zp3_xyGsQH6xHJFs"
chatID = "-1002291391732"
gonderilenBildirimlerFileName = 'bildirimler.txt'

sektorKaraListe = ["Aracı Kurumlar", "GYO", "Sigorta", "Bankacılık", "Yatırım Ortaklıkları", "Spor", "Fin.Kiralama ve Faktoring"]
hisseKaraListe = ["MACKO", "BEYAZ"]
sirketFonKaraListe = ["YATIRIM FONU","MENKUL","FİNANSMAN","PORTFÖY","BANK","FAKTORİNG"]

url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx#page-1"
headers = {
"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

sektorTablosuIsYatirim = pd.read_pickle("sektorTablosuIsYatirim.pkl")
# print(df)
# exit()
# try:
#     hisseTablosuIsYatirim = pd.read_html(url)
# except:
#     hisseTablosuIsYatirim = {}

# if not hisseTablosuIsYatirim:
#     exit()
# else:
#     print("Sektör tablosu başarıyla getirildi.")
    
# for table in hisseTablosuIsYatirim:
#     if 'Sektör' in table.columns:
#         print(table)
#         print(type(table))
#         table.to_pickle("sektorTablosuIsYatirim.pkl")



def sektorunuKontrolEt(hisseKodu):
    global sektorTablosuIsYatirim
    sektorValues = sektorTablosuIsYatirim.loc[sektorTablosuIsYatirim['Kod'] == hisseKodu, 'Sektör'].values
    if sektorValues.size > 0:
        return sektorValues[0]
        
    return False

# Endeks hisselerini çek
endeksURLs = {100: "https://finans.mynet.com/borsa/endeks/xu100-bist-100/endekshisseleri/",
              50: "https://finans.mynet.com/borsa/endeks/xu050-bist-50/endekshisseleri/",
              30: "https://finans.mynet.com/borsa/endeks/xu030-bist-30/endekshisseleri/"
             }
endeksHisseler = {}

try:
    for endeks, url in endeksURLs.items():
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=(10, 10))
        # response = requests.get(url, timeout=(10, 10))
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody', class_='tbody-type-default')
        for a_tag in tbody.find_all('a', {'title': True}):
            title = a_tag.get('title')
            hisse = title.split()[0]
            if endeks in endeksHisseler:
                endeksHisseler[endeks].append(hisse)
            else:
                endeksHisseler[endeks] = [hisse]
except:
    pass

bildirimGrupları = {"Şirket Faaliyetleri ve Stratejileri": ["Ana Faaliyet Konusu Değişikliği"],
                    "Finansal Raporlama ve Performans Değerlendirmeleri": ["Performans Sunum Raporu", "Performans Sunuş Raporu"], 
                    "Yatırımcı İlişkileri ve Sermaye Hareketleri": ["Yatırımcı Raporu", "Sermaye Artırımından Elde Edilecek - Edilen Fonun Kullanımına İlişkin Rapor", "Maddi Duran Varlık Alımı"],
                    "Geleceğe Dönük Değerlendirmeler": ["Geleceğe Dönük Değerlendirmeler"],
                    "Faaliyet Raporu ve Finansal Raporlar": ["Faaliyet Raporu (Konsolide Olmayan)", "Faaliyet Raporu (Konsolide)", "Faaliyet Raporu", "Finansal Rapor"],
                    "Yeni İş İlişkisi, Sözleşme İmzalanması, İhale Sonucu": ["Yeni İş İlişkisi", "Sözleşme İmzalanması", "İhale Süreci / Sonucu", "İhale Süreci", "İhale Süreci/Sonucu"],
                    "Pay Alım Satım": ["Payların Geri Alınmasına İlişkin Bildirim", "Pay Alım Satım Bildirimi"]
                    }


# Bugünün ve X gün önceki tarihini al
bitisTarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%d.%m.%Y")
baslangicTarihi = (datetime.now(pytz.timezone('Europe/Istanbul')) - timedelta(days=7)).strftime("%d.%m.%Y")
now_in_turkey = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y-%m-%d %H:%M')

# KAP API URL
kapBildirimURL = "https://www.kap.org.tr/tr/api/disclosure/list/main"
user_agents = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                ]

headers = {"User-Agent": random.choice(user_agents),
            "Content-Type": "application/json",
            "Accept": "application/json"}
# Define parameters
params = {
    "fromDate": baslangicTarihi,
    "toDate": bitisTarihi,
    "memberTypes": ["IGS"],
}

# API'den veri çek
response = requests.post(url=kapBildirimURL, json=params, headers=headers, timeout=(10, 10))
bildirimlerContent = response.content
bildirimler = json.loads(bildirimlerContent)
sonBildirimler = bildirimler[:1000]


def getThreadID(bildirimBasligi):
        return next((bildirimGrubu for bildirimGrubu, bildirimBasliklari in bildirimGrupları.items() if bildirimBasligi in bildirimBasliklari), "Diger Haber Bildirimleri")

for index, bildirim in enumerate(sonBildirimler):
    now_in_turkey = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y-%m-%d %H:%M')
    message = ""
    tarih = bildirim['disclosureBasic']['publishDate']
    kod = bildirim['disclosureBasic']['stockCode']
    sirketFon = bildirim['disclosureBasic']['companyTitle']
    tip = bildirim['disclosureBasic']['disclosureClass']
    konu = bildirim['disclosureBasic']['title']
    ozetBilgi = bildirim['disclosureBasic'].get('summary', "")
    ilgiliSirketler = bildirim['disclosureBasic']['relatedStocks']
    yil = bildirim['disclosureBasic'].get('year', "")
    periyot = bildirim['disclosureBasic'].get('period', "")
    bildirimNo = bildirim['disclosureBasic']['disclosureIndex']
    bildirimLink = f"https://www.kap.org.tr/tr/Bildirim/{bildirimNo}"

    if not (kod := kod or ilgiliSirketler):
        continue

    try:
        if kod:
            endeksStatus = " - BIST30" if kod in endeksHisseler[30] else " - BIST50" if kod in endeksHisseler[50] else " - BIST100" if kod in endeksHisseler[100] else " - BIST100 DIŞI"
    except:
        endeksStatus = ""

    if any(sirketAdi.lower() in sirketFon.lower() for sirketAdi in sirketFonKaraListe):
        continue

    kodList = kod.split(",")
    try:
        for kod in kodList:
            hisseSektoru = sektorunuKontrolEt(hisseKodu=kod.strip())
            if hisseSektoru:
                break
    except:
        hisseSektoru = ""

    if hisseSektoru in sektorKaraListe:
        continue

    if kod.split(",")[0] in hisseKaraListe:
        continue

    for hisseKodu in kodList:
        hisseKodu = hisseKodu.strip()
        if hisseKodu in hisseKaraListe:
            continue

    if ozetBilgi and any(bildirimOzeti.lower() in ozetBilgi.lower() for bildirimOzeti in istenmeyen_bildirimler):
        continue
    if konu and any(bildirimOzeti.lower() in konu.lower() for bildirimOzeti in istenmeyen_bildirimler):
        continue

    # HTML icerigini parse et
    try:
        bildirimResponse = requests.get(url=bildirimLink, headers=headers, timeout=(10, 10))
        soup = BeautifulSoup(bildirimResponse.text, 'html.parser')
    except:
        print(f"{tarih} --> {kod} için {bildirimNo} numaralı bildirim açıklaması çekilemedi, 3 sn. sonra tekrar denenecek.")
        time.sleep(3)
        try:
            bildirimResponse = requests.get(url=bildirimLink, headers=headers, timeout=(10, 10))
            soup = BeautifulSoup(bildirimResponse.text, 'html.parser')
        except:
            print(f"{tarih} --> {kod} için {bildirimNo} numaralı bildirim açıklaması tekrar çekilemedi, manuel olarak kontrol ediniz. https://www.kap.org.tr/tr/Bildirim/{bildirimNo}")
            continue

    try:
        aciklamalarContent = soup.find('td', class_="taxonomy-context-value-summernote multi-language-content content-tr")
        # aciklama = aciklamalarContent.get_text(separator=" ", strip=True)
        aciklama = ' '.join(aciklamalarContent.stripped_strings)
    except:
        # Açıklama hala boş ise Ek açıklamlar kısmına bak
        try:
            ekAciklamalarContent = soup.find_all('div', class_='gwt-HTML control-label lineheight-32px')
            ekAciklamalarMetin = [div for div in ekAciklamalarContent if div.find('p')]
            aciklama = "\n".join(p.get_text().strip() for div in ekAciklamalarMetin for p in div.find_all('p') if p.get_text().strip())  # Tek paragraf haline getir
        except:
            aciklama = "Açıklama çekilemedi."
    
    
    bildirimGrubu = getThreadID(bildirimBasligi=konu)    

    # Create a new DataFrame row
    new_row = pd.DataFrame([{
        "Tarih": tarih,
        "Kod": kod,
        "Şirket/Fon": sirketFon,
        "Konu": konu,
        "Özet Bilgi": ozetBilgi,
        "Açıklama": aciklama, 
        "Bildirim Link": bildirimLink
    }])

    # Initialize session state for stored data if not already set
    if "tab1Data" not in st.session_state:
        st.session_state.tab1Data = new_row  # First-time initialization
    else:
        # Filter only new rows where "Bildirim Link" is NOT already in the stored DataFrame
        existing_links = set(st.session_state.tab1Data["Bildirim Link"])
        new_data = new_row[~new_row["Bildirim Link"].isin(existing_links)]
        # Append only new unique rows
        if not new_data.empty:
            df = pd.concat([st.session_state.tab1Data, new_data], ignore_index=True)
            df.fillna("", inplace=True)
            st.session_state.tab1Data = df

    # Tab 1: Refreshing Data
    with tab1:
        with df_placeholder.container():
            df = st.session_state.tab1Data.set_index("Kod")
            st.dataframe(df, use_container_width=True, height=900)
            
refresh_interval = 10
time.sleep(refresh_interval)
st.rerun()