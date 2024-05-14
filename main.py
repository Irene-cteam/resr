from fastapi import FastAPI, Request, Response
import json
import datetime
import requests
from collections import defaultdict
app = FastAPI()

class Scrape:
    def __init__(self, request_body) -> None:
        self.start = self._parse_date(request_body.get("start_date"))
        self.end = self._parse_date(request_body.get("end_date"))

    def _parse_date(self, date_str):
        date_format = "%Y-%m-%d"
        try:
            if date_str:
                valid_date = datetime.datetime.strptime(date_str, date_format)
                return valid_date.strftime('%Y/%m/%d')
        except ValueError:
            raise ValueError(f"Date '{date_str}' is not in the expected format: YYYY-MM-DD")
        return "init"


    def get_result(self):
        files = {'start': self.start, 'end': self.end}
        try:
            req = requests.post(f"https://www2.moeaea.gov.tw/oil111/Gasoline/RetailPrice/load", params=files)
            data = req.json()
            result=self._process_data(data)
            return result
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}")








    def _process_data(self, data):
        result = {'result':[]}
        data = data.get('data', {}).get('gasoline', [])
        for item in data:
            date = item['Date'].replace('/', '-')
            result['result'].append({
                'date':date,
                'oil':{
                    'cpc': self._get_fuel_prices(item, 'A'),
                    'fpcc': self._get_fuel_prices(item, 'B')
                }
            })
        return result

    def _get_fuel_prices(self, item, prefix):
        return [
            {"title": "92 無鉛汽油", "price": item[f'{prefix}92']},
            {"title": "95 無鉛汽油", "price": item[f'{prefix}95']},
            {"title": "98 無鉛汽油", "price": item[f'{prefix}98']},
            {"title": "超級/高級柴油", "price": item[f'{prefix}chai']}
        ]





@app.post('/oil_history')
async def oil_history(request: Request):
    try:
        request_data = await request.json()
        result = Scrape(request_data).get_result()
        return Response(content=json.dumps(result), media_type="application/json")
    except Exception as e:
        return Response(content=json.dumps({"error_msg": str(e)}), media_type='application/json')

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app)