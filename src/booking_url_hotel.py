import logging
import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd

# Charger les villes depuis le CSV
path_cities = r'data\weekly_weather_forecast.csv'
cities_df = pd.read_csv(path_cities)

class BookingURLSpider(scrapy.Spider):
    name = "booking_urls"
    
    # Liste des villes
    cities = cities_df.iloc[:, 1].tolist()
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,  # UNE SEULE requête à la fois
        'DOWNLOAD_DELAY': 5,        # 3 secondes suffisent généralement
        'RANDOMIZE_DOWNLOAD_DELAY': True,    
        'REACTOR_THREADPOOL_MAXSIZE': 20,
    }
    
    def start_requests(self):
        """Génère les requêtes pour chaque ville"""
        for city in self.cities:
            url = f"https://www.booking.com/searchresults.fr.html?ss={city.replace(' ', '+')}%2C+France&checkin=2025-10-03&checkout=2025-10-06&order=review_score_and_price"
            yield scrapy.Request(
                url=url, 
                callback=self.parse, 
                meta={"city": city}  # IMPORTANT : on passe la ville ici
            )
    
    def parse(self, response):
        """Parse les résultats - MÉTHODE ROBUSTE"""
        city = response.meta['city']  # Récupération propre de la ville
        
        # MÉTHODE 1 : Récupérer TOUS les liens d'un coup (MEILLEURE)
        hotel_links = response.css('a[data-testid="title-link"]::attr(href)').getall()
        
        # MÉTHODE 2 : Si la première ne marche pas
        if not hotel_links:
            hotel_links = response.css('h3 a::attr(href)').getall()
        
        # MÉTHODE 3 : XPath alternatif
        if not hotel_links:
            hotel_links = response.xpath('//div[@data-testid="property-card"]//h3/a/@href').getall()
        
        # Log pour débuggage
        self.logger.info(f"🏙️  {city}: {len(hotel_links)} hôtels trouvés")
        
        # Limiter aux 20 premiers
        for link in hotel_links[:20]:
            # Nettoyer l'URL
            clean_url = link.split('?')[0] if '?' in link else link
            
            if clean_url.startswith('//'):
                clean_url = 'https:' + clean_url
            elif clean_url.startswith('/'):
                clean_url = 'https://www.booking.com' + clean_url
            
            yield {
                'city': city,
                'url': clean_url
            }

# Fichier de sortie
filenamepath = r'data\all_cities_urls_hotels.json'

# Configuration du processus
process_url = CrawlerProcess(settings={
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'LOG_LEVEL': logging.INFO,
    'FEEDS': {
        filenamepath: {"format": "json", 'overwrite': True},
    }
})

# Lancement
process_url.crawl(BookingURLSpider)
process_url.start()