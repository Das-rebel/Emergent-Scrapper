from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Data Models
class MediaInfo(BaseModel):
    has_images: bool = False
    has_video: bool = False
    is_thread: bool = False
    youtube_links: List[str] = []

class TwitterFeatures(BaseModel):
    hashtag_count: int = 0
    mention_count: int = 0
    url_count: int = 0
    emoji_count: int = 0
    exclamation_count: int = 0
    question_count: int = 0
    caps_ratio: float = 0.0
    word_count: int = 0
    char_count: int = 0
    hour_of_day: int = 0
    day_of_week: int = 0
    is_reply: bool = False
    is_retweet: bool = False
    thread_indicators: bool = False
    hashtags: List[str] = []
    mentions: List[str] = []
    urls: List[str] = []

class MediaFeatures(BaseModel):
    has_media: bool = False
    image_count: int = 0
    is_thread: bool = False
    youtube_video: bool = False
    meme_score: float = 0.0
    infographic_score: float = 0.0
    image_tags: List[str] = []

class YouTubeMetadata(BaseModel):
    title: str = ""
    description: str = ""
    duration: str = ""
    thumbnail: str = ""
    category_id: str = ""

class Sentiment(BaseModel):
    label: str = "neutral"
    confidence: float = 0.5

class AIAnalysis(BaseModel):
    provider: str = ""
    topic: str = ""
    tags: List[str] = []
    entities: List[str] = []
    concepts: List[str] = []
    sentiment: Sentiment = Sentiment()
    intent: str = "unknown"
    relevance_score: float = 0.5
    virality_potential: float = 0.5
    actionable: bool = False
    categories: List[str] = []
    quality_score: float = 0.5
    information_type: str = "unknown"
    target_audience: str = "general"
    key_insights: List[str] = []
    discussion_worthy: bool = False
    composite_score: float = 0.5
    engagement_prediction: float = 0.5
    content_value: float = 0.5

class TweetData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    url: str = ""
    media_urls: List[str] = []
    media_info: MediaInfo = MediaInfo()
    image_tags: List[str] = []
    meme_tags: List[str] = []
    youtube_metadata: Optional[YouTubeMetadata] = None
    image_captions: List[str] = []
    thread_summary: Optional[str] = None
    twitter_features: TwitterFeatures = TwitterFeatures()
    media_features: MediaFeatures = MediaFeatures()
    engagement_score: float = 0.0
    engagement_potential: float = 0.5
    readability_score: float = 0.5
    positive_indicators: int = 0
    negative_indicators: int = 0
    tech_indicators: int = 0
    business_indicators: int = 0
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessedTweet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tweet_data: TweetData
    ai_analysis: AIAnalysis
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "primary"

class ScrapingSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    tweets_processed: int = 0
    errors: List[str] = []
    source_used: str = "primary"

class ScrapingConfig(BaseModel):
    enabled: bool = True
    schedule_interval: int = 3600  # seconds
    max_retries: int = 3
    retry_delay: int = 30
    batch_size: int = 50
    use_fallback: bool = True
    process_images: bool = True
    process_videos: bool = True
    process_threads: bool = True

# Request/Response Models
class ScrapingSessionResponse(BaseModel):
    session: ScrapingSession
    tweets: List[ProcessedTweet]

class TweetSearchParams(BaseModel):
    query: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    has_media: Optional[bool] = None
    is_thread: Optional[bool] = None
    min_quality_score: Optional[float] = None
    min_engagement_score: Optional[float] = None
    limit: int = 50
    offset: int = 0

class TweetAnalyticsResponse(BaseModel):
    total_tweets: int
    avg_quality_score: float
    avg_engagement_score: float
    sentiment_distribution: Dict[str, int]
    top_categories: List[Dict[str, Any]]
    top_authors: List[Dict[str, Any]]
    media_stats: Dict[str, int]
    daily_stats: List[Dict[str, Any]]