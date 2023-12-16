import httpx
import asyncio
import aiohttp

async def fetch(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def test_httpx():
    url = 'https://www.example.org/'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(response)
    return ""

if __name__ == "__main__":
    # asyncio.run(test_httpx())
    text = asyncio.run(fetch('http://www.example.com'))
    print(text)