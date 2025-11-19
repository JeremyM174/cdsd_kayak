import logging
import scrapy
from scrapy.crawler import CrawlerProcess
import json

class BookingDetailsSpider(scrapy.Spider):
    name = "booking_details"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 3,
    }
    
    def start_requests(self):
        """Loads URLs from JSON file"""
        json_path = r'data\all_cities_urls_hotels.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            hotels_data = json.load(f)
        
        self.logger.info(f"📂 Loading {len(hotels_data)} hotel URLs ")
        
        # Request creation per URL
        for hotel in hotels_data:
            url = hotel['url']
            city = hotel['city']
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_hotel,
                meta={'city': city, 'url': url},
                errback=self.handle_error
            )
    
    def parse_hotel(self, response):
        """Extracts hotel details"""
        city = response.meta['city']
        url = response.meta['url']
        
        self.logger.info(f"🏨 Extracting: {response.url}")
        
        # === HOTEL NAME === With several selectors
        nom = response.css('h2.pp-header__title::text').get()
        if not nom:
            nom = response.css('h2[data-testid="property-name"]::text').get()
        if not nom:
            nom = response.xpath('//*[@id="hp_hotel_name"]/div/h2/text()').get()
            # nom = response.xpath('//h2[@class="hp__hotel-name"]/text()').get()
        if not nom:
            nom = response.css('h1.d2fee87262::text').get()
        
        # === Note ===
        note = response.css('div.b5cd09854e::text').get()
        if not note:
            note = response.css('div[data-testid="review-score-component"] div::text').get() 
        if not note:
            note = response.xpath('//*[@id="js--hp-gallery-scorecard"]/a/div/div/div/div[2]/text()').get()
        
            # note = response.xpath('//div[@class="b5cd09854e d10a6220b4"]/text()').get() #//*[@id="js--hp-gallery-scorecard"] //*[@id="js--hp-gallery-scorecard"]/a/div/div/div/div[1]  //*[@id="js--hp-gallery-scorecard"]/a/div/div/div/div[2]
        
        # # Reviews
        # nb_reviews = response.css('div.d8eab2cf7f::text').get()
        # if not nb_reviews:
        #     nb_reviews = response.css('div[data-testid="review-score-component"] span::text').get()
        
        # === ADDRESS ===
        adresse = response.xpath('//*[@class="de576f5064"]/div//text()').get() #inspect button item > div > text
        if not adresse: #backup method returning all of button object as string, insert back string processing in "building results" comments
            adresse = response.xpath('//*[@class="b99b6ef58f.cb4b7a25d9.b06461926f"]//text()').get()
        if not adresse:
            adresse = response.xpath('/html/body/div[4]/div/div[4]/main/div/div[1]/div[1]/div[2]/div[4]/div[4]/div/div/div/div/div/span[1]/button/div').get()
        if not adresse:
            adresse = response.xpath('/html/body/div[5]/div/div[4]/main/div[1]/div[1]/div[1]/div[2]/div[4]/div[4]/div/div/div/div/div/span[1]/button/div').get()
        if not adresse:
            adresse = response.xpath('/html/body/div[4]/div/div[5]/main/div[1]/div[1]/div[1]/div[2]/div[4]/div[4]/div/div/div/div/div/span[1]/button/div').get()
        if not adresse:
            adresse = response.xpath('/html/body/div[5]/div/div[5]/main/div/div[1]/div[1]/div[2]/div[4]/div[4]/div/div/div/div/div/span[1]/button/div').get()
        if not adresse:
            adresse = response.xpath('/html/body/div[5]/div/div[5]/main/div[1]/div[1]/div[1]/div[2]/div[4]/div[4]/div/div/div/div/div/span[1]/button/div').get()
        
        # === DESCRIPTION === Might be divided under several paragraphs
        description_parts = response.css('div#property_description_content p::text').getall()
        if not description_parts:
            description_parts = response.css('div.hp_desc_main_content p::text').getall()
        if not description_parts:
            description_parts = response.xpath('//*[@id="basiclayout"]/div/div[3]/div[1]/div[1]/div[1]/div[1]/div/div/p[1]/text()').getall()
            # description_parts = response.xpath('//div[@id="property_description_content"]//p/text()').getall()
        
        description = ' '.join(description_parts).strip() if description_parts else None
        if not description:
            description = response.css('div.a53cbfa6de::text').get()
        
        # # === EXTRA INFORMATIONS (BONUS) ===
        # # Price
        # price = response.css('span.prco-valign-middle-helper::text').get()
        # if not price:
        #     price = response.css('div.bui-price-display__value::text').get()
        
        # # Lodgings type
        # lodgings_type = response.css('span.hp__hotel-type-badge::text').get()
        
        # # Equipment
        # equipements = response.css('div.important_facility span::text').getall()
        # if not equipements:
        #     equipements = response.css('div.hp-description ul li::text').getall()
        
        # === BUILDING RESULTS ===
        hotel_data = {
            'place': city,
            'url': url,
            'name': nom.strip() if nom else 'Unavailable',
            'note': note.strip() if note else 'Unavailable',
            # 'nb_reviews': nb_reviews.strip() if nb_reviews else 'Unavailable',
            'address': adresse.strip() if adresse else 'Unavailable', #.split(">")[1].split("<")[0] # Previous comment = string processing as backup
            'description': description if description else 'Unavailable',
            # 'price': price.strip() if price else 'Unavailable',
            # 'lodgings_type': lodgings_type.strip() if lodgings_type else 'Unavailable',
            # 'equipements': equipements[:5] if equipements else []
        }
        
        self.logger.info(f"✅ Extracted: {hotel_data['name']} - Note: {hotel_data['note']}") #preview log for powershell
        
        yield hotel_data
    
    def handle_error(self, failure):
        """Error handling"""
        self.logger.error(f"❌ Scraping error: {failure.value}")
        self.logger.error(f"Related URL: {failure.request.url}")


# === CONFIG - RUN ===
if __name__ == '__main__':
    output_path = r'data\hotels_details.json'
    
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': logging.INFO,
        'FEEDS': {
            output_path: {
                "format": "json",
                'overwrite': True,
                'encoding': 'utf-8',
                'indent': 2
            },
        }
    })
    
    process.crawl(BookingDetailsSpider)
    process.start()