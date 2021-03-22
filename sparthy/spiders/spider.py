import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import SparthyItem
from itemloaders.processors import TakeFirst
import json
import requests

pattern = r'(\xa0)?'

url = "https://www.sparthy.dk/api/sdc/news/search"

payload = "{{\"page\":{},\"filterType\":\"categories\",\"filterValues\":[]}}"
headers = {
    'authority': 'www.sparthy.dk',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': 'application/json, text/plain, */*',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://www.sparthy.dk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.sparthy.dk/nyhedsarkiv',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': 'sdc_device_id=ed7e11bc-4605-a83e-a60b-194c5d51bddf; CookieInformationConsent=%7B%22website_uuid%22%3A%220240e5d8-0ab8-4b16-aed7-0daef8579187%22%2C%22timestamp%22%3A%222021-03-05T10%3A16%3A00.044Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fwww.sparthy.dk%2F%22%2C%22consent_website%22%3A%22sparthy.dk%22%2C%22consent_domain%22%3A%22www.sparthy.dk%22%2C%22user_uid%22%3A%22202cb5c3-34f2-46f3-afaa-b8483b0ce479%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%2C%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22consents_denied%22%3A%5B%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Windows%20NT%206.1%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F88.0.4324.190%20Safari%2F537.36%22%7D; _fbp=fb.1.1614939360281.1646984361; _ga=GA1.2.1955942811.1614943406; ARRAffinity=df04468a6d146999412491bdcbd8a69ea30f0cacaa8056d6ac5ad4bb1d2c754a; ARRAffinitySameSite=df04468a6d146999412491bdcbd8a69ea30f0cacaa8056d6ac5ad4bb1d2c754a; TS011c3006=014105db70b352666a83f9ce5eb05ceedbb416f4244a07dab303f7931b456155ad3a15906c22416ade02f34fe969505f4e06e4cb0b; TS01f606a1=014105db702cd324c76da49da951918c8db603b1d94a07dab303f7931b456155ad3a15906c40fafc412ecf1f2f4516c72d9274fa86905cfc27d89b4c24fd86a4b9b78ddd3bcea038572e431a6ac7fa3484964c3a55; sdc_auth=eyJwcm9kdWN0cyI6W10sImF2YWlsYWJsZVNlZ21lbnRzIjpbXSwiYXV0aGVudGljYXRlZCI6ZmFsc2V9; _gcl_au=1.1.1878982666.1616396284; _gid=GA1.2.1350464610.1616396284; _gat_UA-4586725-7=1; TS011c3006=014105db701f5560aae3442ea970a511caf37a52c5b98220b4186f0076c12658bb1d797dfc621c0cdbb5515219c5b9d618ced2569e'
}

class SparthySpider(scrapy.Spider):
    name = 'sparthy'
    page = 0
    start_urls = ['https://www.sparthy.dk/nyhedsarkiv']

    def parse(self, response):
        data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
        data = json.loads(data.text)

        for index in range(len(data['results'])):
            links = data['results'][index]['url']
            date = data['results'][index]['date'].split()[0]
            yield response.follow(links, self.parse_post, cb_kwargs=dict(date=date))
        if self.page < data['totalPages']:
            self.page += 1
            yield response.follow(response.url, self.parse, dont_filter=True)

    def parse_post(self, response, date):

        title = response.xpath('(//h2)[last()]//text() | //h1//text()').get()
        content = response.xpath('//div[@class="frame__cell-item"]//text()[not (ancestor::aside)]').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "",' '.join(content))

        item = ItemLoader(item=SparthyItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
