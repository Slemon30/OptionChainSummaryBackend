from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
# import logging

# logging.basicConfig(level=logging.DEBUG,
#     format='%(asctime)s %(levelname)s [%(name)s] %(message)s')
# logging.getLogger('apscheduler').setLevel(logging.DEBUG)

cached_data = {
    "option_chain": [],
    "summary": {}
}

app = Flask(__name__)
CORS(app)

def fetch_option_data():
    optiondata_list = []
    url = 'https://groww.in/options/nifty'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table', class_='tb10Table borderPrimary optc56Table')

    if tables:
   
        table = tables[0]
    
 
        tbody = table.find('tbody', class_='optc56Tbody optc56TbodyOv')
    
        if tbody:
       
            rows = tbody.find_all('tr')
        
      
            for row in rows:
            
                CallcellsOI = row.find_all('td', class_='opr84CallCell', attrs={"width":"14.5%"})
                CallcellsPrice = row.find_all('td', class_='opr84CallCell', attrs={"width":"14%"})
                StrikePrice = row.find_all('td', class_= 'tb10Td')
                PutcellsOI = row.find_all('td', class_= 'opr84PutCell', attrs = {"width":"14.5%"})
                PutcellsPrice = row.find_all('td', class_= 'opr84PutCell', attrs = {"width":"14%"})
            
            
                for td in CallcellsOI:
                    callcelldiv_OI = td.find('div', class_='opr84CellVal')
                    callOI = callcelldiv_OI.text.replace(",", "").strip()  
                    if callOI == '--':
                        callOI = 0
                    else:
                        callOI = float(callOI)

                #print("Call OI: ", callOI)  
                for td in CallcellsPrice:
                    callcelldiv_Price = td.find('div', class_='opr84CellVal')
                    callPrice = callcelldiv_Price.text.replace(",", "").replace("₹", "").strip()  
                    if callPrice == '--':
                        callPrice = 0
                    else:
                        callPrice = float(callPrice)
                #print("Call Price: ", callPrice)  

                for td in StrikePrice:
                    celldiv_Price = td.find('span', class_='opr84AbsoluteCentre')
                    strikePrice = float(celldiv_Price.text.replace(",", "").strip()) 
                #print("Strike Price: ", strikePrice)  
                for td in PutcellsOI:
                    putcelldiv_OI = td.find('div', class_='opr84CellVal')
                    putOI = putcelldiv_OI.text.replace(",", "").strip()
                    if putOI == '--':
                        putOI = 0
                    else:
                        putOI = float(putOI)
                #print("Put OI: ", putOI)  

                for td in PutcellsPrice:
                    putcelldiv_Price = td.find('div', class_='opr84CellVal')
                    putPrice = putcelldiv_Price.text.replace(",", "").replace("₹", "").strip()  
                    if putPrice == '--':
                        putPrice = 0
                    else:
                        putPrice = float(putPrice)
                #print("Put Price: ", putPrice)  
                callplusputOI = callOI + putOI
                callminusputOI = callOI - putOI
                data1 = [callOI, callPrice, strikePrice, putPrice, putOI, callplusputOI, callminusputOI]
                optiondata_list.append(data1)
                        
        else:
            print("tbody tag not found within the table.")
    else:
        print("Table with class 'tb10Table optc56Table' not found in the static HTML.")

    return optiondata_list

def update_data():
    optiondata_list = fetch_option_data()
    optionchain = pd.DataFrame(optiondata_list, columns=['Call OI', 'Call Price', 'Strike Price', 'Put Price', 'Put OI', 'Call+Put', 'Call-Put'])
    
    totalCallOI = optionchain['Call OI'].sum()
    totalPutOI = optionchain['Put OI'].sum()
    put_to_call_ratio = totalPutOI / totalCallOI if totalCallOI else 0
    maxCallOI_StrikePrice = None
    maxPutOI_StrikePrice = None
    maxOI_StrikePrice = None

    if not optionchain.empty:
        maxCallOI_StrikePrice = optionchain.loc[optionchain['Call OI'].idxmax(), 'Strike Price']
        maxPutOI_StrikePrice = optionchain.loc[optionchain['Put OI'].idxmax(), 'Strike Price']
        maxOI_StrikePrice = optionchain.loc[(optionchain['Call+Put']).idxmax(), 'Strike Price']
        top3_maxOI = optionchain.nlargest(3, 'Call+Put')
        top3_maxOI_StrikePrices = top3_maxOI['Strike Price'].tolist()
        maxOI_StrikePrice2 = top3_maxOI_StrikePrices[1]
        maxOI_StrikePrice3 = top3_maxOI_StrikePrices[2]

    
    #maxCallOI_StrikePrice = optionchain.loc[optionchain['Call OI'].idxmax()]['Strike Price'] if not optionchain['Call OI'].empty else None
    #maxPutOI_StrikePrice = optionchain.loc[optionchain['Put OI'].idxmax()]['Strike Price'] if not optionchain['Put OI'].empty else None
    #maxOI_StrikePrice = optionchain.loc[optionchain['Call OI'] + optionchain['Put OI'] == (optionchain['Call OI'] + optionchain['Put OI']).max()]['Strike Price'].values[0]
    #optionchain['Call OI'] = pd.to_numeric(optionchain['Call OI'], errors='coerce').fillna(0)
    #optionchain['Put OI'] = pd.to_numeric(optionchain['Put OI'], errors='coerce').fillna(0)

   # combined_OI = optionchain['Call OI'] + optionchain['Put OI']
    #max_combined_OI = combined_OI.max()
    #maxOI_StrikePrice = 0
    #filtered = optionchain.loc[combined_OI == max_combined_OI]
    #if not filtered.empty:
        #maxOI_StrikePrice = filtered['Strike Price'].values[0]
        #print("Strike Price with max OI:", maxOI_StrikePrice)
    #else:
        #print("No Strike Price found with maximum combined OI.")

    cached_data["option_chain"] = optiondata_list
    cached_data["summary"] = {
            "totalCallOI": totalCallOI,
            "totalPutOI": totalPutOI,
            "putToCallRatio": put_to_call_ratio,
            "maxCallOI_StrikePrice": maxCallOI_StrikePrice,
            "maxPutOI_StrikePrice": maxPutOI_StrikePrice,
            "maxOI_StrikePrice": maxOI_StrikePrice,
            "maxOI_StrikePrice2": maxOI_StrikePrice2,
            "maxOI_StrikePrice3": maxOI_StrikePrice3
        }

@app.route('/get_option_data', methods=['GET'])
def get_option_data():
    return jsonify(cached_data)

scheduler = BackgroundScheduler()
scheduler.add_job(update_data, "interval", minutes=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    update_data()
    app.run(debug=True)
