from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiohttp
import csv
import asyncio
import uvicorn
import os
# PORT = 8000 
HOST = '0.0.0.0'
PORT = int(os.environ.get("PORT", 8000))  # 如果没有设置环境变量，则使用8000

app = FastAPI()
abspath=os.path.abspath('./web')
print('当前工作路径',os.getcwd())
print('静态文件工作路径',abspath)
if not os.path.exists(abspath):
    raise RuntimeError(f"目录'{abspath}'不存在")
app.mount("/static", StaticFiles(directory=abspath), name="static")
templates = Jinja2Templates(directory=abspath)

# 读取城市数据
async def read_cities():
    path= os.path.abspath(os.getcwd()+'/europe.csv')
    print('读取城市数据',path)
    cities = []
    with open(path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cities.append((row['capital'], row['country'], row['latitude'], row['longitude']))
    return cities

# 获取城市温度
async def fetch_temperature(latitude, longitude):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true") as response:
            data = await response.json()
            return data['current_weather']['temperature']

# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    cities = await read_cities()
    return templates.TemplateResponse('index.html', {"request": request, "cities": cities})

# 路由：获取城市温度
@app.get("/temperatures")
async def get_temperatures():
    cities = await read_cities()
    tasks = [fetch_temperature(lat, lon) for _, _, lat, lon in cities]
    temperatures = await asyncio.gather(*tasks)

    # 构建所需的数据结构
    datas = [{"country": city[1], "capital": city[0], "temperature": temp} for city, temp in zip(cities, temperatures)]
    
    return {"datas": datas}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

