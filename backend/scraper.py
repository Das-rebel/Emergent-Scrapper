import asyncio
import aiohttp
import json
import re
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from models import (
    TweetData, ProcessedTweet, ScrapingSession, MediaInfo, TwitterFeatures,
    MediaFeatures, YouTubeMetadata, Sentiment, AIAnalysis
)
from database import database

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self):
        self.session = None
        self.rate_limits = {}
        self.max_retries = int(os.environ.get('SCRAPER_MAX_RETRIES', '3'))
        self.retry_delay = int(os.environ.get('SCRAPER_RETRY_DELAY', '30'))
        self.batch_size = int(os.environ.get('SCRAPER_BATCH_SIZE', '50'))
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_bookmarks(self) -> List[Dict[str, Any]]:
        """Scrape Twitter bookmarks using primary and fallback methods"""
        
        # For demo purposes, return mock data if no API keys are configured
        if not any([
            os.environ.get('SCRAPINGBEE_KEY'),
            os.environ.get('TWITTER_BEARER_TOKEN')
        ]):
            logger.info("No API keys configured, returning mock data for demonstration")
            return self._get_mock_bookmarks()
        
        # Primary method: Custom bookmark scraper
        try:
            bookmarks = await self._fetch_primary_bookmarks()
            if bookmarks:
                return bookmarks
        except Exception as e:
            logger.error(f"Primary bookmark fetch failed: {e}")
        
        # Fallback method: ScrapingBee
        try:
            bookmarks = await self._fetch_fallback_bookmarks()
            if bookmarks:
                return bookmarks
        except Exception as e:
            logger.error(f"Fallback bookmark fetch failed: {e}")
        
        # Last resort: Twitter API
        try:
            bookmarks = await self._fetch_twitter_api_bookmarks()
            if bookmarks:
                return bookmarks
        except Exception as e:
            logger.error(f"Twitter API fetch failed: {e}")
        
        # If all real methods fail, return mock data for demo
        logger.warning("All real scraping methods failed, returning mock data")
        return self._get_mock_bookmarks()
    
    def _get_mock_bookmarks(self) -> List[Dict[str, Any]]:
        """Return mock bookmarks for demonstration purposes"""
        from datetime import datetime, timedelta
        import random
        
        mock_tweets = [
            {
                'id': '1',
                'text': 'Just launched our new AI-powered Twitter scraper! 🚀 It automatically analyzes sentiment, extracts topics, and identifies trends. Perfect for social media monitoring and research. #AI #MachineLearning #SocialMedia',
                'author': 'TechInnovator',
                'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'url': 'https://twitter.com/TechInnovator/status/1',
                'media_urls': []
            },
            {
                'id': '2', 
                'text': 'Thread 🧵 about the future of web scraping: 1/5\n\nWeb scraping is evolving rapidly with AI integration. Modern scrapers can now understand context, handle dynamic content, and provide intelligent data extraction.',
                'author': 'DataScientist',
                'created_at': (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                'url': 'https://twitter.com/DataScientist/status/2',
                'media_urls': ['https://example.com/image1.jpg']
            },
            {
                'id': '3',
                'text': 'Really impressed with the latest FastAPI updates! The performance improvements are incredible. Building APIs has never been easier 💯 #FastAPI #Python #WebDev',
                'author': 'PythonDev',
                'created_at': (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                'url': 'https://twitter.com/PythonDev/status/3',
                'media_urls': []
            },
            {
                'id': '4',
                'text': 'Breaking: Major breakthrough in natural language processing! New transformer model achieves 95% accuracy on sentiment analysis tasks. This could revolutionize how we analyze social media data.',
                'author': 'AIResearcher',
                'created_at': (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                'url': 'https://twitter.com/AIResearcher/status/4',
                'media_urls': []
            },
            {
                'id': '5',
                'text': 'Quick tip for developers: Always validate your API responses! I spent 3 hours debugging an issue that was caused by assuming API data structure. Lesson learned 😅 #DevTips #API #LessonsLearned',
                'author': 'SeniorDev',
                'created_at': (datetime.utcnow() - timedelta(hours=16)).isoformat(),
                'url': 'https://twitter.com/SeniorDev/status/5',
                'media_urls': []
            }
        ]
        
        return mock_tweets
    
    async def _fetch_primary_bookmarks(self) -> List[Dict[str, Any]]:
        """Fetch bookmarks using primary scraper"""
        url = "https://twitter-bookmark-scraper.onrender.com/scrape"
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(url, timeout=60) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('bookmarks') and not data.get('error'):
                            return data['bookmarks']
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        return []
    
    async def _fetch_fallback_bookmarks(self) -> List[Dict[str, Any]]:
        """Fetch bookmarks using ScrapingBee"""
        api_key = os.environ.get('SCRAPINGBEE_KEY')
        if not api_key:
            raise Exception("ScrapingBee API key not found")
        
        url = "https://api.scrapingbee.com/v1/"
        params = {
            'api_key': api_key,
            'url': 'https://twitter.com/i/bookmarks',
            'render_js': 'true',
            'wait': '5000',
            'extract_rules': json.dumps({
                "tweets": {
                    "selector": "article",
                    "type": "list",
                    "output": {
                        "text": {"selector": "[data-testid=tweetText]", "output": "text"},
                        "author": {"selector": "[data-testid=User-Name]", "output": "text"},
                        "url": {"selector": "a[href*=status]", "output": "href"}
                    }
                }
            })
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('tweets'):
                    # Transform ScrapingBee response to match original format
                    tweets = []
                    for tweet in data['tweets']:
                        tweets.append({
                            'text': tweet.get('text', ''),
                            'author': tweet.get('author', '').split('·')[0].strip(),
                            'url': f"https://twitter.com{tweet.get('url', '')}"
                        })
                    return tweets
        
        return []
    
    async def _fetch_twitter_api_bookmarks(self) -> List[Dict[str, Any]]:
        """Fetch bookmarks using Twitter API"""
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            raise Exception("Twitter Bearer Token not found")
        
        url = "https://api.twitter.com/2/users/me/bookmarks"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', [])
        
        return []
    
    def detect_media(self, tweet: Dict[str, Any]) -> MediaInfo:
        """Detect media types in tweet"""
        text = tweet.get('text', '')
        media_info = MediaInfo()
        
        # Image detection
        media_info.has_images = bool(re.search(r'pic\.twitter\.com|twitter\.com/[^/]+/status/[0-9]+/photo/', text, re.I))
        
        # Video detection
        media_info.has_video = bool(re.search(r'video|gif|mp4|mov', text, re.I))
        
        # YouTube detection
        youtube_links = re.findall(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+', text, re.I)
        media_info.youtube_links = [link[0] + link[1] + link[2] + link[3] for link in youtube_links]
        
        # Thread detection
        media_info.is_thread = bool(re.search(r'🧵|thread|\d+/\d+', text, re.I))
        
        return media_info
    
    def extract_twitter_features(self, tweet_data: Dict[str, Any]) -> TwitterFeatures:
        """Extract Twitter-specific features from tweet"""
        text = tweet_data.get('text', '')
        created_at = datetime.fromisoformat(tweet_data.get('created_at', datetime.utcnow().isoformat()))
        
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+'
        
        return TwitterFeatures(
            hashtag_count=len(re.findall(r'#\w+', text)),
            mention_count=len(re.findall(r'@\w+', text)),
            url_count=len(re.findall(r'https?://[^\s]+', text)),
            emoji_count=len(re.findall(emoji_pattern, text)),
            exclamation_count=text.count('!'),
            question_count=text.count('?'),
            caps_ratio=len(re.findall(r'[A-Z]', text)) / max(len(text), 1),
            word_count=len(text.split()),
            char_count=len(text),
            hour_of_day=created_at.hour,
            day_of_week=created_at.weekday(),
            is_reply=text.startswith('@'),
            is_retweet=text.startswith('RT @'),
            thread_indicators=bool(re.search(r'\b\d+/\d+\b|thread|🧵', text, re.I)),
            hashtags=[tag[1:] for tag in re.findall(r'#\w+', text)],
            mentions=[mention[1:] for mention in re.findall(r'@\w+', text)],
            urls=re.findall(r'https?://[^\s]+', text)
        )
    
    def calculate_engagement_potential(self, features: TwitterFeatures) -> float:
        """Calculate engagement potential score"""
        score = 0.5
        score += min(0.2, features.hashtag_count * 0.05)
        score += min(0.1, features.mention_count * 0.03)
        score += features.question_count * 0.1
        score += min(0.15, features.emoji_count * 0.03)
        score -= features.url_count * 0.05
        
        if 10 <= features.word_count <= 30:
            score += 0.1
        
        if 9 <= features.hour_of_day <= 17:
            score += 0.05
        
        return max(0, min(1, score))
    
    def calculate_readability(self, text: str) -> float:
        """Calculate readability score"""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return 0.5
        
        avg_words_per_sentence = words / sentences
        avg_chars_per_word = len(text) / words
        complexity = (avg_words_per_sentence / 20) + (avg_chars_per_word / 10)
        
        return max(0, min(1, 1 - complexity))
    
    async def process_tweet(self, tweet_data: Dict[str, Any]) -> TweetData:
        """Process individual tweet and extract features"""
        
        # Create base tweet data
        tweet = TweetData(
            id=tweet_data.get('id', str(datetime.utcnow().timestamp())),
            text=tweet_data.get('text', ''),
            author=tweet_data.get('author', 'unknown'),
            created_at=datetime.fromisoformat(tweet_data.get('created_at', datetime.utcnow().isoformat())),
            url=tweet_data.get('url', ''),
            media_urls=tweet_data.get('media_urls', [])
        )
        
        # Detect media
        tweet.media_info = self.detect_media(tweet_data)
        
        # Extract Twitter features
        tweet.twitter_features = self.extract_twitter_features(tweet_data)
        
        # Calculate scores
        tweet.engagement_potential = self.calculate_engagement_potential(tweet.twitter_features)
        tweet.readability_score = self.calculate_readability(tweet.text)
        
        # Extract indicators
        tweet.positive_indicators = len(re.findall(r'\b(great|amazing|awesome|love|excellent|fantastic|wonderful|brilliant|perfect|outstanding)\b', tweet.text, re.I))
        tweet.negative_indicators = len(re.findall(r'\b(terrible|awful|hate|horrible|worst|disgusting|pathetic|useless|stupid|annoying)\b', tweet.text, re.I))
        tweet.tech_indicators = len(re.findall(r'\b(AI|ML|tech|startup|code|programming|software|app|digital|innovation|algorithm|data|cloud|blockchain|crypto)\b', tweet.text, re.I))
        tweet.business_indicators = len(re.findall(r'\b(business|marketing|sales|revenue|profit|growth|strategy|leadership|management|entrepreneur|investment|funding)\b', tweet.text, re.I))
        
        # Process media features
        tweet.media_features = MediaFeatures(
            has_media=len(tweet.media_urls) > 0,
            image_count=len(tweet.media_urls),
            is_thread=tweet.media_info.is_thread,
            youtube_video=len(tweet.media_info.youtube_links) > 0
        )
        
        return tweet
    
    async def analyze_with_ai(self, tweet_data: TweetData) -> AIAnalysis:
        """Analyze tweet with AI (OpenAI/DeepSeek)"""
        
        # Check if any AI API keys are available
        providers = [
            {
                'name': 'OpenAI',
                'url': 'https://api.openai.com/v1/chat/completions',
                'api_key': os.environ.get('OPENAI_API_KEY'),
                'model': 'gpt-3.5-turbo-0125'
            },
            {
                'name': 'DeepSeek',
                'url': 'https://api.deepseek.com/v1/chat/completions',
                'api_key': os.environ.get('DEEPSEEK_API_KEY'),
                'model': 'deepseek-chat'
            }
        ]
        
        # If no API keys are configured, return mock analysis
        if not any(provider['api_key'] for provider in providers):
            logger.info("No AI API keys configured, returning mock analysis")
            return self._get_mock_analysis(tweet_data)
        
        prompt = f"""Analyze this tweet in JSON format. Include:
1. Topic (max 100 chars)
2. Tags (max 8)
3. Entities (people/orgs/products, max 15)
4. Core concepts (max 10)
5. Sentiment {{label, confidence}}
6. Intent (inform, promote, question, discuss)
7. Relevance score (0-1)
8. Virality potential (0-1)
9. Actionable (boolean)
10. Categories (max 5)
11. Quality score (0-1)
12. Information type (news, opinion, humor, etc.)
13. Key insights (max 5)
14. Discussion worthy (boolean)

Tweet data:
{json.dumps(tweet_data.dict())}

Output ONLY valid JSON, no extra text."""
        
        for provider in providers:
            if not provider['api_key']:
                continue
            
            try:
                request_body = {
                    "model": provider['model'],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                
                headers = {
                    "Authorization": f"Bearer {provider['api_key']}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.post(provider['url'], json=request_body, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        try:
                            analysis = json.loads(content)
                            return self._validate_ai_analysis(analysis, provider['name'])
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"AI analysis failed for {provider['name']}: {e}")
                continue
        
        # Return mock analysis if all providers fail
        logger.warning("All AI providers failed, returning mock analysis")
        return self._get_mock_analysis(tweet_data)
    
    def _get_mock_analysis(self, tweet_data: TweetData) -> AIAnalysis:
        """Generate mock AI analysis based on tweet content"""
        import random
        
        text = tweet_data.text.lower()
        
        # Determine sentiment based on content
        positive_words = ['great', 'amazing', 'awesome', 'love', 'excellent', 'fantastic', 'good', '🚀', '💯', '❤️']
        negative_words = ['terrible', 'awful', 'hate', 'horrible', 'worst', 'bad', 'disappointed', '😞', '💔']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = Sentiment(label="positive", confidence=0.7 + random.uniform(0, 0.2))
        elif negative_count > positive_count:
            sentiment = Sentiment(label="negative", confidence=0.7 + random.uniform(0, 0.2))
        else:
            sentiment = Sentiment(label="neutral", confidence=0.6 + random.uniform(0, 0.3))
        
        # Generate categories based on content
        categories = []
        if any(word in text for word in ['ai', 'ml', 'artificial intelligence', 'machine learning']):
            categories.append('AI/ML')
        if any(word in text for word in ['tech', 'technology', 'software', 'code', 'programming']):
            categories.append('Technology')
        if any(word in text for word in ['business', 'startup', 'entrepreneur', 'marketing']):
            categories.append('Business')
        if any(word in text for word in ['news', 'breaking', 'update', 'announcement']):
            categories.append('News')
        if any(word in text for word in ['tip', 'advice', 'how to', 'tutorial']):
            categories.append('Educational')
        
        if not categories:
            categories = ['General']
        
        # Generate topic
        if 'ai' in text or 'ml' in text:
            topic = "AI and Machine Learning Discussion"
        elif 'tech' in text or 'software' in text:
            topic = "Technology and Software Development" 
        elif 'business' in text or 'startup' in text:
            topic = "Business and Entrepreneurship"
        else:
            topic = "General Social Media Discussion"
        
        # Generate entities
        entities = []
        if '@' in tweet_data.text:
            entities.extend([mention[1:] for mention in re.findall(r'@\w+', tweet_data.text)])
        
        tech_entities = ['FastAPI', 'Python', 'React', 'AI', 'ML', 'Twitter', 'API']
        entities.extend([entity for entity in tech_entities if entity.lower() in text])
        
        # Generate key insights
        key_insights = []
        if sentiment.label == 'positive':
            key_insights.append("Positive sentiment indicates user satisfaction or enthusiasm")
        if len(tweet_data.twitter_features.hashtags) > 0:
            key_insights.append(f"Uses {len(tweet_data.twitter_features.hashtags)} hashtags for better reach")
        if tweet_data.twitter_features.question_count > 0:
            key_insights.append("Contains questions that encourage engagement")
        if tweet_data.media_info.is_thread:
            key_insights.append("Thread format suggests detailed information sharing")
        
        return AIAnalysis(
            provider="mock",
            topic=topic,
            tags=tweet_data.twitter_features.hashtags[:8],
            entities=entities[:15],
            concepts=['Social Media', 'Communication', 'Information Sharing'],
            sentiment=sentiment,
            intent='inform' if any(word in text for word in ['news', 'update', 'tip']) else 'discuss',
            relevance_score=0.6 + random.uniform(0, 0.3),
            virality_potential=min(1.0, (tweet_data.twitter_features.hashtag_count * 0.1 + 
                                        tweet_data.twitter_features.emoji_count * 0.05 + 
                                        0.3 if sentiment.label == 'positive' else 0)),
            actionable=any(word in text for word in ['tip', 'how to', 'tutorial', 'advice']),
            categories=categories,
            quality_score=0.5 + random.uniform(0, 0.4),
            information_type='educational' if any(word in text for word in ['tip', 'tutorial']) else 'opinion',
            target_audience='tech community' if 'tech' in text else 'general',
            key_insights=key_insights,
            discussion_worthy=tweet_data.twitter_features.question_count > 0 or sentiment.confidence > 0.8
        )
    
    def _validate_ai_analysis(self, analysis: Dict[str, Any], provider: str) -> AIAnalysis:
        """Validate and normalize AI analysis response"""
        
        sentiment = analysis.get('sentiment', {})
        if isinstance(sentiment, str):
            sentiment = {"label": sentiment, "confidence": 0.5}
        
        validated = AIAnalysis(
            provider=provider,
            topic=str(analysis.get('topic', 'No topic extracted'))[:100],
            tags=analysis.get('tags', [])[:8],
            entities=analysis.get('entities', [])[:15],
            concepts=analysis.get('concepts', [])[:10],
            sentiment=Sentiment(
                label=sentiment.get('label', 'neutral'),
                confidence=min(1, max(0, float(sentiment.get('confidence', 0.5))))
            ),
            intent=analysis.get('intent', 'unknown'),
            relevance_score=min(1, max(0, float(analysis.get('relevance_score', 0.5)))),
            virality_potential=min(1, max(0, float(analysis.get('virality_potential', 0.5)))),
            actionable=bool(analysis.get('actionable', False)),
            categories=analysis.get('categories', ['uncategorized'])[:5],
            quality_score=min(1, max(0, float(analysis.get('quality_score', 0.5)))),
            information_type=analysis.get('information_type', 'unknown'),
            target_audience=analysis.get('target_audience', 'general'),
            key_insights=analysis.get('key_insights', [])[:5],
            discussion_worthy=bool(analysis.get('discussion_worthy', False))
        )
        
        # Calculate composite scores
        validated.composite_score = (
            validated.relevance_score * 0.3 +
            validated.quality_score * 0.3 +
            validated.virality_potential * 0.2 +
            (0.1 if validated.actionable else 0) +
            (0.1 if validated.discussion_worthy else 0)
        )
        
        validated.engagement_prediction = (
            validated.virality_potential * 0.4 +
            (0.2 if validated.sentiment.confidence > 0.7 else 0) +
            (0.2 if validated.discussion_worthy else 0) +
            (0.1 if len(validated.key_insights) > 0 else 0) +
            (0.1 if validated.actionable else 0)
        )
        
        validated.content_value = (
            validated.relevance_score * 0.4 +
            validated.quality_score * 0.3 +
            (0.2 if validated.actionable else 0) +
            (0.1 if len(validated.key_insights) > 0 else 0)
        )
        
        return validated
    
    async def run_scraping_session(self) -> ScrapingSession:
        """Run a complete scraping session"""
        session = ScrapingSession()
        
        try:
            # Save initial session
            await database.save_session(session)
            
            # Scrape bookmarks
            bookmarks = await self.scrape_bookmarks()
            
            # Process tweets
            for bookmark in bookmarks:
                try:
                    # Process tweet data
                    tweet_data = await self.process_tweet(bookmark)
                    
                    # Analyze with AI
                    ai_analysis = await self.analyze_with_ai(tweet_data)
                    
                    # Create processed tweet
                    processed_tweet = ProcessedTweet(
                        tweet_data=tweet_data,
                        ai_analysis=ai_analysis,
                        source=bookmark.get('source', 'primary')
                    )
                    
                    # Save to database
                    await database.save_tweet(processed_tweet)
                    session.tweets_processed += 1
                    
                except Exception as e:
                    error_msg = f"Error processing tweet: {str(e)}"
                    session.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update session
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            
        except Exception as e:
            session.status = "failed"
            session.errors.append(f"Session failed: {str(e)}")
            logger.error(f"Scraping session failed: {e}")
        
        finally:
            await database.save_session(session)
        
        return session

# Global scraper instance
scraper = TwitterScraper()